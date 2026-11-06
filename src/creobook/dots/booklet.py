"""A5/A6 connect-the-dots pages and booklet imposition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from creobook.coloring.models import PAGE_FORMATS
from creobook.compiler import compile_template
from creobook.dots.geometry import PuzzleGeometry, dot_payload
from creobook.dots.models import DotsConfig, content_size
from creobook.imposition import impose_booklet
from creobook.theme import Theme, load_theme


def reading_pages(
    config: DotsConfig,
    puzzles: list[tuple[str, PuzzleGeometry]],
) -> list[dict[str, Any]]:
    """Cover and unsolved puzzles only. Solutions never share this booklet."""
    pages: list[dict[str, Any]] = [
        {
            "kind": "cover",
            "title": config.title,
            "subtitle": "Spojovačky · 6–8 let",
            "footer": "CreoBook.cz",
        }
    ]
    for index, (_name, geometry) in enumerate(puzzles, start=1):
        pages.append(_puzzle_page(index, geometry, solved=False))
    while len(pages) % 4 != 0:
        pages.append({"kind": "blank"})
    return pages


def answer_pages(puzzles: list[tuple[str, PuzzleGeometry]]) -> list[dict[str, Any]]:
    return [
        _puzzle_page(index, geometry, solved=True, name=name)
        for index, (name, geometry) in enumerate(puzzles, start=1)
    ]


def _puzzle_page(
    index: int,
    geometry: PuzzleGeometry,
    *,
    solved: bool,
    name: str = "",
) -> dict[str, Any]:
    return {
        "kind": "answer" if solved else "puzzle",
        "number": index,
        "heading": name if solved else "Co se skrývá mezi tečkami?",
        "caption": f"Řešení č. {index}" if solved else f"č. {index}",
        "font_pt": geometry.font_pt,
        "dots": [dot_payload(dot) for dot in geometry.dots],
    }


def compile_dots_pdfs(
    config: DotsConfig,
    puzzles: list[tuple[str, PuzzleGeometry]],
    output_dir: Path,
    *,
    theme: Theme | None = None,
) -> dict[str, Path]:
    theme = theme or load_theme()
    spec = PAGE_FORMATS[config.page_format]
    width, height = content_size(config.page_format)
    pages = reading_pages(config, puzzles)
    for page in pages:
        if page["kind"] in {"puzzle", "answer"}:
            page["content_width"] = width
            page["content_height"] = height
    data = {
        "page_type": "dots_booklet",
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
    slug = Path(config.output_directory).name or "spojovacky"
    reading = output_dir / f"{slug}-{config.page_format.lower()}.pdf"
    imposed = output_dir / f"{slug}-tisk.pdf"
    _compile(data, reading, theme)
    impose_booklet(
        reading,
        imposed,
        theme=theme,
        fold_guide=False,
        sheet_width_mm=spec["sheet_width_mm"],
        sheet_height_mm=spec["sheet_height_mm"],
    )
    paths = {"reading": reading, "print": imposed}
    if config.include_answers:
        answers = answer_pages(puzzles)
        for page in answers:
            page["content_width"] = width
            page["content_height"] = height
        solution_data = dict(data)
        solution_data["pages"] = answers
        solutions = output_dir / f"{slug}-reseni.pdf"
        _compile(solution_data, solutions, theme)
        paths["solutions"] = solutions
    return paths


def _compile(data: dict[str, Any], output: Path, theme: Theme) -> None:
    compile_template("games/spojovacky.typ", data, output, theme=theme)
