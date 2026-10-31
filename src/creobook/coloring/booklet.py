"""A5/A6 coloring pages and booklet imposition on top of the existing PDF pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from creobook.coloring.models import PAGE_FORMATS, ColoringConfig, ColoringError, Illustration
from creobook.compiler import compile_template
from creobook.imposition import impose_booklet
from creobook.theme import Theme, load_theme

AGE_LABELS = {"3-5": "3–5 let", "6-8": "6–8 let", "9-12": "9–12 let"}


def sheet_pairs(page_count: int) -> list[tuple[int, int]]:
    """Pages that share the two sides of one half of a folded sheet."""
    if page_count <= 0 or page_count % 4 != 0:
        raise ValueError("booklet page count must be a positive multiple of 4")
    pairs: list[tuple[int, int]] = []
    sheets = page_count // 4
    for sheet in range(sheets):
        pairs.append((page_count - 2 * sheet, 2 * sheet + 2))
        pairs.append((2 * sheet + 1, page_count - 2 * sheet - 1))
    return pairs


def physical_reverse(page: int, page_count: int) -> int:
    for left, right in sheet_pairs(page_count):
        if page == left:
            return right
        if page == right:
            return left
    raise ValueError(f"page {page} is outside a {page_count}-page booklet")


def _content_pages(config: ColoringConfig, illustrations: list[Illustration]) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = [
        {
            "kind": "cover",
            "title": config.title,
            "subtitle": f"Omalovánky · {AGE_LABELS[config.age_group]}",
            "footer": "CreoBook.cz",
        }
    ]
    for index, item in enumerate(illustrations, start=1):
        pages.append(
            {
                "kind": "illustration",
                "number": index,
                "id": item.id,
                "title": item.title,
                "image": f"coloring-images/{index:02d}-{item.id}.png",
            }
        )
    return pages


def single_sided_pages(content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Put drawings on the outer faces and leave the paper reverse blank for markers."""
    sheets = max(1, (len(content) + 1) // 2)
    while True:
        count = sheets * 4
        fronts: list[int] = []
        for sheet in range(sheets):
            fronts.append(count - 2 * sheet)
            fronts.append(2 * sheet + 1)
        fronts.sort()
        if len(fronts) >= len(content):
            break
        sheets += 1
    pages: list[dict[str, Any]] = [{"kind": "blank"} for _ in range(count)]
    for slot, item in zip(fronts, content, strict=False):
        pages[slot - 1] = item
    return pages


def filled_illustration_count(requested: int) -> int:
    """Smallest count at or above ``requested`` that fills a booklet signature.

    One cover plus the illustrations must be a multiple of four, otherwise the
    folded sheet would contain blank pages.
    """
    if requested < 1:
        raise ValueError("illustration count must be positive")
    remainder = (1 + requested) % 4
    if remainder == 0:
        return requested
    return requested + (4 - remainder)


def reading_pages(config: ColoringConfig, illustrations: list[Illustration]) -> list[dict[str, Any]]:
    content = _content_pages(config, illustrations)
    if config.single_sided:
        return single_sided_pages(content)
    if len(content) % 4 != 0:
        raise ColoringError(
            f"Sešit má {len(content)} stran. Počet stran musí být násobek 4, "
            "aby v něm nezůstaly prázdné stránky."
        )
    return content


def compile_coloring_pdfs(
    config: ColoringConfig,
    illustrations: list[Illustration],
    image_files: dict[str, Path],
    output_dir: Path,
    *,
    theme: Theme | None = None,
    fold_guide: bool = False,
) -> dict[str, Path]:
    theme = theme or load_theme()
    spec = PAGE_FORMATS[config.page_format]
    pages = reading_pages(config, illustrations)
    data = {
        "page_type": "coloring_booklet",
        "theme": theme.to_typst_dict(),
        "title": config.title,
        "page_width_mm": spec["width_mm"],
        "page_height_mm": spec["height_mm"],
        "margin_inside_mm": spec["margin_inside_mm"],
        "margin_outside_mm": spec["margin_outside_mm"],
        "margin_top_mm": spec["margin_top_mm"],
        "margin_bottom_mm": spec["margin_bottom_mm"],
        "pages": pages,
    }
    slug = Path(config.output_directory).name or "omalovanky"
    reading = output_dir / f"{slug}-{config.page_format.lower()}.pdf"
    imposed = output_dir / f"{slug}-tisk.pdf"
    extra = {
        f"games/{page['image']}": image_files[page["id"]]
        for page in pages
        if page.get("kind") == "illustration"
    }
    compile_template("games/coloring.typ", data, reading, theme=theme, extra_files=extra)
    impose_booklet(
        reading,
        imposed,
        theme=theme,
        fold_guide=fold_guide,
        sheet_width_mm=spec["sheet_width_mm"],
        sheet_height_mm=spec["sheet_height_mm"],
    )
    return {"reading": reading, "print": imposed}
