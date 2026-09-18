"""Unit tests for game generators."""

from __future__ import annotations

import creobook.games  # noqa: F401
from creobook.games.base import get_generator, registered_kinds
from creobook.games.models import Difficulty
from creobook.games.nonogram import clues_for, verify_clues
from creobook.games.sudoku import count_solutions
from creobook.games.validation import validate_puzzle
from creobook.games.word_search import load_theme_words


def test_registry_has_core_games():
    kinds = set(registered_kinds())
    assert {
        "sudoku",
        "maze",
        "word_search",
        "nonogram",
        "connect_dots",
        "spot_difference",
        "cipher",
        "two_player",
    } <= kinds


def test_deterministic_sudoku():
    a = get_generator("sudoku").generate(seed=99, difficulty=Difficulty.easy)
    b = get_generator("sudoku").generate(seed=99, difficulty=Difficulty.easy)
    assert a.data == b.data
    assert a.answer == b.answer


def test_sudoku_fill_page_counts():
    from creobook.games.sudoku import puzzles_per_page

    assert puzzles_per_page(4) == 6
    assert puzzles_per_page(6) == 4
    assert puzzles_per_page(9) == 2
    filled = get_generator("sudoku").generate(
        seed=1, difficulty=Difficulty.easy, params={"size": 4, "fill": True}
    )
    assert filled.data["count"] == 6
    assert len(filled.data["puzzles"]) == 6
    single = get_generator("sudoku").generate(
        seed=1, difficulty=Difficulty.easy, params={"size": 4}
    )
    assert single.data["count"] == 1


def test_sudoku_unique_solution():
    for diff, size in [
        (Difficulty.easy, 4),
        (Difficulty.medium, 6),
        (Difficulty.hard, 9),
    ]:
        p = get_generator("sudoku").generate(
            seed=7, difficulty=diff, params={"size": size, "count": 1}
        )
        assert count_solutions(p.data["grid"], limit=2) == 1
        assert p.data["count"] == 1
        validate_puzzle(p)


def test_maze_path():
    p = get_generator("maze").generate(seed=3, difficulty=Difficulty.medium)
    path = p.answer["path"]
    assert path[0] == p.data["start"]
    assert path[-1] == p.data["goal"]
    validate_puzzle(p)


def test_word_search_themes_and_placements():
    for theme in ("zvířata", "cestování", "vesmír", "knihy", "příroda"):
        words = load_theme_words(theme)
        assert len(words) >= 5
    p = get_generator("word_search").generate(
        seed=11, difficulty=Difficulty.easy, params={"theme": "zvířata"}
    )
    validate_puzzle(p)
    assert {x["word"] for x in p.answer["placements"]} == set(p.data["words"])


def test_nonogram_clues():
    p = get_generator("nonogram").generate(seed=5, difficulty=Difficulty.easy)
    verify_clues(p.answer["grid"], p.data["row_clues"], p.data["col_clues"])
    r, c = clues_for(p.answer["grid"])
    assert r == p.data["row_clues"]


def test_connect_dots_numbering():
    p = get_generator("connect_dots").generate(seed=8, difficulty=Difficulty.medium)
    nums = [pt["n"] for pt in p.data["points"]]
    assert nums == list(range(1, len(nums) + 1))
    assert len(nums) == 40


def test_spot_difference_counts():
    for diff, n in [
        (Difficulty.easy, 5),
        (Difficulty.medium, 7),
        (Difficulty.hard, 10),
    ]:
        p = get_generator("spot_difference").generate(seed=2, difficulty=diff)
        assert p.data["difference_count"] == n
        assert len(p.answer["changes"]) == n


def test_cipher_has_plaintext():
    p = get_generator("cipher").generate(seed=1, difficulty=Difficulty.easy)
    assert p.answer["plaintext"]
    validate_puzzle(p)
