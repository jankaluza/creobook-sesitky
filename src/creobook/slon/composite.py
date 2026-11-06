"""Elephant background removal and deterministic compositing."""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFilter

from creobook.slon.models import Placement, SlonError

# When several gaps are equally open, each page prefers a different part of the picture.
_PREFER: tuple[tuple[float, float], ...] = (
    (0.22, 0.30),
    (0.78, 0.34),
    (0.30, 0.72),
    (0.74, 0.70),
    (0.50, 0.48),
    (0.18, 0.55),
    (0.82, 0.52),
    (0.46, 0.80),
    (0.62, 0.22),
    (0.36, 0.46),
    (0.72, 0.84),
    (0.28, 0.18),
)

_BANDS = {
    "easy": (0.10, 0.12),
    "medium": (0.07, 0.10),
    "hard": (0.05, 0.07),
}


def sprite_pixel_size(scene_width: int, sprite: Image.Image, scale: float) -> tuple[int, int]:
    target_w = max(8, round(scene_width * scale))
    target_h = max(8, round(sprite.height * target_w / max(1, sprite.width)))
    return target_w, target_h


def _dark_integral(image: Image.Image) -> tuple[list[int], int]:
    width, height = image.size
    pixels = image.load()
    stride = width + 1
    table = [0] * (stride * (height + 1))
    for y in range(height):
        row = 0
        for x in range(width):
            row += 1 if pixels[x, y] < 128 else 0
            table[(y + 1) * stride + x + 1] = table[y * stride + x + 1] + row
    return table, stride


def _area(table: list[int], stride: int, left: int, top: int, right: int, bottom: int) -> int:
    return (
        table[bottom * stride + right]
        - table[top * stride + right]
        - table[bottom * stride + left]
        + table[top * stride + left]
    )


