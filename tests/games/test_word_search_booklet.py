"""Tests for Czech word-search vocabulary, generator, and booklet."""

from __future__ import annotations

from pathlib import Path

import pytest

from creobook.games.base import make_rng
from creobook.games.models import Difficulty
from creobook.games.validation import validate_puzzle
from creobook.games.vocab import (
    LENGTH_BOUNDS,
    THEME_TITLES_CS,
    count_pools,
    load_vocabulary,
    normalize_czech,
    pool_for,
    validate_vocabulary,
)
from creobook.games.word_search import (
    DIFFICULTY_SPEC,
    DIRS,
    GenerationStats,
    generate_puzzle,
    select_themed_words,
    words_are_path_compatible,
)
from creobook.games.word_search_booklet import (
    EXPECTED_SPREADS,
    build_word_search_booklet_pages,
    compile_word_search_booklet,
    edition_date_from_seed,
    format_edition_date_cs,
)
from creobook.imposition import booklet_spreads
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_content_within_media_box,
    check_page_count,
    extract_page_text,
)


def test_vocabulary_structure_and_pools():
    vocab = load_vocabulary()
    validate_vocabulary(vocab)
    pools = count_pools(vocab)
    assert pools["easy"] >= 250
    assert pools["medium"] >= 350
    assert pools["hard"] >= 350
    norms = set()
    for entry in vocab.nouns:
        assert entry.pos == "noun"
        assert entry.word
        assert entry.child_safe
        assert entry.normalized == normalize_czech(entry.word)
        assert entry.normalized.isupper()
        assert entry.normalized.isalpha()
        assert " " not in entry.word
        assert entry.category in THEME_TITLES_CS
        assert entry.normalized not in norms
        norms.add(entry.normalized)
        for level in entry.difficulty:
            lo, hi = LENGTH_BOUNDS[level]
            assert lo <= len(entry.normalized) <= hi


@pytest.mark.parametrize(
    "word,expected",
    [
        ("židle", "ZIDLE"),
        ("kůň", "KUN"),
        ("řeřicha", "RERICHA"),
        ("nádraží", "NADRAZI"),
        ("chléb", "CHLEB"),
    ],
)
def test_normalization_examples(word, expected):
    assert normalize_czech(word) == expected


def test_easy_has_no_diagonal_or_backwards():
    rng = make_rng(99)
    theme, words = select_themed_words(
        difficulty=Difficulty.easy, count=8, used=set(), rng=rng
    )
    puzzle = generate_puzzle(
        seed=99, difficulty=Difficulty.easy, theme=theme, words=words
    )
    validate_puzzle(puzzle)
    assert puzzle.data["size"] == 10
    assert len(puzzle.data["words"]) == 8
    dirs = {p["direction"] for p in puzzle.answer["placements"]}
    assert dirs <= {"E", "S"}


def test_medium_and_hard_dimensions():
    for diff, size, count in (
        (Difficulty.medium, 13, 12),
        (Difficulty.hard, 16, 16),
    ):
        rng = make_rng(100 + size)
        theme, words = select_themed_words(
            difficulty=diff, count=count, used=set(), rng=rng
        )
        puzzle = generate_puzzle(seed=100 + size, difficulty=diff, theme=theme, words=words)
        validate_puzzle(puzzle)
        assert puzzle.data["size"] == size
        assert len(puzzle.data["words"]) == count
        for p in puzzle.answer["placements"]:
            assert p["direction"] in DIRS
            assert 0 <= p["row"] < size
            assert 0 <= p["col"] < size


def test_reproducible_and_different_seeds():
    def one(seed: int):
        rng = make_rng(seed)
        theme, words = select_themed_words(
            difficulty=Difficulty.easy, count=8, used=set(), rng=rng
        )
        return generate_puzzle(
            seed=seed, difficulty=Difficulty.easy, theme=theme, words=words
        )

    a = one(20270101)
    b = one(20270101)
    c = one(20270102)
    assert a.data["grid"] == b.data["grid"]
    assert a.data["words"] == b.data["words"]
    assert a.data["grid"] != c.data["grid"] or a.data["words"] != c.data["words"]


