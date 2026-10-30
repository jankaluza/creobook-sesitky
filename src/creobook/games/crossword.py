"""Czech crossword generator with highlighted tajenka column."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.crossword_data import (
    DATASET_VERSION,
    THEME_TITLES_CS,
    ClueEntry,
    CrosswordDataset,
    TajenkaEntry,
    answer_cells,
    clues_for,
    load_crossword_dataset,
    tajenka_key,
    tajenky_for,
)
from creobook.games.models import Difficulty, PuzzleBase

GENERATOR_VERSION = "1.0.0"

DIFFICULTY_LABEL_CS = {
    Difficulty.easy: "LEHKÁ",
    Difficulty.medium: "STŘEDNÍ",
    Difficulty.hard: "TĚŽKÁ",
}

DIFFICULTY_MARKER = {
    Difficulty.easy: "●○○",
    Difficulty.medium: "●●○",
    Difficulty.hard: "●●●",
}

# Usable width ~124 mm; keep cells >= 6 mm → max ~20 cols; prefer tighter.
DIFFICULTY_SPEC: dict[Difficulty, dict[str, Any]] = {
    Difficulty.easy: {
        "tajenka_letters": (5, 8),
        "word_len": (3, 8),
        "max_cols": 12,
        "min_cell_mm": 7.0,
    },
    Difficulty.medium: {
        "tajenka_letters": (7, 10),
        "word_len": (4, 10),
        "max_cols": 14,
        "min_cell_mm": 6.5,
    },
    Difficulty.hard: {
        "tajenka_letters": (9, 13),
        "word_len": (5, 12),
        "max_cols": 16,
        "min_cell_mm": 6.0,
    },
}

MAX_PUZZLE_ATTEMPTS = 120
BLOCK = "#"
EMPTY = ""


class CrosswordGenerationError(ValueError):
    """Raised when a valid puzzle cannot be built from the dataset."""


@dataclass
class RowBuild:
    clue_num: int
    clue: str
    answer: str
    cells: list[str]
    tajenka_index: int
    start_col: int


def _index_letter_pool(
    clues: list[ClueEntry],
    *,
    min_len: int,
    max_len: int,
    banned: set[str],
) -> dict[str, list[tuple[ClueEntry, int]]]:
    """Map letter → list of (clue, cell_index) candidates."""
    pool: dict[str, list[tuple[ClueEntry, int]]] = {}
    for clue in clues:
        cells = clue.cells
        if not (min_len <= len(cells) <= max_len):
            continue
        if clue.answer in banned:
            continue
        for idx, letter in enumerate(cells):
            pool.setdefault(letter, []).append((clue, idx))
    return pool


def _try_build_rows(
    tajenka: TajenkaEntry,
    pool: dict[str, list[tuple[ClueEntry, int]]],
    rng,
    *,
    max_cols: int,
) -> list[RowBuild]:
    letters = tajenka.letters
    used_answers: set[str] = set()
    # Relative placement: tajenka column fixed at 0; start_col may be negative.
    relative: list[tuple[ClueEntry, int, int]] = []  # clue, taj_idx, start_rel

    for letter in letters:
        candidates = [
            (clue, idx)
            for clue, idx in pool.get(letter, [])
            if clue.answer not in used_answers
        ]
        if not candidates:
            raise CrosswordGenerationError(
                f"No unused answer contains tajenka letter {letter!r} "
                f"for phrase {tajenka.phrase!r}"
            )
        rng.shuffle(candidates)
        placed = False
        for clue, idx in candidates:
            start_rel = -idx
            trial = relative + [(clue, idx, start_rel)]
            mins = [s for _c, _i, s in trial]
            maxs = [s + len(c.cells) - 1 for c, _i, s in trial]
            width = max(maxs) - min(mins) + 1
            if width <= max_cols:
                relative.append((clue, idx, start_rel))
                used_answers.add(clue.answer)
                placed = True
                break
        if not placed:
            raise CrosswordGenerationError(
                f"Could not place letter {letter!r} within max_cols={max_cols}"
            )

    min_col = min(start for _, _, start in relative)
    rows: list[RowBuild] = []
    for num, (clue, idx, start_rel) in enumerate(relative, start=1):
        rows.append(
            RowBuild(
                clue_num=num,
                clue=clue.clue,
                answer=clue.answer,
                cells=list(clue.cells),
                tajenka_index=idx,
                start_col=start_rel - min_col,
            )
        )
    return rows


def _build_grid(rows: list[RowBuild]) -> tuple[list[list[str]], int, list[str]]:
    cols = max(r.start_col + len(r.cells) for r in rows)
    # Balance: pad right so tajenka column is nearer center when possible.
    taj_col = rows[0].start_col + rows[0].tajenka_index
    left = taj_col
    right = cols - 1 - taj_col
    if right < left:
        pad = min(2, left - right)
        # shift content right by padding left with blocks via increasing start_col
        for r in rows:
            r.start_col += pad
        cols += pad
        taj_col += pad

    grid: list[list[str]] = [[BLOCK for _ in range(cols)] for _ in rows]
    tajenka_check: list[str] = []
    for r_i, row in enumerate(rows):
        for offset, letter in enumerate(row.cells):
            c = row.start_col + offset
            grid[r_i][c] = letter
        letter = row.cells[row.tajenka_index]
        assert row.start_col + row.tajenka_index == taj_col
        tajenka_check.append(letter)
    return grid, taj_col, tajenka_check


def _blank_grid(solution: list[list[str]]) -> list[list[str]]:
    return [
        [BLOCK if cell == BLOCK else EMPTY for cell in row] for row in solution
    ]


def validate_crossword_structure(
    *,
    solution: list[list[str]],
    blank: list[list[str]],
    rows: list[dict[str, Any]],
    tajenka_col: int,
    tajenka_letters: list[str],
    tajenka_phrase: str,
) -> None:
    if len(solution) != len(rows) or len(blank) != len(rows):
        raise ValueError("Row count mismatch")
    cols = len(solution[0]) if solution else 0
    if any(len(r) != cols for r in solution) or any(len(r) != cols for r in blank):
        raise ValueError("Ragged grid")
    if not (0 <= tajenka_col < cols):
        raise ValueError("Tajenka column out of range")

    built_taj: list[str] = []
    seen_answers: set[str] = set()
    for i, row_meta in enumerate(rows):
        num = int(row_meta["num"])
        if num != i + 1:
            raise ValueError(f"Clue numbering mismatch at row {i}")
        answer = row_meta["answer"]
        if answer in seen_answers:
            raise ValueError(f"Duplicate answer in puzzle: {answer}")
        seen_answers.add(answer)
        cells = answer_cells(answer)
        if cells != row_meta["cells"]:
            raise ValueError(f"Answer cells mismatch for {answer}")
        start = int(row_meta["start_col"])
        t_idx = int(row_meta["tajenka_index"])
        if cells[t_idx] != tajenka_letters[i]:
            raise ValueError(f"Tajenka letter mismatch on row {num}")
        for offset, letter in enumerate(cells):
            c = start + offset
            if solution[i][c] != letter:
                raise ValueError(f"Grid letter mismatch for {answer} at col {c}")
            if blank[i][c] != EMPTY:
                raise ValueError(f"Blank grid should be empty at answer cell {i},{c}")
        for c, cell in enumerate(solution[i]):
            in_word = start <= c < start + len(cells)
            if in_word and cell == BLOCK:
                raise ValueError("Block inside answer")
            if not in_word and cell != BLOCK:
                raise ValueError("Non-block outside answer")
            if not in_word and blank[i][c] != BLOCK:
                raise ValueError("Blank/block mismatch")
        built_taj.append(solution[i][tajenka_col])
        if start + t_idx != tajenka_col:
            raise ValueError("Tajenka index does not align to column")

    if built_taj != tajenka_letters:
        raise ValueError(
            f"Tajenka column spells {''.join(built_taj)!r}, "
            f"expected {''.join(tajenka_letters)!r}"
        )
    if "".join(tajenka_letters) != tajenka_key(tajenka_phrase):
        raise ValueError("Tajenka phrase/letters disagree")


def generate_crossword(
    *,
    seed: int,
    difficulty: Difficulty,
    theme: str | None = None,
    puzzle_number: int = 1,
    used_answers: set[str] | None = None,
    used_tajenky: set[str] | None = None,
    dataset: CrosswordDataset | None = None,
    title: str | None = None,
) -> PuzzleBase:
    if difficulty == Difficulty.mixed:
        raise ValueError("generate_crossword expects easy/medium/hard, not mixed")
    if theme is not None and theme not in THEME_TITLES_CS:
        raise ValueError(f"Unknown theme: {theme!r}. Known: {sorted(THEME_TITLES_CS)}")

    dataset = dataset or load_crossword_dataset()
    spec = DIFFICULTY_SPEC[difficulty]
    t_min, t_max = spec["tajenka_letters"]
    w_min, w_max = spec["word_len"]
    max_cols = int(spec["max_cols"])
    banned = set(used_answers or ())
    banned_t = set(used_tajenky or ())

    theme_key = theme or "mixed"
    # Hard puzzles may also draw medium-tagged clues for rare letters.
    clue_pool = clues_for(dataset, difficulty=difficulty.value, theme=theme_key)
    if difficulty == Difficulty.hard:
        medium_extra = clues_for(dataset, difficulty="medium", theme=theme_key)
        seen_ans = {c.answer for c in clue_pool}
        clue_pool = clue_pool + [c for c in medium_extra if c.answer not in seen_ans]
    if difficulty == Difficulty.medium:
        easy_extra = clues_for(dataset, difficulty="easy", theme=theme_key)
        seen_ans = {c.answer for c in clue_pool}
        clue_pool = clue_pool + [c for c in easy_extra if c.answer not in seen_ans]

    taj_candidates = [
        t
        for t in tajenky_for(
            dataset,
            difficulty=difficulty.value,
            theme=theme_key,
            letter_min=t_min,
            letter_max=t_max,
        )
        if t.key not in banned_t
    ]
    if not clue_pool:
        raise CrosswordGenerationError(
            f"No clues for difficulty={difficulty.value} theme={theme_key}"
        )
    if not taj_candidates:
        raise CrosswordGenerationError(
            f"No unused tajenky for difficulty={difficulty.value} theme={theme_key} "
            f"length {t_min}-{t_max}"
        )

    rng = make_rng(seed)
    last_error = "unknown"
    for attempt in range(1, MAX_PUZZLE_ATTEMPTS + 1):
        try:
            pool = _index_letter_pool(
                clue_pool, min_len=w_min, max_len=w_max, banned=banned
            )
            taj_pool = [
                t
                for t in taj_candidates
                if all(pool.get(letter) for letter in t.letters)
            ]
            if not taj_pool:
                raise CrosswordGenerationError(
                    "No remaining tajenka can be spelled with unused answers"
                )
            tajenka = rng.choice(taj_pool)
            rows = _try_build_rows(tajenka, pool, rng, max_cols=max_cols)
            solution, taj_col, taj_letters = _build_grid(rows)
            if len(solution[0]) > max_cols:
                raise CrosswordGenerationError("Grid wider than max_cols")
            blank = _blank_grid(solution)
            row_dicts = [
                {
                    "num": r.clue_num,
                    "clue": r.clue,
                    "answer": r.answer,
                    "cells": r.cells,
                    "tajenka_index": r.tajenka_index,
                    "start_col": r.start_col,
                    "length": len(r.cells),
                }
                for r in rows
            ]
            validate_crossword_structure(
                solution=solution,
                blank=blank,
                rows=row_dicts,
                tajenka_col=taj_col,
                tajenka_letters=taj_letters,
                tajenka_phrase=tajenka.phrase,
            )
            theme_title = THEME_TITLES_CS[theme_key]
            puzzle = PuzzleBase(
                kind="crossword",
                title=title or f"Křížovka {puzzle_number}",
                instructions=(
                    "Doplňte vodorovná slova podle nápověd. Zvýrazněný sloupec "
                    "tvoří tajenku shora dolů. Písmeno CH zabírá dvě políčka."
                ),
                difficulty=difficulty,
                seed=seed,
                data={
                    "puzzle_number": puzzle_number,
                    "rows": len(solution),
                    "cols": len(solution[0]),
                    "grid": blank,
                    "tajenka_col": taj_col,
                    "clues": [{"num": r["num"], "clue": r["clue"], "length": r["length"]} for r in row_dicts],
                    "row_meta": row_dicts,
                    "tajenka_phrase": tajenka.phrase,
                    "tajenka_letters": taj_letters,
                    "theme": theme_key,
                    "theme_title": theme_title,
                    "difficulty_label_cs": DIFFICULTY_LABEL_CS[difficulty],
                    "difficulty_marker": DIFFICULTY_MARKER[difficulty],
                    "min_cell_mm": spec["min_cell_mm"],
                    "ch_note": "Písmeno CH zabírá dvě políčka (C + H).",
                    "generation": {
                        "attempt": attempt,
                        "generator_version": GENERATOR_VERSION,
                        "dataset_version": DATASET_VERSION,
                    },
                },
                answer={
                    "grid": solution,
                    "tajenka": tajenka.phrase,
                    "tajenka_letters": taj_letters,
                    "answers": [r["answer"] for r in row_dicts],
                },
            )
            return puzzle
        except (CrosswordGenerationError, ValueError, AssertionError) as exc:
            last_error = str(exc)
            continue

    raise CrosswordGenerationError(
        f"Failed to generate crossword after {MAX_PUZZLE_ATTEMPTS} attempts "
        f"(seed={seed}, difficulty={difficulty.value}, theme={theme_key}): {last_error}"
    )


@register
class CrosswordGenerator(GameGenerator):
    kind = "crossword"

    def generate(
        self,
        *,
        seed: int,
        difficulty: Difficulty,
        title: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> PuzzleBase:
        params = params or {}
        theme = params.get("theme")
        puzzle_number = int(params.get("puzzle_number") or 1)
        if difficulty == Difficulty.mixed:
            # Single-page mixed → medium default
            difficulty = Difficulty.medium
        return generate_crossword(
            seed=seed,
            difficulty=difficulty,
            theme=theme,
            puzzle_number=puzzle_number,
            title=title,
        )