def find_open_center(
    scene: Image.Image,
    elephant: Image.Image,
    *,
    scale: float,
    used: list[tuple[float, float]],
    index: int,
) -> tuple[float, float, bool]:
    """Place the elephant in a white gap that sits among the drawn objects.

    The gap must be inside the drawing. A gap with objects around it wins over
    empty margin. Pages of one booklet take different gaps when several fit.
    The last value is true when the chosen gap is clear of lines.
    """
    base = scene.convert("L")
    sprite = elephant.convert("RGBA")
    target_w, target_h = sprite_pixel_size(base.width, sprite, scale)
    if target_w >= base.width or target_h >= base.height:
        raise SlonError("Elephant is larger than the scene")
    halo = max(1, round(min(target_w, target_h) * 0.08))
    dilated = base.filter(ImageFilter.MinFilter(halo * 2 + 1))
    raw_table, stride = _dark_integral(base)
    soft_table, _ = _dark_integral(dilated)
    content = base.point(lambda value: 255 if value < 128 else 0).getbbox()
    prefer = _PREFER[index % len(_PREFER)]
    used_cells = {(min(2, int(x * 3)), min(2, int(y * 3))) for x, y in used}
    margin = max(2, round(min(base.width, base.height) * 0.02))
    step = 1 if max(base.size) <= 400 else max(2, min(8, min(target_w, target_h) // 6))

    def score(left: int, top: int) -> tuple[float, ...]:
        right = left + target_w
        bottom = top + target_h
        cx = (left + target_w / 2) / base.width
        cy = (top + target_h / 2) / base.height
        pad = max(2, round(min(target_w, target_h) * 0.45))
        near_left = max(0, left - pad)
        near_top = max(0, top - pad)
        near_right = min(base.width, right + pad)
        near_bottom = min(base.height, bottom + pad)
        inside = _area(soft_table, stride, left, top, right, bottom)
        covered = _area(raw_table, stride, left, top, right, bottom)
        around = _area(raw_table, stride, near_left, near_top, near_right, near_bottom) - _area(
            raw_table, stride, left, top, right, bottom
        )
        outside = 0
        if content is not None and not (content[0] <= cx * base.width <= content[2] and content[1] <= cy * base.height <= content[3]):
            outside = 1
        cell = (min(2, int(cx * 3)), min(2, int(cy * 3)))
        border = int(left < margin or top < margin or right > base.width - margin or bottom > base.height - margin)
        distance = (cx - prefer[0]) ** 2 + (cy - prefer[1]) ** 2
        return (outside, inside, covered, 0 if around else 1, 1 if cell in used_cells else 0, border, distance)

    def search(step_px: int, x0: int, y0: int, x1: int, y1: int) -> tuple[int, int] | None:
        best_key: tuple[float, ...] | None = None
        best_at: tuple[int, int] | None = None
        top = y0
        while top <= y1:
            left = x0
            while left <= x1:
                key = score(left, top)
                if best_key is None or key < best_key:
                    best_key = key
                    best_at = (left, top)
                left += step_px
            top += step_px
        return best_at

    coarse = search(step, 0, 0, base.width - target_w, base.height - target_h)
    if coarse is None:
        raise SlonError("Scene has no place for the elephant")
    left0 = max(0, coarse[0] - step)
    top0 = max(0, coarse[1] - step)
    left1 = min(base.width - target_w, coarse[0] + step)
    top1 = min(base.height - target_h, coarse[1] + step)
    fine = search(1, left0, top0, left1, top1) or coarse
    chosen = score(fine[0], fine[1])
    cx = (fine[0] + target_w / 2) / base.width
    cy = (fine[1] + target_h / 2) / base.height
    return cx, cy, chosen[1] == 0 and chosen[2] == 0


def knockout_background(
    image: Image.Image,
    *,
    white_threshold: int = 235,
) -> Image.Image:
    """Make the exterior transparent. White regions enclosed by the outline stay opaque.

    A one-pixel gap in the outline is closed only for the flood fill, so the interior
    coloring regions are not turned transparent.
    """
    rgba = image.convert("RGBA")
    width, height = rgba.size
    source = rgba.load()
    barrier = Image.new("L", (width, height), 0)
    wall = barrier.load()
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = source[x, y]
            if alpha >= 16 and min(red, green, blue) < white_threshold:
                wall[x, y] = 255
    barrier = barrier.filter(ImageFilter.MaxFilter(3))
    wall = barrier.load()

    visited = bytearray(width * height)
    stack: list[tuple[int, int]] = []
    for x in range(width):
        stack.append((x, 0))
        stack.append((x, height - 1))
    for y in range(height):
        stack.append((0, y))
        stack.append((width - 1, y))

    while stack:
        x, y = stack.pop()
        index = y * width + x
        if visited[index] or wall[x, y]:
            continue
        visited[index] = 1
        if x > 0:
            stack.append((x - 1, y))
        if x + 1 < width:
            stack.append((x + 1, y))
        if y > 0:
            stack.append((x, y - 1))
        if y + 1 < height:
            stack.append((x, y + 1))

    output = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dest = output.load()
    for y in range(height):
        for x in range(width):
            if visited[y * width + x]:
                continue
            red, green, blue, alpha = source[x, y]
            if alpha < 16:
                continue
            if (red + green + blue) // 3 < 128:
                dest[x, y] = (0, 0, 0, 255)
            else:
                dest[x, y] = (255, 255, 255, 255)
    return output


def crop_alpha(image: Image.Image) -> Image.Image:
    alpha = image.convert("RGBA").getchannel("A")
    box = alpha.getbbox()
    if box is None:
        raise SlonError("Elephant asset is empty after background removal")
    return image.convert("RGBA").crop(box)


def binarize_rgba(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    output = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    source = rgba.load()
    dest = output.load()
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = source[x, y]
            if alpha < 128:
                continue
            if (red + green + blue) // 3 < 128:
                dest[x, y] = (0, 0, 0, 255)
            else:
                dest[x, y] = (255, 255, 255, 255)
    return output


def prepare_elephant(image: Image.Image) -> Image.Image:
    return crop_alpha(knockout_background(image))


# Crops of one standing elephant. Each page shows a different piece, so the
# silhouette is not the same on every puzzle. Fractions are of the asset.
_PARTS: dict[str, tuple[float, float, float, float]] = {
    "full": (0.0, 0.0, 1.0, 1.0),
    "head": (0.05, 0.0, 0.90, 0.40),
    "trunk": (0.0, 0.18, 0.46, 0.62),
    "ear": (0.0, 0.02, 0.36, 0.38),
    "legs": (0.18, 0.55, 0.64, 0.45),
    "rear": (0.52, 0.08, 0.48, 0.58),
}

_VIEWS: dict[str, tuple[tuple[str, bool], ...]] = {
    "easy": (("full", False), ("head", False), ("body", True), ("ear", False)),
    "medium": (("trunk", False), ("head", True), ("ear", True), ("legs", False)),
    "hard": (("trunk", True), ("ear", False), ("trunk", False), ("rear", True)),
}


def elephant_view(index: int, difficulty: str) -> tuple[str, bool]:
    """Which piece of the elephant this page hides, and whether it is mirrored."""
    options = _VIEWS.get(difficulty, _VIEWS["medium"])
    # "body" is stored as the legs-and-belly crop; the easy list says body.
    name, flip = options[(index - 1) % len(options)]
    if name == "body":
        name = "legs"
    return name, flip


def slice_elephant(sprite: Image.Image, name: str, flip: bool) -> Image.Image:
    """Cut one recognizable piece out of the shared elephant. Interior white stays opaque."""
    image = sprite.convert("RGBA")
    x, y, width, height = _PARTS.get(name, _PARTS["full"])
    pixel_w, pixel_h = image.size
    left = int(x * pixel_w)
    top = int(y * pixel_h)
    right = max(left + 1, int((x + width) * pixel_w))
    bottom = max(top + 1, int((y + height) * pixel_h))
    piece = image.crop((left, top, right, bottom))
    if flip:
        piece = piece.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return crop_alpha(piece)


def _fit_center(
    cx: float,
    cy: float,
    width_px: int,
    height_px: int,
    scene_w: int,
    scene_h: int,
    *,
    allow_nudge: bool,
) -> tuple[int, int]:
    left = round(cx * scene_w - width_px / 2)
    top = round(cy * scene_h - height_px / 2)
    if width_px >= scene_w or height_px >= scene_h:
        raise SlonError("Elephant is larger than the scene")
    nudged_left = min(max(left, 0), scene_w - width_px)
    nudged_top = min(max(top, 0), scene_h - height_px)
    if (nudged_left, nudged_top) != (left, top) and not allow_nudge:
        raise SlonError("Elephant would be clipped at this position")
    return nudged_left, nudged_top


def composite_elephant(
    scene: Image.Image,
    elephant: Image.Image,
    *,
    scene_id: str,
    cx: float,
    cy: float,
    scale: float,
    rotation: float = 0,
    manual: bool = False,
    allow_nudge: bool = False,
    occlusion: str | None = None,
) -> tuple[Image.Image, Placement]:
    """Clear scene lines under the elephant silhouette, then draw its black outlines.

    Interior white stays white. Pixels outside the silhouette are left unchanged.
    """
    base = scene.convert("L")
    sprite = elephant.convert("RGBA")
    if abs(rotation) > 0.01:
        sprite = binarize_rgba(sprite.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC))
        sprite = crop_alpha(sprite)
    target_w, target_h = sprite_pixel_size(base.width, sprite, scale)
    sprite = binarize_rgba(sprite.resize((target_w, target_h), Image.Resampling.LANCZOS))
    left, top = _fit_center(
        cx,
        cy,
        target_w,
        target_h,
        base.width,
        base.height,
        allow_nudge=allow_nudge,
    )
    output = base.copy()
    dest = output.load()
    pixels = sprite.load()
    for y in range(target_h):
        for x in range(target_w):
            red, _green, _blue, alpha = pixels[x, y]
            if alpha < 16:
                continue
            dest[left + x, top + y] = 0 if red < 128 else 255
    actual_cx = (left + target_w / 2) / base.width
    actual_cy = (top + target_h / 2) / base.height
    placement = Placement(
        scene_id=scene_id,
        cx=actual_cx,
        cy=actual_cy,
        scale=scale,
        rotation=rotation,
        manual=manual,
        occlusion=occlusion,
        bbox_x=left / base.width,
        bbox_y=top / base.height,
        bbox_w=target_w / base.width,
        bbox_h=target_h / base.height,
    )
    return output, placement


def placement_warnings(placement: Placement, difficulty: str) -> list[str]:
    warnings: list[str] = []
    if (
        placement.bbox_x < 0
        or placement.bbox_y < 0
        or placement.bbox_x + placement.bbox_w > 1.001
        or placement.bbox_y + placement.bbox_h > 1.001
    ):
        warnings.append("elephant is clipped")
    low, high = _BANDS[difficulty]
    if not low - 0.008 <= placement.bbox_w <= high + 0.008:
        warnings.append("elephant size is outside the difficulty band")
    if placement.bbox_w < 0.04:
        warnings.append("elephant may be too small to recognize when printed")
    return warnings


def circle_mm(
    placement: Placement,
    origin_x: float,
    origin_y: float,
    fitted_w: float,
    fitted_h: float,
) -> tuple[float, float, float]:
    """Circle center and radius in millimetres, from the stored bounding box."""
    cx = origin_x + (placement.bbox_x + placement.bbox_w / 2) * fitted_w
    cy = origin_y + (placement.bbox_y + placement.bbox_h / 2) * fitted_h
    radius = max(placement.bbox_w * fitted_w, placement.bbox_h * fitted_h) / 2 * 1.35
    return cx, cy, radius


def draw_solution(scene: Image.Image, placement: Placement) -> Image.Image:
    """The same puzzle image with a double circle. No second drawing from the image model."""
    rgb = scene.convert("RGB")
    draw = ImageDraw.Draw(rgb)
    width, height = rgb.size
    cx = (placement.bbox_x + placement.bbox_w / 2) * width
    cy = (placement.bbox_y + placement.bbox_h / 2) * height
    radius = max(placement.bbox_w * width, placement.bbox_h * height) / 2 * 1.35
    radius = max(radius, 3)
    box = (cx - radius, cy - radius, cx + radius, cy + radius)
    draw.ellipse(box, outline=0, width=2)
    inset = max(2, radius * 0.18)
    inner = (
        cx - radius + inset,
        cy - radius + inset,
        cx + radius - inset,
        cy + radius - inset,
    )
    draw.ellipse(inner, outline=0, width=2)
    return rgb.convert("L")
