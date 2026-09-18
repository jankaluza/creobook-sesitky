"""PDF / booklet integration tests for game packs."""

from __future__ import annotations

from pathlib import Path

import pytest

from creobook.games.booklet import (
    build_booklet_pages,
    compile_games_booklet,
    compile_single_game,
    load_pack,
)
from creobook.games.models import BookletBuildOptions, Difficulty
from creobook.imposition import booklet_spreads, pad_page_count
from creobook.theme import load_theme
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_content_within_media_box,
    check_page_count,
)


@pytest.fixture(scope="module")
def theme():
    return load_theme()


def test_pack_page_count_multiple_of_four():
    for pack_id, sheets, expected in (
        ("hlavolamy", 4, 16),
        ("pro-dva", 4, 16),
        ("sudoku", 6, 24),
    ):
        pack = load_pack(pack_id)
        assert len(pack.pages) == expected
        assert pack.sheets == sheets
        # Avoid regenerating the full sudoku pack (many 9×9) in this smoke test
        if pack_id == "sudoku":
            continue
        pages = build_booklet_pages(pack, sheets=sheets, seed=20260917)
        assert len(pages) == expected
        assert pad_page_count(len(pages)) == expected


@pytest.mark.parametrize("sheets", [4, 5, 6])
def test_imposition_sheet_counts(sheets):
    logical = sheets * 4
    spreads = booklet_spreads(logical)
    assert len(spreads) == sheets * 2  # front+back per sheet
    assert pad_page_count(logical) == logical


def test_hlavolamy_pdf(tmp_path, theme):
    pages = tmp_path / "hlav-pages.pdf"
    book = tmp_path / "hlav-booklet.pdf"
    opts = BookletBuildOptions(pack_id="hlavolamy", seed=20260917, sheets=4)
    compile_games_booklet(opts, pages, theme=theme, impose=True, booklet_output=book)
    assert check_page_count(pages, 16).ok
    assert check_a5_pages(pages).ok
    assert check_content_within_media_box(pages).ok
    assert check_page_count(book, 8).ok
    assert check_a4_landscape_sheets(book).ok


def test_sudoku_pack_pdf(tmp_path, theme):
    pack = load_pack("sudoku")
    assert pack.sheets == 6
    assert len(pack.pages) == 24  # exact 6-sheet capacity (no free-page pad)
    sudoku_specs = [p for p in pack.pages if p.kind == "sudoku"]
    assert len(sudoku_specs) == 15
    assert all(p.params.get("fill") for p in sudoku_specs)
    assert any(p.kind == "bonus" for p in pack.pages)

    from creobook.games.sudoku import puzzles_per_page

    expected_puzzles = sum(
        puzzles_per_page(int(p.params["size"])) for p in sudoku_specs
    )
    # 4×6 + 5×4 + 6×2 = 56
    assert expected_puzzles == 56

    # Smoke-compile one filled easy page (keeps CI fast)
    from creobook.games.booklet import compile_single_game

    one = tmp_path / "filled4.pdf"
    compile_single_game(
        "sudoku",
        one,
        seed=20260917,
        difficulty=Difficulty.easy,
        params={"size": 4, "fill": True},
    )
    assert check_a5_pages(one).ok
    assert check_page_count(one, 1).ok


def test_single_game_pages(tmp_path, theme):
    for kind in ("sudoku", "maze", "word_search"):
        out = tmp_path / f"{kind}.pdf"
        params = {"theme": "zvířata"} if kind == "word_search" else None
        compile_single_game(
            kind,
            out,
            seed=42,
            difficulty=Difficulty.easy,
            params=params,
        )
        assert check_a5_pages(out).ok
        assert check_page_count(out, 1).ok


def test_font_is_inter(theme):
    assert theme.fonts.family == "Inter"


def test_cover_text_present(tmp_path, theme):
    pages = tmp_path / "hlav-pages.pdf"
    opts = BookletBuildOptions(pack_id="hlavolamy", seed=20260917, sheets=4)
    compile_games_booklet(opts, pages, theme=theme, impose=False)
    from creobook.validation import extract_page_text

    text0 = extract_page_text(pages)[0]
    assert "Hlavolamy" in text0 or "CreoBook" in text0


def test_deterministic_booklet_data():
    pack = load_pack("hlavolamy")
    a = build_booklet_pages(pack, seed=123, sheets=4)
    b = build_booklet_pages(pack, seed=123, sheets=4)
    assert a == b
