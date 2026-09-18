"""Puzzle-level validation helpers for games."""

from __future__ import annotations

from creobook.games.models import PuzzleBase
from creobook.games.sudoku import count_solutions


def validate_puzzle(puzzle: PuzzleBase) -> None:
    if puzzle.kind == "sudoku":
        puzzles = puzzle.data.get("puzzles") or [{"grid": puzzle.data["grid"]}]
        answers = puzzle.answer.get("puzzles") or [{"grid": puzzle.answer["grid"]}]
        if len(puzzles) != len(answers):
            raise ValueError("Sudoku puzzle/answer count mismatch")
        for puz, ans in zip(puzzles, answers, strict=True):
            if count_solutions(puz["grid"], limit=2) != 1:
                raise ValueError("Sudoku uniqueness failed")
            if ans.get("grid") is None:
                raise ValueError("Sudoku missing solution")
    elif puzzle.kind == "maze":
        path = puzzle.answer.get("path") or []
        if len(path) < 2:
            raise ValueError("Maze solution path too short")
        start = puzzle.data["start"]
        goal = puzzle.data["goal"]
        if path[0] != start or path[-1] != goal:
            raise ValueError("Maze path must run START→CÍL")
    elif puzzle.kind == "word_search":
        placements = puzzle.answer.get("placements") or []
        words = puzzle.data["words"]
        found = {p["word"] for p in placements}
        if set(words) != found:
            raise ValueError("Word-search placements incomplete")
    elif puzzle.kind == "nonogram":
        from creobook.games.nonogram import verify_clues

        verify_clues(
            puzzle.answer["grid"],
            puzzle.data["row_clues"],
            puzzle.data["col_clues"],
        )
    elif puzzle.kind == "connect_dots":
        pts = puzzle.data["points"]
        nums = [p["n"] for p in pts]
        if nums != list(range(1, len(pts) + 1)):
            raise ValueError("Connect-the-dots numbering broken")
    elif puzzle.kind == "spot_difference":
        n = puzzle.data["difference_count"]
        if len(puzzle.answer.get("changes") or []) != n:
            raise ValueError("Spot-the-difference count mismatch")
    elif puzzle.kind == "cipher":
        if not puzzle.answer.get("plaintext"):
            raise ValueError("Cipher missing plaintext")
