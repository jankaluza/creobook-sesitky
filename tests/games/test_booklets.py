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
from creobook.compiler import compile_template
from creobook.games.models import BookletBuildOptions, Difficulty, PackConfig, PageSpec
from creobook.imposition import booklet_spreads, pad_page_count
from creobook.theme import load_theme
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_content_within_media_box,
    check_page_count,
    extract_page_text,
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


def test_medium_solutions_stay_on_one_page(tmp_path, theme):
    def grid(n: int) -> list[list[int]]:
        return [[(r + c) % n + 1 for c in range(n)] for r in range(n)]

    items = [
        {
            "page": 8,
            "sub": i + 1,
            "title": f"Sudoku 6×6 · {i + 1}",
            "kind": "sudoku",
            "answer": {"grid": grid(6)},
            "data": {"size": 6, "grid": grid(6), "box": [2, 3]},
        }
        for i in range(12)
    ]
    pdf = tmp_path / "solutions-6.pdf"
    compile_template(
        "games/booklet.typ",
        {
            "page_type": "games_booklet",
            "pages": [
                {
                    "kind": "solutions",
                    "title": "Řešení 6×6 (str. 8–10)",
                    "instructions": "Kompaktní řešení vybraných stran.",
                    "difficulty": "medium",
                    "data": {"items": items},
                    "answer": {},
                }
            ],
            "theme": theme.to_typst_dict(),
            "title": "Sudoku",
        },
        pdf,
        theme=theme,
    )
    assert check_page_count(pdf, 1).ok


def test_short_sudoku_booklet_fills_empty_pages_with_puzzles():
    pack = PackConfig(
        id="sudoku",
        title="CreoBook Sudoku",
        sheets=1,
        pages=[
            PageSpec(kind="cover", title="CreoBook Sudoku"),
            PageSpec(kind="sudoku", title="Sudoku 4×4 · snadné", difficulty=Difficulty.easy, params={"size": 4, "fill": True}),
            PageSpec(kind="back", title="CreoBook"),
        ],
    )
    pages = build_booklet_pages(pack, sheets=1, seed=1)
    assert [page["kind"] for page in pages] == ["cover", "sudoku", "sudoku", "back"]
    assert pages[2]["data"]["size"] == 4
    assert pages[2]["data"]["count"] == 6
    assert "free_grid" not in {page["kind"] for page in pages}


def test_cover_stores_the_same_number_as_the_product_name():
    pack = PackConfig(
        id="sudoku",
        title="CreoBook Sudoku",
        pages=[PageSpec(kind="cover", title="CreoBook Sudoku")],
        sheets=1,
    )
    pages = build_booklet_pages(pack, sheets=1, seed=1, edition_label="č. 2")
    assert pages[0]["kind"] == "cover"
    assert pages[0]["data"]["edition_label"] == "č. 2"


def test_covers_print_the_product_number(tmp_path, theme):
    pages = [
        {
            "kind": kind,
            "title": title,
            "instructions": "Podtitul",
            "difficulty": "easy",
            "data": {"edition_label": label, "pack_subtitle": "Podtitul", "legend": []},
            "answer": {},
        }
        for kind, title, label in (
            ("cover", "CreoBook Sudoku", "č. 2"),
            ("ws_cover", "OSMISMĚRKY", "č. 3"),
            ("maze_cover", "BLUDIŠTĚ", "č. 4"),
        )
    ]
    pdf = tmp_path / "covers.pdf"
    compile_template(
        "games/booklet.typ",
        {
            "page_type": "games_booklet",
            "pages": pages,
            "theme": theme.to_typst_dict(),
            "title": "Sešitky",
        },
        pdf,
        theme=theme,
    )
    texts = extract_page_text(pdf)
    for text, label in zip(texts, ("č. 2", "č. 3", "č. 4"), strict=True):
        assert label in text


def test_hard_sudoku_page_holds_two_puzzles(tmp_path):
    one = tmp_path / "hard9.pdf"
    compile_single_game(
        "sudoku",
        one,
        seed=20260917,
        difficulty=Difficulty.hard,
        params={"size": 9, "fill": True},
    )
    assert check_page_count(one, 1).ok
    assert check_a5_pages(one).ok
    text = extract_page_text(one)[0]
    assert "š.1" in text
    assert "š.2" in text


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
