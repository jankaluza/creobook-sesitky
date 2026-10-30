"""Tests for Czech crossword generation and KŘÍŽOVKY booklet PDFs."""

from __future__ import annotations

import unicodedata

import pytest

from creobook.games.crossword import (
    DIFFICULTY_SPEC,
    generate_crossword,
    validate_crossword_structure,
)
from creobook.games.crossword_booklet import (
    PUZZLE_COUNT,
    SOLUTION_BANDS,
    build_crossword_booklet_pages,
    compile_crossword_booklet,
)
from creobook.games.word_search_booklet import EXPECTED_SPREADS
from creobook.games.crossword_data import (
    THEME_TITLES_CS,
    answer_cells,
    load_crossword_dataset,
    tajenka_key,
    tajenka_letters,
)
from creobook.games.models import Difficulty
from creobook.games.validation import validate_puzzle
from creobook.imposition import booklet_spreads
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_content_within_media_box,
    check_page_count,
    extract_page_text,
)


def test_dataset_loads_and_covers_letters():
    ds = load_crossword_dataset()
    assert len(ds.clues) >= 200
    assert len(ds.tajenky) >= 20
    letters = {ch for c in ds.clues for ch in c.cells}
    needed = {ch for t in ds.tajenky for ch in t.letters}
    assert needed <= letters


def test_ch_is_two_cells():
    assert answer_cells("CHLÉB") == ["C", "H", "L", "É", "B"]
    assert tajenka_letters("ZLATÝ KLÍČ") == list("ZLATÝKLÍČ")
    assert tajenka_key("ZLATÝ KLÍČ") == "ZLATÝKLÍČ"


@pytest.mark.parametrize("difficulty", [Difficulty.easy, Difficulty.medium, Difficulty.hard])
def test_single_crossword_valid(difficulty):
    puzzle = generate_crossword(
        seed=20270101 + ord(difficulty.value[0]),
        difficulty=difficulty,
        puzzle_number=1,
    )
    validate_puzzle(puzzle)
    assert puzzle.kind == "crossword"
    cols = puzzle.data["cols"]
    assert cols <= DIFFICULTY_SPEC[difficulty]["max_cols"]
    assert unicodedata.is_normalized("NFC", puzzle.data["tajenka_phrase"])
    for ans in puzzle.answer["answers"]:
        assert ans == unicodedata.normalize("NFC", ans)
        assert ans == ans.upper()


def test_crossword_deterministic():
    a = generate_crossword(seed=42, difficulty=Difficulty.easy, puzzle_number=1)
    b = generate_crossword(seed=42, difficulty=Difficulty.easy, puzzle_number=1)
    c = generate_crossword(seed=43, difficulty=Difficulty.easy, puzzle_number=1)
    assert a.answer["grid"] == b.answer["grid"]
    assert a.answer["tajenka"] == b.answer["tajenka"]
    assert a.answer["grid"] != c.answer["grid"] or a.answer["tajenka"] != c.answer["tajenka"]


def test_booklet_structure_mixed():
    pages, meta = build_crossword_booklet_pages(seed=20270101, difficulty="mixed")
    assert len(pages) == 24
    assert pages[0]["kind"] == "cw_cover"
    assert pages[0]["title"] == "CreoBook – Křížovky"
    assert pages[0]["data"]["edition_date"] == "01. 01. 2027"
    puzzles = [p for p in pages if p["kind"] == "crossword"]
    assert len(puzzles) == PUZZLE_COUNT
    assert sum(1 for p in puzzles if p["difficulty"] == "easy") == 7
    assert sum(1 for p in puzzles if p["difficulty"] == "medium") == 7
    assert sum(1 for p in puzzles if p["difficulty"] == "hard") == 6
    sols = [p for p in pages if p["kind"] == "cw_solutions"]
    assert len(sols) == 3
    assert SOLUTION_BANDS == [(1, 7), (8, 14), (15, 20)]
    assert booklet_spreads(24) == EXPECTED_SPREADS

    tajenky = [p["answer"]["tajenka"] for p in puzzles]
    assert len(set(tajenka_key(t) for t in tajenky)) == PUZZLE_COUNT
    all_answers = [a for p in puzzles for a in p["answer"]["answers"]]
    assert len(all_answers) == len(set(all_answers))

    for p in puzzles:
        validate_crossword_structure(
            solution=p["answer"]["grid"],
            blank=p["data"]["grid"],
            rows=p["data"]["row_meta"],
            tajenka_col=p["data"]["tajenka_col"],
            tajenka_letters=p["data"]["tajenka_letters"],
            tajenka_phrase=p["data"]["tajenka_phrase"],
        )


@pytest.mark.parametrize("theme", sorted(THEME_TITLES_CS))
def test_booklet_themes(theme):
    pages, _meta = build_crossword_booklet_pages(
        seed=20261006, difficulty="mixed", theme=theme
    )
    assert len(pages) == 24


def test_crossword_booklet_pdf(tmp_path):
    pages_pdf = tmp_path / "cw-a5.pdf"
    booklet_pdf = tmp_path / "cw-a4.pdf"
    json_path = tmp_path / "cw.json"
    compile_crossword_booklet(
        seed=20270101,
        difficulty="mixed",
        pages_output=pages_pdf,
        output=booklet_pdf,
        json_output=json_path,
    )
    assert check_page_count(pages_pdf, 24).ok
    assert check_a5_pages(pages_pdf).ok
    assert check_content_within_media_box(pages_pdf).ok
    assert check_page_count(booklet_pdf, 12).ok
    assert check_a4_landscape_sheets(booklet_pdf).ok
    assert json_path.exists()

    texts = extract_page_text(pages_pdf)
    cover = texts[0]
    assert "Křížovky" in cover or "KŘÍŽOVKY" in cover.upper()
    assert "CreoBook" in cover
    assert "Vydání: 01. 01. 2027" in cover
    assert "CH" in cover

    puzzle_text = texts[1]
    assert "Křížovka" in puzzle_text or "Nápovědy" in puzzle_text

    # Diacritics survive in exported text layer
    joined = "\n".join(texts)
    assert any(ch in joined for ch in "ÁÉĚÍÓÚŮÝČĎŇŘŠŤŽáéěíóúůýčďňřšťž")

    sol_text = texts[21]
    assert "Řešení" in sol_text or "Tajenka" in sol_text
