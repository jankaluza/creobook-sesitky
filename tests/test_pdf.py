"""End-to-end PDF generation and validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from creobook.compiler import compile_calendar, compile_page
from creobook.imposition import booklet_spreads, impose_booklet, pad_page_count
from creobook.theme import load_theme
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_calendar_months_present,
    check_content_within_media_box,
    check_page_count,
)


@pytest.fixture(scope="module")
def theme():
    return load_theme()


@pytest.fixture(scope="module")
def ruled_pdf(tmp_path_factory, theme):
    out = tmp_path_factory.mktemp("pdf") / "ruled.pdf"
    compile_page("ruled", out, theme=theme, spacing_mm=7.0, page_count=1)
    return out


@pytest.fixture(scope="module")
def calendar_2026_pdf(tmp_path_factory, theme):
    out = tmp_path_factory.mktemp("pdf") / "calendar-2026.pdf"
    compile_calendar(2026, out, theme=theme)
    return out


def test_theme_defaults(theme):
    assert theme.page.width_mm == 148.0
    assert theme.page.height_mm == 210.0
    assert theme.margins.inner_mm == 13.0
    assert theme.margins.outer_mm == 9.0
    assert theme.margins.top_mm == 11.0
    assert theme.margins.bottom_mm == 11.0


def test_ruled_a5_dimensions(ruled_pdf):
    result = check_a5_pages(ruled_pdf)
    assert result.ok, result.messages
    assert check_page_count(ruled_pdf, 1).ok
    assert check_content_within_media_box(ruled_pdf).ok


def test_calendar_twelve_a5_pages(calendar_2026_pdf):
    assert check_page_count(calendar_2026_pdf, 12).ok
    assert check_a5_pages(calendar_2026_pdf).ok
    months = check_calendar_months_present(calendar_2026_pdf, 2026)
    assert months.ok, months.messages
    assert check_content_within_media_box(calendar_2026_pdf).ok


def test_booklet_imposition_calendar(calendar_2026_pdf, tmp_path, theme):
    out = tmp_path / "calendar-booklet.pdf"
    impose_booklet(calendar_2026_pdf, out, theme=theme, fold_guide=True)
    # 12 pages → 12/4 = 3 sheets × 2 sides = 6 imposed pages
    assert check_page_count(out, 6).ok
    assert check_a4_landscape_sheets(out).ok
    assert check_content_within_media_box(out).ok


def test_booklet_pads_to_multiple_of_four(tmp_path, theme):
    src = tmp_path / "five.pdf"
    compile_page("blank", src, theme=theme, page_count=5)
    assert check_page_count(src, 5).ok
    out = tmp_path / "five-booklet.pdf"
    impose_booklet(src, out, theme=theme, fold_guide=False)
    # 5 → pad 8 → 4 sheets sides = 4 pages? Wait: n=8, sheets=2, spreads=4
    assert pad_page_count(5) == 8
    assert len(booklet_spreads(5)) == 4
    assert check_page_count(out, 4).ok
    assert check_a4_landscape_sheets(out).ok


def test_repeating_insert_booklet_numbered_pages(tmp_path, theme):
    """Twenty numbered A5 pages impose to a 5-sheet booklet (10 sides)."""
    from creobook.imposition import BOOKLET_A5_PAGES

    src = tmp_path / "linky.pdf"
    compile_page("ruled", src, theme=theme, page_count=BOOKLET_A5_PAGES, spacing_mm=7.0)
    assert check_page_count(src, BOOKLET_A5_PAGES).ok
    out = tmp_path / "linky-booklet.pdf"
    impose_booklet(src, out, theme=theme, fold_guide=False)
    assert check_page_count(out, 10).ok
    assert check_a4_landscape_sheets(out).ok


def test_single_page_booklet_pads_to_one_sheet(tmp_path, theme):
    src = tmp_path / "one.pdf"
    compile_page("ruled", src, theme=theme, page_count=1, spacing_mm=7.0)
    assert check_page_count(src, 1).ok
    out = tmp_path / "one-booklet.pdf"
    impose_booklet(src, out, theme=theme, fold_guide=False)
    assert check_page_count(out, 2).ok  # pad to 4 A5 → 1 sheet × 2 sides
    assert check_a4_landscape_sheets(out).ok


@pytest.mark.parametrize(
    "page_type,kwargs",
    [
        ("blank", {}),
        ("dotted", {"spacing_mm": 5.0}),
        ("grid", {"spacing_mm": 5.0}),
        ("checklist", {}),
        ("cornell", {}),
        ("ruled", {"margin_line": True, "spacing_mm": 7.0}),
    ],
)
def test_page_types_a5(tmp_path, theme, page_type, kwargs):
    out = tmp_path / f"{page_type}.pdf"
    compile_page(page_type, out, theme=theme, page_count=1, **kwargs)
    assert check_a5_pages(out).ok
    assert check_page_count(out, 1).ok
