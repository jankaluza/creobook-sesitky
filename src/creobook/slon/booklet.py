"""A5/A6 Najdi slona pages and booklet imposition."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from creobook.coloring.models import PAGE_FORMATS
from creobook.compiler import compile_template
from creobook.imposition import impose_booklet
from creobook.slon.composite import circle_mm
from creobook.slon.models import Placement, SlonConfig
from creobook.theme import Theme, load_theme

AGE_LABELS = {"3-5": "3–5 let", "6-8": "6–8 let", "9-12": "9–12 let"}
LEVEL_LABELS = {"easy": "snadné", "medium": "střední", "hard": "těžší"}


@dataclass
class PuzzleView:
    index: int
    scene_id: str
    placement: Placement
    width: int
    height: int
    warnings: list[str] | None = None
    difficulty: str = "medium"
    reference: str = "slon-images/elephant.png"


def content_box(page_format: str) -> tuple[float, float]:
    spec = PAGE_FORMATS[page_format]
    width = spec["width_mm"] - spec["margin_inside_mm"] - spec["margin_outside_mm"]
    height = spec["height_mm"] - spec["margin_top_mm"] - spec["margin_bottom_mm"]
    return width, height


def contain(box_w: float, box_h: float, img_w: int, img_h: int) -> tuple[float, float, float, float]:
    scale = min(box_w / img_w, box_h / img_h)
    drawn_w = img_w * scale
    drawn_h = img_h * scale
    return (box_w - drawn_w) / 2, (box_h - drawn_h) / 2, drawn_w, drawn_h


def _caption(puzzle: PuzzleView, show_level: bool) -> str:
    if show_level:
        return f"č. {puzzle.index} · {LEVEL_LABELS[puzzle.difficulty]}"
    return f"č. {puzzle.index}"


def _image_name(puzzle: PuzzleView) -> str:
    return f"slon-images/{puzzle.index:02d}-{puzzle.scene_id}.png"


def reading_pages(config: SlonConfig, puzzles: list[PuzzleView]) -> list[dict[str, Any]]:
    content_w, content_h = content_box(config.page_format)
    pages: list[dict[str, Any]] = [
        {
            "kind": "cover",
            "title": config.title,
            "subtitle": _cover_subtitle(config),
            "footer": "CreoBook.cz",
            "elephant": "slon-images/elephant.png",
        }
    ]
    header = 14.0
    for puzzle in puzzles:
        offset_x, offset_y, drawn_w, drawn_h = contain(
            content_w,
            content_h - header,
            puzzle.width,
            puzzle.height,
        )
        pages.append(
            {
                "kind": "puzzle",
                "number": puzzle.index,
                "id": puzzle.scene_id,
                "image": _image_name(puzzle),
                "elephant": puzzle.reference,
                "image_x_mm": offset_x,
                "image_y_mm": header + offset_y,
                "image_w_mm": drawn_w,
                "image_h_mm": drawn_h,
            }
        )
    if config.include_solutions and puzzles:
        mixed = len(set(config.page_difficulties())) > 1
        pages.extend(_solution_pages(puzzles, content_w, content_h, show_level=mixed))
    while len(pages) % 4:
        pages.append({"kind": "blank"})
    return pages


def _cover_subtitle(config: SlonConfig) -> str:
    subtitle = f"Najdi slona! · {AGE_LABELS[config.age_group]}"
    if len(set(config.page_difficulties())) > 1:
        return subtitle + " · snadné, střední i těžší"
    return subtitle


def _solution_pages(
    puzzles: list[PuzzleView],
    content_w: float,
    content_h: float,
    *,
    show_level: bool = False,
) -> list[dict[str, Any]]:
    columns, rows = 2, 2
    per_page = columns * rows
    gap = 3.0
    title_h = 8.0
    caption_h = 5.0
    cell_w = (content_w - gap * (columns - 1)) / columns
    cell_h = (content_h - title_h - gap * (rows - 1)) / rows
    pages: list[dict[str, Any]] = []
    for start in range(0, len(puzzles), per_page):
        thumbs: list[dict[str, Any]] = []
        for offset, puzzle in enumerate(puzzles[start : start + per_page]):
            column = offset % columns
            row = offset // columns
            box_x = column * (cell_w + gap)
            box_y = title_h + row * (cell_h + gap)
            ox, oy, drawn_w, drawn_h = contain(
                cell_w,
                cell_h - caption_h,
                puzzle.width,
                puzzle.height,
            )
            center_x, center_y, radius = circle_mm(
                puzzle.placement,
                box_x + ox,
                box_y + caption_h + oy,
                drawn_w,
                drawn_h,
            )
            thumbs.append(
                {
                    "id": puzzle.scene_id,
                    "image": _image_name(puzzle),
                    "caption": _caption(puzzle, show_level),
                    "caption_x_mm": box_x,
                    "caption_y_mm": box_y,
                    "image_x_mm": box_x + ox,
                    "image_y_mm": box_y + caption_h + oy,
                    "image_w_mm": drawn_w,
                    "image_h_mm": drawn_h,
                    "cx_mm": center_x,
                    "cy_mm": center_y,
                    "r_mm": radius,
                }
            )
        pages.append({"kind": "solution", "thumbs": thumbs})
    return pages


def compile_slon_pdfs(
    config: SlonConfig,
    puzzles: list[PuzzleView],
    image_files: dict[str, Path],
    elephant_file: Path,
    output_dir: Path,
    *,
    theme: Theme | None = None,
) -> dict[str, Path]:
    theme = theme or load_theme()
    spec = PAGE_FORMATS[config.page_format]
    pages = reading_pages(config, puzzles)
    data = {
        "page_type": "najdi_slona",
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
    slug = Path(config.output_directory).name or "najdi-slona"
    reading = output_dir / f"{slug}-{config.page_format.lower()}.pdf"
    imposed = output_dir / f"{slug}-tisk.pdf"
    extra: dict[str, Path] = {"games/slon-images/elephant.png": elephant_file}
    for page in pages:
        if page.get("kind") == "puzzle":
            extra[f"games/{page['image']}"] = image_files[page["id"]]
            if page["elephant"] != "slon-images/elephant.png":
                extra[f"games/{page['elephant']}"] = image_files[f"{page['id']}-ref"]
        if page.get("kind") == "solution":
            for thumb in page["thumbs"]:
                extra[f"games/{thumb['image']}"] = image_files[thumb["id"]]
    compile_template("games/najdi_slona.typ", data, reading, theme=theme, extra_files=extra)
    impose_booklet(
        reading,
        imposed,
        theme=theme,
        fold_guide=False,
        sheet_width_mm=spec["sheet_width_mm"],
        sheet_height_mm=spec["sheet_height_mm"],
    )
    return {"reading": reading, "print": imposed}
