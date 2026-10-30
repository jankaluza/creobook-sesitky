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
        from creobook.games.models import Difficulty
        from creobook.games.word_search import (
            DIFFICULTY_SPEC,
            DIRS,
            _unique_word_paths,
        )

        placements = puzzle.answer.get("placements") or []
        words = puzzle.data["words"]
        found = {p.get("word") for p in placements}
        if set(words) != found:
            raise ValueError("Word-search placements incomplete")
        grid = puzzle.data["grid"]
        size = int(puzzle.data["size"])
        if len(grid) != size or any(len(row) != size for row in grid):
            raise ValueError("Word-search grid size mismatch")
        dirs_used = {p["direction"] for p in placements}
        if not dirs_used <= set(DIRS):
            raise ValueError("Word-search unknown direction")
        if puzzle.difficulty == Difficulty.easy and dirs_used - {"E", "S"}:
            raise ValueError("Easy word-search used forbidden directions")
        scan_dirs = DIFFICULTY_SPEC[Difficulty(puzzle.difficulty)]["dirs"]
        for p in placements:
            dr, dc = DIRS[p["direction"]]
            word = p.get("normalized") or p["word"]
            built = "".join(
                grid[p["row"] + dr * i][p["col"] + dc * i] for i in range(p["length"])
            )
            if built != word:
                raise ValueError(f"Placement letters mismatch for {word}")
            paths = _unique_word_paths(grid, word, scan_dirs)
            intended = frozenset((cell[0], cell[1]) for cell in (p.get("cells") or []))
            if not intended:
                intended = frozenset(
                    (p["row"] + dr * i, p["col"] + dc * i) for i in range(p["length"])
                )
            if paths != {intended}:
                raise ValueError(
                    f"Accidental duplicate for {word}: {len(paths)} unique paths"
                )
            cells = p.get("cells") or []
            if cells:
                for i, (rr, cc) in enumerate(cells):
                    if not (0 <= rr < size and 0 <= cc < size):
                        raise ValueError(f"Cell out of bounds for {word}")
                    if [rr, cc] != [p["row"] + dr * i, p["col"] + dc * i]:
                        raise ValueError(f"Cell list mismatch for {word}")
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
    elif puzzle.kind == "crossword":
        from creobook.games.crossword import validate_crossword_structure

        validate_crossword_structure(
            solution=puzzle.answer["grid"],
            blank=puzzle.data["grid"],
            rows=puzzle.data["row_meta"],
            tajenka_col=int(puzzle.data["tajenka_col"]),
            tajenka_letters=list(puzzle.data["tajenka_letters"]),
            tajenka_phrase=puzzle.data["tajenka_phrase"],
        )
        if puzzle.answer.get("tajenka") != puzzle.data["tajenka_phrase"]:
            raise ValueError("Crossword tajenka answer/data mismatch")
        if puzzle.answer.get("answers") != [r["answer"] for r in puzzle.data["row_meta"]]:
            raise ValueError("Crossword answers list mismatch")
