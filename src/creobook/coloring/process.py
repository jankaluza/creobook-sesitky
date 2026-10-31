"""Turn a generated illustration into print-ready black-and-white line art."""

from __future__ import annotations

import io
from dataclasses import dataclass, field

from PIL import Image

from creobook.coloring.models import ProcessSettings


@dataclass
class QualityReport:
    width: int
    height: int
    white_ratio: float
    dark_ratio: float
    largest_dark_ratio: float
    warnings: list[str] = field(default_factory=list)


def _components(image: Image.Image) -> tuple[int, int]:
    """Return (dark pixel count, largest connected dark component)."""
    width, height = image.size
    pixels = image.load()
    assert pixels is not None
    seen = bytearray(width * height)
    dark = 0
    largest = 0
    for y in range(height):
        for x in range(width):
            index = y * width + x
            if seen[index]:
                continue
            seen[index] = 1
            if pixels[x, y] >= 128:
                continue
            stack = [(x, y)]
            size = 0
            while stack:
                cx, cy = stack.pop()
                size += 1
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    neighbor = ny * width + nx
                    if seen[neighbor] or pixels[nx, ny] >= 128:
                        continue
                    seen[neighbor] = 1
                    stack.append((nx, ny))
            dark += size
            if size > largest:
                largest = size
    return dark, largest


def _erase_small(image: Image.Image, min_speck: int) -> Image.Image:
    if min_speck <= 1:
        return image
    width, height = image.size
    pixels = image.load()
    assert pixels is not None
    seen = bytearray(width * height)
    output = image.copy()
    out_px = output.load()
    assert out_px is not None
    for y in range(height):
        for x in range(width):
            index = y * width + x
            if seen[index]:
                continue
            seen[index] = 1
            if pixels[x, y] >= 128:
                continue
            stack = [(x, y)]
            cells: list[tuple[int, int]] = []
            while stack:
                cx, cy = stack.pop()
                cells.append((cx, cy))
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if nx < 0 or ny < 0 or nx >= width or ny >= height:
                        continue
                    neighbor = ny * width + nx
                    if seen[neighbor] or pixels[nx, ny] >= 128:
                        continue
                    seen[neighbor] = 1
                    stack.append((nx, ny))
            if len(cells) < min_speck:
                for cx, cy in cells:
                    out_px[cx, cy] = 255
    return output


def process_line_art(
    source: Image.Image,
    settings: ProcessSettings | None = None,
    *,
    max_px: tuple[int, int] | None = None,
) -> Image.Image:
    """Grayscale, whiten the background, threshold, drop specks. Never upscale."""
    settings = settings or ProcessSettings()
    gray = source.convert("RGB").convert("L")
    # Near-white paper becomes pure white before the line threshold.
    whitened = gray.point(lambda value: 255 if value >= settings.white_threshold else value)
    if max_px is not None:
        limit_w, limit_h = max_px
        if whitened.width > limit_w or whitened.height > limit_h:
            scale = min(limit_w / whitened.width, limit_h / whitened.height)
            resized = (
                max(1, int(whitened.width * scale)),
                max(1, int(whitened.height * scale)),
            )
            whitened = whitened.resize(resized, Image.Resampling.LANCZOS)
    lines = whitened.point(lambda value: 0 if value < settings.black_threshold else 255)
    return _erase_small(lines.convert("L"), settings.min_speck)


def assess(image: Image.Image) -> QualityReport:
    """Lightweight warnings. Unusual images stay available for manual review."""
    gray = image.convert("L")
    width, height = gray.size
    total = width * height
    hist = gray.histogram()
    white = hist[255]
    dark_pixels, largest = _components(gray)
    mid = total - white - hist[0]
    white_ratio = white / total
    dark_ratio = dark_pixels / total
    largest_ratio = largest / total
    warnings: list[str] = []
    if height <= width:
        warnings.append("illustration is not portrait")
    if dark_ratio < 0.004:
        warnings.append("illustration looks blank")
    if dark_ratio > 0.35:
        warnings.append("illustration is very dense")
    if largest_ratio > 0.15:
        warnings.append("a large solid black region may not be colorable")
    if mid > total * 0.02:
        warnings.append("unexpected gray pixels remain")
    if white_ratio < 0.45:
        warnings.append("background is not mostly white")
    return QualityReport(
        width=width,
        height=height,
        white_ratio=white_ratio,
        dark_ratio=dark_ratio,
        largest_dark_ratio=largest_ratio,
        warnings=warnings,
    )


def png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.convert("L").save(buffer, format="PNG")
    return buffer.getvalue()


def open_png(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))
