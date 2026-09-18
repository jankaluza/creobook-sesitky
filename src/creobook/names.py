"""Czech filenames and display labels for notebook page types."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PageName:
    """ASCII slug for filenames + Czech subtitle with diacritics."""

    slug: str
    subtitle: str  # Czech label shown in the PDF header/footer


# Keys match CLI page types; use "ruled-margin" for the margin-line variant.
PAGE_NAMES: dict[str, PageName] = {
    "blank": PageName("prazdny", "Prázdný"),
    "ruled": PageName("linky", "Linky"),
    "ruled-margin": PageName("linky-odsazene", "Linky odsazené"),
    "dotted": PageName("tecky", "Tečky"),
    "grid": PageName("mrizka", "Mřížka"),
    "checklist": PageName("seznam", "Seznam"),
    "cornell": PageName("cornell", "Cornell"),
    "calendar": PageName("kalendar", "Kalendář"),
}


def page_key(page_type: str, *, margin_line: bool = False) -> str:
    if page_type == "ruled" and margin_line:
        return "ruled-margin"
    return page_type


def get_page_name(page_type: str, *, margin_line: bool = False) -> PageName:
    key = page_key(page_type, margin_line=margin_line)
    if key not in PAGE_NAMES:
        raise KeyError(f"Unknown page type for naming: {key}")
    return PAGE_NAMES[key]


def a5_filename(page_type: str, *, margin_line: bool = False) -> str:
    """Return ``creobook-$name-a5.pdf`` (ASCII slug, no diacritics)."""
    return f"creobook-{get_page_name(page_type, margin_line=margin_line).slug}-a5.pdf"


def booklet_filename(page_type: str, *, margin_line: bool = False) -> str:
    """Imposed booklet basename — A5 after folding, same as the pages file."""
    return a5_filename(page_type, margin_line=margin_line)


def booklet_filename_from_pages_path(pages_path: str | Path) -> str:
    """Map pages PDF path to booklet basename (keeps ``-a5`` suffix)."""
    return Path(pages_path).name
