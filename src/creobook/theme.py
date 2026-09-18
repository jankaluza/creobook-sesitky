"""Theme and path helpers for CreoBook templates."""

from __future__ import annotations

import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def project_root() -> Path:
    """Return the project root that contains config/, templates/, assets/."""
    pkg = Path(__file__).resolve().parent
    # Wheel install with force-included assets under the package dir
    if (pkg / "config" / "theme.toml").exists():
        return pkg
    # Editable / src layout: <root>/src/creobook/*.py
    src_root = pkg.parents[2]
    if (src_root / "config" / "theme.toml").exists():
        return src_root
    cwd = Path.cwd()
    if (cwd / "config" / "theme.toml").exists():
        return cwd
    raise FileNotFoundError(
        "Could not locate CreoBook project root (config/theme.toml missing)"
    )


class PageTheme(BaseModel):
    width_mm: float = 148.0
    height_mm: float = 210.0


class MarginsTheme(BaseModel):
    inner_mm: float = 13.0
    outer_mm: float = 9.0
    top_mm: float = 11.0
    bottom_mm: float = 11.0


class ColorsTheme(BaseModel):
    ink: str = "#000000"
    muted: str = "#1a1a1a"
    light: str = "#333333"
    rule: str = "#000000"
    accent: str = "#000000"
    weekend: str = "#000000"
    holiday: str = "#000000"
    adjacent: str = "#444444"
    background: str = "#ffffff"
    fold_guide: str = "#666666"
    header: str = "#000000"
    holiday_bg: str = "#ffffff"
    weekend_bg: str = "#ffffff"


class FontsTheme(BaseModel):
    family: str = "Inter"
    directory: str = "assets/fonts"


class LinesTheme(BaseModel):
    rule_width_mm: float = 0.35
    grid_width_mm: float = 0.35
    dot_diameter_mm: float = 0.65
    margin_line_width_mm: float = 0.45
    fold_guide_width_mm: float = 0.35
    checkbox_size_mm: float = 3.5
    checkbox_stroke_mm: float = 0.40


class DefaultsTheme(BaseModel):
    ruled_spacing_mm: float = 7.0
    dotted_spacing_mm: float = 5.0
    grid_spacing_mm: float = 5.0
    checklist_rows: int = 16
    header_height_mm: float = 6.0
    footer_height_mm: float = 5.0
    margin_line_from_inner_mm: float = 28.0
    cornell_cue_width_mm: float = 48.0
    cornell_summary_height_mm: float = 28.0


class BookletTheme(BaseModel):
    sheet_width_mm: float = 297.0
    sheet_height_mm: float = 210.0
    fold_guide: bool = True


class BrandTheme(BaseModel):
    name: str = "CreoBook"
    tagline: str = "notebook inserts"


class Theme(BaseModel):
    page: PageTheme = Field(default_factory=PageTheme)
    margins: MarginsTheme = Field(default_factory=MarginsTheme)
    colors: ColorsTheme = Field(default_factory=ColorsTheme)
    fonts: FontsTheme = Field(default_factory=FontsTheme)
    lines: LinesTheme = Field(default_factory=LinesTheme)
    defaults: DefaultsTheme = Field(default_factory=DefaultsTheme)
    booklet: BookletTheme = Field(default_factory=BookletTheme)
    brand: BrandTheme = Field(default_factory=BrandTheme)

    def with_accent(self, accent: str | None) -> Theme:
        if not accent:
            return self
        data = self.model_dump()
        data["colors"]["accent"] = accent
        return Theme.model_validate(data)

    def to_typst_dict(self) -> dict[str, Any]:
        """Serialize theme for Typst JSON consumption (all lengths in mm)."""
        return self.model_dump()

    def font_paths(self) -> list[Path]:
        root = project_root()
        return [root / self.fonts.directory]


@lru_cache(maxsize=4)
def load_theme(path: str | None = None) -> Theme:
    theme_path = Path(path) if path else project_root() / "config" / "theme.toml"
    with theme_path.open("rb") as fh:
        raw = tomllib.load(fh)
    return Theme.model_validate(raw)


def templates_dir() -> Path:
    return project_root() / "templates"


def config_dir() -> Path:
    return project_root() / "config"


def default_pages_dir() -> Path:
    return project_root() / "output" / "pages"


def default_booklet_dir() -> Path:
    return project_root() / "output" / "booklet"
