"""Compile Typst templates with structured JSON page data."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import typst

from creobook.theme import Theme, load_theme, project_root, templates_dir

# Pinned via the `typst` PyPI package (messense/typst-py), which embeds this
# Typst compiler version. Keep in sync with pyproject.toml.
PINNED_TYPST_VERSION = "0.13.2"

TEMPLATE_MAP = {
    "blank": "blank.typ",
    "ruled": "ruled.typ",
    "dotted": "dotted.typ",
    "grid": "grid.typ",
    "checklist": "checklist.typ",
    "cornell": "cornell.typ",
    "calendar": "calendar.typ",
}


def build_page_data(
    page_type: str,
    theme: Theme,
    *,
    title: str | None = None,
    spacing_mm: float | None = None,
    margin_line: bool = False,
    rows: int | None = None,
    page_count: int = 1,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    defaults = theme.defaults
    data: dict[str, Any] = {
        "page_type": page_type,
        "theme": theme.to_typst_dict(),
        "title": title or theme.brand.name,
        "page_count": page_count,
        "margin_line": margin_line,
        "spacing_mm": spacing_mm
        or {
            "ruled": defaults.ruled_spacing_mm,
            "dotted": defaults.dotted_spacing_mm,
            "grid": defaults.grid_spacing_mm,
        }.get(page_type, defaults.ruled_spacing_mm),
        "rows": rows or defaults.checklist_rows,
    }
    if extra:
        data.update(extra)
    return data


def compile_template(
    template_name: str,
    data: dict[str, Any],
    output_pdf: Path | str,
    *,
    theme: Theme | None = None,
) -> Path:
    """
    Write JSON data and compile a Typst template to PDF.

    Rendering is independent of booklet imposition.
    """
    theme = theme or load_theme()
    output_path = Path(output_pdf)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    template_file = templates_dir() / template_name
    if not template_file.exists():
        raise FileNotFoundError(f"Template not found: {template_file}")

    font_paths = [str(p) for p in theme.font_paths()]
    root = project_root()

    with tempfile.TemporaryDirectory(prefix="creobook-") as tmp:
        tmp_path = Path(tmp)
        # Copy templates so relative imports resolve, and place data.json beside them
        work_templates = tmp_path / "templates"
        shutil.copytree(templates_dir(), work_templates)
        data_path = work_templates / "data.json"
        data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        # Also expose project assets (fonts referenced relatively from theme)
        work_root = tmp_path / "root"
        work_root.mkdir()
        # Symlink assets into a root that Typst can read via absolute font_paths
        # Fonts are passed via font_paths; templates only need data.json + .typ files
        entry = work_templates / template_name
        typst.compile(
            str(entry),
            output=str(output_path),
            root=str(work_templates),
            font_paths=font_paths,
            sys_inputs={"data_path": "data.json"},
        )

    return output_path


def compile_page(
    page_type: str,
    output_pdf: Path | str,
    *,
    theme: Theme | None = None,
    accent: str | None = None,
    **kwargs: Any,
) -> Path:
    theme = (theme or load_theme()).with_accent(accent)
    if page_type not in TEMPLATE_MAP:
        raise ValueError(f"Unknown page type: {page_type}")
    data = build_page_data(page_type, theme, **kwargs)
    return compile_template(TEMPLATE_MAP[page_type], data, output_pdf, theme=theme)


def compile_calendar(
    year: int,
    output_pdf: Path | str,
    *,
    theme: Theme | None = None,
    accent: str | None = None,
    calendar_data: dict[str, Any] | None = None,
) -> Path:
    from creobook.calendar import build_calendar_data

    theme = (theme or load_theme()).with_accent(accent)
    data = calendar_data or build_calendar_data(year, theme=theme, accent=accent)
    return compile_template("calendar.typ", data, output_pdf, theme=theme)