def test_no_word_reuse_in_booklet():
    pages, meta = build_word_search_booklet_pages(seed=20270101)
    puzzles = [p for p in pages if p["kind"] == "word_search"]
    assert len(puzzles) == 18
    used: set[str] = set()
    for p in puzzles:
        for n in p["data"]["words_normalized"]:
            assert n not in used
            used.add(n)
    assert meta["used_word_count"] == len(used)


def test_edition_date_formatting():
    from datetime import date

    assert format_edition_date_cs(date(2027, 1, 1)) == "01. 01. 2027"
    assert edition_date_from_seed(20270101) == date(2027, 1, 1)
    assert edition_date_from_seed(42, today=date(2026, 9, 18)) == date(2026, 9, 18)


def test_booklet_page_structure_and_difficulties():
    pages, meta = build_word_search_booklet_pages(seed=20270101, edition_label="č. 2")
    assert len(pages) == 24
    assert pages[0]["kind"] == "ws_cover"
    assert pages[0]["data"]["edition_date"] == "01. 01. 2027"
    assert pages[0]["data"]["edition_label"] == "č. 2"
    assert meta["edition_date"] == "01. 01. 2027"
    puzzles = [p for p in pages if p["kind"] == "word_search"]
    assert sum(1 for p in puzzles if p["difficulty"] == "easy") == 6
    assert sum(1 for p in puzzles if p["difficulty"] == "medium") == 6
    assert sum(1 for p in puzzles if p["difficulty"] == "hard") == 6
    sols = [p for p in pages if p["kind"] == "ws_solutions"]
    assert len(sols) == 5
    assert all(p["data"]["items"] for p in sols)
    assert booklet_spreads(24) == EXPECTED_SPREADS


def test_compatible_word_sets():
    from creobook.games.vocab import NounEntry

    a = NounEntry(
        word="most",
        normalized="MOST",
        category="city",
        difficulty=["easy"],
    )
    b = NounEntry(
        word="mostek",
        normalized="MOSTEK",
        category="city",
        difficulty=["easy", "medium"],
    )
    assert not words_are_path_compatible([a, b])


def test_pdf_booklet_and_solutions(tmp_path):
    pages_pdf = tmp_path / "ws-a5.pdf"
    booklet_pdf = tmp_path / "ws-a4.pdf"
    json_path = tmp_path / "ws.json"
    result = compile_word_search_booklet(
        seed=20270101,
        pages_output=pages_pdf,
        output=booklet_pdf,
        json_output=json_path,
    )
    assert result["pages"] == pages_pdf
    assert check_page_count(pages_pdf, 24).ok
    assert check_a5_pages(pages_pdf).ok
    assert check_content_within_media_box(pages_pdf).ok
    assert check_page_count(booklet_pdf, 12).ok
    assert check_a4_landscape_sheets(booklet_pdf).ok
    assert json_path.exists()

    texts = extract_page_text(pages_pdf)
    assert "OSMISMĚRKY" in texts[0]
    assert "Vydání: 01. 01. 2027" in texts[0]
    assert "Jméno" not in texts[0]
    # Cover + 18 puzzles + 5 solutions
    assert any("LEHKÁ" in t or "●○○" in t for t in texts[1:7])
    # Czech diacritics survive in word lists on some puzzle page
    assert any(any(ch in t for ch in "ěščřžýáíéúů") for t in texts[1:19])


def test_generation_terminates(stats_bound=True):
    stats = GenerationStats()
    rng = make_rng(7)
    theme, words = select_themed_words(
        difficulty=Difficulty.hard, count=16, used=set(), rng=rng
    )
    generate_puzzle(
        seed=7, difficulty=Difficulty.hard, theme=theme, words=words, stats=stats
    )
    assert stats.restarts < 60
    assert stats.backtrack_nodes <= 40_000
