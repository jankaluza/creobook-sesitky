"""Turn a filled silhouette into numbered dots and an answer outline.

Numbers are placed here, never by the image model. The contour is the outer
boundary of the largest dark shape.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from creobook.dots.models import DotsError

# Clockwise from north. Image y grows downward.
_DIRS = ((0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1))


@dataclass(frozen=True)
class Dot:
    number: int
    x: float
    y: float
    label_x: float
    label_y: float
    label_w: float
    label_h: float


@dataclass(frozen=True)
class PuzzleGeometry:
    dots: tuple[Dot, ...]
    font_pt: float
    content_width: float
    content_height: float

    @property
    def max_number(self) -> int:
        return self.dots[-1].number


def mask_from_png(png: bytes, *, max_side: int = 480) -> list[list[bool]]:
    import io

    from PIL import Image

    image = Image.open(io.BytesIO(png)).convert("L")
    image.thumbnail((max_side, max_side), Image.Resampling.BOX)
    width, height = image.size
    pixels = image.load()
    assert pixels is not None
    dark = 0
    total = width * height
    mask = []
    for y in range(height):
        row = []
        for x in range(width):
            filled = pixels[x, y] < 160
            row.append(filled)
            dark += int(filled)
        mask.append(row)
    if total == 0 or dark / total < 0.01:
        raise DotsError("The silhouette is missing. The image is almost white.")
    if dark / total > 0.85:
        mask = [[not cell for cell in row] for row in mask]
    return largest_component(mask)


def largest_component(mask: list[list[bool]]) -> list[list[bool]]:
    height = len(mask)
    width = len(mask[0]) if height else 0
    seen = [[False] * width for _ in range(height)]
    best: list[tuple[int, int]] = []
    for y in range(height):
        for x in range(width):
            if not mask[y][x] or seen[y][x]:
                continue
            stack = [(x, y)]
            seen[y][x] = True
            cells: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                cells.append((cx, cy))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < width and 0 <= ny < height and mask[ny][nx] and not seen[ny][nx]:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if len(cells) > len(best):
                best = cells
    if len(best) < 30:
        raise DotsError("The silhouette is too small to trace.")
    out = [[False] * width for _ in range(height)]
    for x, y in best:
        out[y][x] = True
    return out


def trace_contour(mask: list[list[bool]]) -> list[tuple[float, float]]:
    """Outer boundary of a filled shape, in pixel-center coordinates."""
    height = len(mask)
    width = len(mask[0]) if height else 0
    start = None
    for y in range(height):
        for x in range(width):
            if mask[y][x]:
                start = (x, y)
                break
        if start:
            break
    if start is None:
        raise DotsError("The silhouette has no outer contour.")
    sx, sy = start
    x, y = sx, sy
    back = 6
    contour: list[tuple[float, float]] = []
    limit = width * height
    while len(contour) <= limit:
        contour.append((x + 0.5, y + 0.5))
        found = None
        for step in range(1, 9):
            direction = (back + step) % 8
            dx, dy = _DIRS[direction]
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height and mask[ny][nx]:
                found = (nx, ny, direction)
                break
        if found is None:
            break
        nx, ny, direction = found
        if (nx, ny) == (sx, sy) and len(contour) > 8:
            break
        x, y = nx, ny
        back = (direction + 4) % 8
    else:
        raise DotsError("The contour did not close. Regenerate this puzzle.")
    if len(contour) < 12:
        raise DotsError("The contour is too short to be a picture.")
    return contour


def _distance_to_segment(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    ax, ay = start
    bx, by = end
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    if length == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def simplify(points: list[tuple[float, float]], epsilon: float) -> list[tuple[float, float]]:
    """Douglas–Peucker on an open chain."""
    if len(points) < 3:
        return list(points)
    end = len(points) - 1
    keep = [False] * len(points)
    keep[0] = keep[end] = True
    stack = [(0, end)]
    while stack:
        left, right = stack.pop()
        farthest = 0.0
        index = left
        for cursor in range(left + 1, right):
            distance = _distance_to_segment(points[cursor], points[left], points[right])
            if distance > farthest:
                farthest = distance
                index = cursor
        if farthest > epsilon and index not in (left, right):
            keep[index] = True
            stack.append((left, index))
            stack.append((index, right))
    return [point for point, flag in zip(points, keep, strict=True) if flag]


def simplify_closed(points: list[tuple[float, float]], epsilon: float = 1.6) -> list[tuple[float, float]]:
    if len(points) < 8:
        return list(points)
    simplified = simplify([*points, points[0]], epsilon)
    if len(simplified) >= 2 and math.hypot(
        simplified[0][0] - simplified[-1][0], simplified[0][1] - simplified[-1][1]
    ) < 1e-6:
        simplified = simplified[:-1]
    if len(simplified) < 8:
        return simplify_closed(points, epsilon / 2) if epsilon > 0.4 else list(points)
    return simplified


def smooth_closed(points: list[tuple[float, float]], passes: int = 2) -> list[tuple[float, float]]:
    current = list(points)
    for _ in range(passes):
        count = len(current)
        nxt = []
        for index in range(count):
            ax, ay = current[(index - 1) % count]
            bx, by = current[index]
            cx, cy = current[(index + 1) % count]
            nxt.append(((ax + 2 * bx + cx) / 4, (ay + 2 * by + cy) / 4))
        current = nxt
    return current


def _turn(prev: tuple[float, float], current: tuple[float, float], nxt: tuple[float, float]) -> float:
    ax, ay = current[0] - prev[0], current[1] - prev[1]
    bx, by = nxt[0] - current[0], nxt[1] - current[1]
    la = math.hypot(ax, ay) or 1.0
    lb = math.hypot(bx, by) or 1.0
    dot = max(-1.0, min(1.0, (ax * bx + ay * by) / (la * lb)))
    return math.acos(dot)


def sample_closed(points: list[tuple[float, float]], count: int) -> list[tuple[float, float]]:
    """Place ``count`` points around a closed path, denser where it turns."""
    if count < 2:
        raise DotsError("A puzzle needs at least two dots.")
    total_points = len(points)
    if total_points < 3:
        raise DotsError("The contour is too simple.")
    weights = []
    for index in range(total_points):
        turn = _turn(
            points[(index - 1) % total_points],
            points[index],
            points[(index + 1) % total_points],
        )
        weights.append(1.0 + 5.0 * (turn / math.pi))
    edges: list[float] = []
    total = 0.0
    for index in range(total_points):
        nxt = points[(index + 1) % total_points]
        length = math.hypot(nxt[0] - points[index][0], nxt[1] - points[index][1])
        weight = length * (weights[index] + weights[(index + 1) % total_points]) / 2
        edges.append(weight)
        total += weight
    if total <= 0:
        raise DotsError("The contour has no length.")
    sampled: list[tuple[float, float]] = []
    edge_index = 0
    walked = 0.0
    for step in range(count):
        target = total * step / count
        while edge_index < total_points - 1 and walked + edges[edge_index] < target:
            walked += edges[edge_index]
            edge_index += 1
        span = edges[edge_index] or 1.0
        blend = max(0.0, min(1.0, (target - walked) / span))
        start = points[edge_index]
        end = points[(edge_index + 1) % total_points]
        sampled.append(
            (start[0] + blend * (end[0] - start[0]), start[1] + blend * (end[1] - start[1]))
        )
    leftmost = min(range(count), key=lambda index: (sampled[index][0], sampled[index][1]))
    return sampled[leftmost:] + sampled[:leftmost]


def _segments_cross(
    a: tuple[float, float],
    b: tuple[float, float],
    c: tuple[float, float],
    d: tuple[float, float],
) -> bool:
    def orient(p: tuple[float, float], q: tuple[float, float], r: tuple[float, float]) -> float:
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    o1, o2 = orient(a, b, c), orient(a, b, d)
    o3, o4 = orient(c, d, a), orient(c, d, b)
    return o1 * o2 < 0 and o3 * o4 < 0


def _font_pt(count: int, page_format: str) -> list[float]:
    if count <= 31:
        sizes = [8.0, 7.0, 6.0]
    elif count <= 51:
        sizes = [6.5, 5.5, 5.0]
    elif count <= 76:
        sizes = [5.5, 5.0, 4.5]
    else:
        sizes = [5.0, 4.5, 4.0]
    if page_format == "A6":
        sizes = [max(4.0, size - 1.0) for size in sizes]
    return sizes


def _label_box(number: int, font_pt: float) -> tuple[float, float]:
    font_mm = font_pt * 0.3528
    width = max(font_mm, 0.62 * font_mm * len(str(number))) + 0.4
    return width, font_mm + 0.3


def _boxes_overlap(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
    gap: float = 0.35,
) -> bool:
    ax, ay, aw, ah = left
    bx, by, bw, bh = right
    return abs(ax - bx) * 2 < (aw + bw + gap) and abs(ay - by) * 2 < (ah + bh + gap)


def place_labels(
    points: list[tuple[float, float]],
    *,
    content_width: float,
    content_height: float,
    page_format: str,
    top: float = 11.0,
    bottom: float = 7.0,
) -> PuzzleGeometry:
    count = len(points)
    if count < 11:
        raise DotsError("A puzzle needs numbers from 0 through at least 10.")
    cx = sum(point[0] for point in points) / count
    cy = sum(point[1] for point in points) / count
    outward: list[tuple[float, float]] = []
    for index, (x, y) in enumerate(points):
        prev = points[(index - 1) % count]
        nxt = points[(index + 1) % count]
        tx, ty = nxt[0] - prev[0], nxt[1] - prev[1]
        left = (-ty, tx)
        right = (ty, -tx)
        away_x, away_y = x - cx, y - cy
        normal = left if left[0] * away_x + left[1] * away_y >= right[0] * away_x + right[1] * away_y else right
        scale = math.hypot(normal[0], normal[1]) or 1.0
        outward.append((normal[0] / scale, normal[1] / scale))

    last_error = "Numbers overlap."
    for font_pt in _font_pt(count, page_format):
        placed: list[Dot] = []
        failed = False
        for index, (x, y) in enumerate(points):
            width, height = _label_box(index, font_pt)
            ox, oy = outward[index]
            base = math.atan2(oy, ox)
            choice = None
            for radius in (2.4, 3.6, 5.0):
                for turn in (0, 20, -20, 45, -45, 70, -70, 110, -110, 160, 180):
                    angle = math.radians(turn) + base
                    lx = x + radius * math.cos(angle)
                    ly = y + radius * math.sin(angle)
                    if not _inside(lx, ly, width, height, content_width, content_height, top, bottom):
                        continue
                    box = (lx, ly, width, height)
                    if any(
                        _boxes_overlap(box, (dot.label_x, dot.label_y, dot.label_w, dot.label_h))
                        for dot in placed
                    ):
                        continue
                    if any(
                        math.hypot(lx - dot.x, ly - dot.y) < 0.7 + max(width, height) / 2
                        for dot in (*placed, Dot(index, x, y, x, y, 0.8, 0.8))
                    ):
                        continue
                    if any(math.hypot(lx - px, ly - py) < 1.8 for px, py in points):
                        continue
                    choice = (lx, ly, width, height)
                    break
                if choice:
                    break
            if choice is None:
                failed = True
                last_error = f"Number {index} has no free spot."
                break
            lx, ly, width, height = choice
            placed.append(Dot(index, x, y, lx, ly, width, height))
        if not failed and len(placed) == count:
            geometry = PuzzleGeometry(tuple(placed), font_pt, content_width, content_height)
            validate_geometry(geometry, top=top, bottom=bottom)
            return geometry
    raise DotsError(
        f"{last_error} The picture is too detailed for {count - 1} numbers. "
        "Regenerate the puzzle or choose a lower maximum."
    )


def _inside(
    x: float,
    y: float,
    width: float,
    height: float,
    content_width: float,
    content_height: float,
    top: float,
    bottom: float,
) -> bool:
    return (
        x - width / 2 >= 0.4
        and x + width / 2 <= content_width - 0.4
        and y - height / 2 >= top
        and y + height / 2 <= content_height - bottom
    )


def validate_geometry(geometry: PuzzleGeometry, *, top: float = 11.0, bottom: float = 7.0) -> None:
    dots = geometry.dots
    numbers = [dot.number for dot in dots]
    expected = list(range(len(dots)))
    if numbers != expected:
        raise DotsError("Numbering must be 0, 1, 2, … with every integer once.")
    count = len(dots)
    for index, dot in enumerate(dots):
        if not _inside(
            dot.x,
            dot.y,
            1.2,
            1.2,
            geometry.content_width,
            geometry.content_height,
            top,
            bottom,
        ):
            raise DotsError(f"Dot {dot.number} sits outside the page.")
        if not _inside(
            dot.label_x,
            dot.label_y,
            dot.label_w,
            dot.label_h,
            geometry.content_width,
            geometry.content_height,
            top,
            bottom,
        ):
            raise DotsError(f"Number {dot.number} sits outside the page.")
        for other in dots[index + 1 :]:
            if math.hypot(dot.x - other.x, dot.y - other.y) < 0.9:
                raise DotsError(f"Dots {dot.number} and {other.number} are on top of each other.")
            if _boxes_overlap(
                (dot.label_x, dot.label_y, dot.label_w, dot.label_h),
                (other.label_x, other.label_y, other.label_w, other.label_h),
                gap=0.2,
            ):
                raise DotsError(f"Numbers {dot.number} and {other.number} overlap.")
    lengths = []
    for index, dot in enumerate(dots):
        nxt = dots[(index + 1) % count]
        lengths.append(math.hypot(nxt.x - dot.x, nxt.y - dot.y))
    shortest = min(lengths)
    longest = max(lengths)
    if shortest < 0.8:
        raise DotsError("Two neighbouring dots are too close.")
    if longest > max(24.0, sum(lengths) * 0.22):
        raise DotsError("A gap between dots is long enough to hide the shape.")
    for index in range(count):
        turn = _turn(
            (dots[(index - 1) % count].x, dots[(index - 1) % count].y),
            (dots[index].x, dots[index].y),
            (dots[(index + 1) % count].x, dots[(index + 1) % count].y),
        )
        if turn > math.radians(165):
            raise DotsError(f"Dot {dots[index].number} makes a spike the line cannot follow.")
    points = [(dot.x, dot.y) for dot in dots]
    for left in range(count):
        a, b = points[left], points[(left + 1) % count]
        for right in range(left + 1, count):
            if abs(left - right) <= 1 or abs(left - right) == count - 1:
                continue
            c, d = points[right], points[(right + 1) % count]
            if _segments_cross(a, b, c, d):
                raise DotsError("The outline crosses itself, so the order would be ambiguous.")


def fit_points(
    points: list[tuple[float, float]],
    *,
    content_width: float,
    content_height: float,
    top: float = 11.0,
    bottom: float = 7.0,
    pad: float = 8.0,
) -> list[tuple[float, float]]:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max(max_x - min_x, 1.0)
    span_y = max(max_y - min_y, 1.0)
    box_w = content_width - 2 * pad
    box_h = content_height - top - bottom - 2 * pad
    if box_w <= 4 or box_h <= 4:
        raise DotsError("The page is too small for the puzzle.")
    scale = min(box_w / span_x, box_h / span_y)
    used_w = span_x * scale
    used_h = span_y * scale
    origin_x = pad + (box_w - used_w) / 2
    origin_y = top + pad + (box_h - used_h) / 2
    return [
        (origin_x + (x - min_x) * scale, origin_y + (y - min_y) * scale) for x, y in points
    ]


def geometry_from_png(
    png: bytes,
    *,
    max_number: int,
    content_width: float,
    content_height: float,
    page_format: str,
) -> PuzzleGeometry:
    mask = mask_from_png(png)
    contour = smooth_closed(simplify_closed(trace_contour(mask)))
    sampled = sample_closed(contour, max_number + 1)
    fitted = fit_points(sampled, content_width=content_width, content_height=content_height)
    return place_labels(
        fitted,
        content_width=content_width,
        content_height=content_height,
        page_format=page_format,
    )


def puzzle_svg(geometry: PuzzleGeometry, *, page_width: float, page_height: float, answer: bool) -> str:
    """Vector drawing in page coordinates. The puzzle itself has no connecting lines."""
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{page_width}mm" height="{page_height}mm" '
        f'viewBox="0 0 {page_width} {page_height}">',
        '<rect width="100%" height="100%" fill="white"/>',
    ]
    if answer:
        chain = " ".join(f"{dot.x:.2f},{dot.y:.2f}" for dot in geometry.dots)
        first = geometry.dots[0]
        parts.append(
            f'<polyline points="{chain} {first.x:.2f},{first.y:.2f}" '
            'fill="none" stroke="black" stroke-width="0.35" stroke-linejoin="round"/>'
        )
    for dot in geometry.dots:
        if dot.number == 0:
            parts.append(
                f'<circle cx="{dot.x:.2f}" cy="{dot.y:.2f}" r="1.7" fill="none" stroke="black" stroke-width="0.25"/>'
            )
        parts.append(f'<circle cx="{dot.x:.2f}" cy="{dot.y:.2f}" r="0.6" fill="black"/>')
        parts.append(
            f'<text x="{dot.label_x:.2f}" y="{dot.label_y:.2f}" font-size="{geometry.font_pt * 0.3528:.2f}" '
            f'font-family="Inter, DejaVu Sans, sans-serif" text-anchor="middle" '
            f'dominant-baseline="middle">{dot.number}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def dot_payload(dot: Dot) -> dict[str, float | int]:
    return {
        "n": dot.number,
        "x": round(dot.x, 2),
        "y": round(dot.y, 2),
        "lx": round(dot.label_x, 2),
        "ly": round(dot.label_y, 2),
        "lw": round(dot.label_w, 2),
        "lh": round(dot.label_h, 2),
    }
