"""Deterministic Czech word-search generator with accidental-duplicate checks."""

from __future__ import annotations

from typing import Any

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase
from creobook.games.vocab import (
    THEME_TITLES_CS,
    NounEntry,
    categories_with_enough,
    load_vocabulary,
    pool_for,
)

GENERATOR_VERSION = "1.0.0"

DIRS: dict[str, tuple[int, int]] = {
    "E": (0, 1),
    "W": (0, -1),
    "S": (1, 0),
    "N": (-1, 0),
    "SE": (1, 1),
    "SW": (1, -1),
    "NE": (-1, 1),
    "NW": (-1, -1),
}

DIFFICULTY_SPEC: dict[Difficulty, dict[str, Any]] = {
    Difficulty.easy: {
        "size": 10,
        "word_count": 8,
        "dirs": ["E", "S"],
        "prefer_overlap": False,
        "list_columns": 2,
    },
    Difficulty.medium: {
        "size": 13,
        "word_count": 12,
        "dirs": ["E", "W", "S", "N", "SE", "SW", "NE", "NW"],
        "prefer_overlap": "moderate",
        "list_columns": 3,
    },
    Difficulty.hard: {
        "size": 16,
        "word_count": 16,
        "dirs": ["E", "W", "S", "N", "SE", "SW", "NE", "NW"],
        "prefer_overlap": True,
        "list_columns": 3,
    },
}

# Approximate Czech letter frequencies without diacritics (relative weights).
CZECH_FREQ_NORMALIZED: dict[str, int] = {
    "A": 84,
    "B": 16,
    "C": 28,
    "D": 36,
    "E": 100,
    "F": 4,
    "G": 4,
    "H": 22,
    "I": 62,
    "J": 20,
    "K": 34,
    "L": 42,
    "M": 32,
    "N": 64,
    "O": 82,
    "P": 34,
    "R": 48,
    "S": 52,
    "T": 54,
    "U": 36,
    "V": 42,
    "Y": 24,
    "Z": 28,
}

CZECH_FREQ_DIACRITIC: dict[str, int] = {
    "A": 62,
    "Á": 18,
    "B": 16,
    "C": 18,
    "Č": 12,
    "D": 28,
    "Ď": 2,
    "E": 70,
    "É": 12,
    "Ě": 14,
    "F": 4,
    "G": 4,
    "H": 18,
    "I": 42,
    "Í": 18,
    "J": 20,
    "K": 34,
    "L": 42,
    "M": 32,
    "N": 52,
    "Ň": 4,
    "O": 70,
    "Ó": 4,
    "P": 34,
    "R": 36,
    "Ř": 14,
    "S": 40,
    "Š": 14,
    "T": 42,
    "Ť": 2,
    "U": 24,
    "Ú": 8,
    "Ů": 8,
    "V": 42,
    "Y": 16,
    "Ý": 8,
    "Z": 18,
    "Ž": 12,
}

MAX_PLACEMENT_RESTARTS = 60
MAX_BACKTRACK_NODES = 40_000
MAX_FILLER_RETRIES = 80


class GenerationStats:
    def __init__(self) -> None:
        self.restarts = 0
        self.backtrack_nodes = 0
        self.filler_retries = 0
        self.puzzles = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "restarts": self.restarts,
            "backtrack_nodes": self.backtrack_nodes,
            "filler_retries": self.filler_retries,
            "puzzles": self.puzzles,
        }


def _freq_alphabet(weights: dict[str, int], rng) -> list[str]:
    letters: list[str] = []
    for ch, w in weights.items():
        letters.extend([ch] * w)
    rng.shuffle(letters)
    return letters


def _all_placements(
    size: int, word: str, dirs: list[str]
) -> list[tuple[int, int, str, int, int]]:
    out: list[tuple[int, int, str, int, int]] = []
    length = len(word)
    for dname in dirs:
        dr, dc = DIRS[dname]
        for r in range(size):
            for c in range(size):
                er = r + dr * (length - 1)
                ec = c + dc * (length - 1)
                if 0 <= er < size and 0 <= ec < size:
                    out.append((r, c, dname, dr, dc))
    return out


def _can_place(
    grid: list[list[str | None]],
    word: str,
    r: int,
    c: int,
    dr: int,
    dc: int,
) -> tuple[bool, int]:
    overlaps = 0
    for i, ch in enumerate(word):
        rr, cc = r + dr * i, c + dc * i
        cell = grid[rr][cc]
        if cell is not None and cell != ch:
            return False, 0
        if cell == ch:
            overlaps += 1
    return True, overlaps


def _place(
    grid: list[list[str | None]], word: str, r: int, c: int, dr: int, dc: int
) -> list[tuple[int, int, str | None]]:
    undo: list[tuple[int, int, str | None]] = []
    for i, ch in enumerate(word):
        rr, cc = r + dr * i, c + dc * i
        undo.append((rr, cc, grid[rr][cc]))
        grid[rr][cc] = ch
    return undo


def _undo(grid: list[list[str | None]], undo: list[tuple[int, int, str | None]]) -> None:
    for rr, cc, prev in undo:
        grid[rr][cc] = prev


def _score_placement(
    overlaps: int,
    prefer: bool | str,
    length: int,
) -> float:
    if prefer is True:
        return float(overlaps) * 3.0 + length * 0.01
    if prefer == "moderate":
        return 1.0 if overlaps <= 2 else (0.3 if overlaps <= 4 else -1.0)
    # avoid overlap when possible
    return 2.0 if overlaps == 0 else (0.5 if overlaps == 1 else -0.5)


def _place_words_backtracking(
    words: list[NounEntry],
    size: int,
    dirs: list[str],
    rng,
    prefer_overlap: bool | str,
    stats: GenerationStats,
) -> list[dict[str, Any]] | None:
    grid: list[list[str | None]] = [[None] * size for _ in range(size)]
    ordered = sorted(words, key=lambda e: (len(e.normalized), e.normalized), reverse=True)
    if rng.random() < 0.5:
        # Alternate placement order among equal lengths
        ordered = sorted(words, key=lambda e: (-len(e.normalized), rng.random()))
    placements: list[dict[str, Any]] = []

    candidates: dict[str, list[tuple[int, int, str, int, int]]] = {}
    for entry in ordered:
        opts = _all_placements(size, entry.normalized, dirs)
        rng.shuffle(opts)
        candidates[entry.normalized] = opts

    def search(idx: int) -> bool:
        stats.backtrack_nodes += 1
        if stats.backtrack_nodes > MAX_BACKTRACK_NODES:
            return False
        if idx >= len(ordered):
            return True
        entry = ordered[idx]
        word = entry.normalized
        scored: list[tuple[float, tuple[int, int, str, int, int]]] = []
        for opt in candidates[word]:
            r, c, dname, dr, dc = opt
            ok, overlaps = _can_place(grid, word, r, c, dr, dc)
            if not ok:
                continue
            score = _score_placement(overlaps, prefer_overlap, len(word))
            score += rng.random() * 0.05
            scored.append((score, opt))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:100]
        rng.shuffle(top)
        for _, (r, c, dname, dr, dc) in top:
            undo = _place(grid, word, r, c, dr, dc)
            cells = [[r + dr * i, c + dc * i] for i in range(len(word))]
            end_r = r + dr * (len(word) - 1)
            end_c = c + dc * (len(word) - 1)
            placements.append(
                {
                    "word": entry.word,
                    "normalized": word,
                    "row": r,
                    "col": c,
                    "end_row": end_r,
                    "end_col": end_c,
                    "direction": dname,
                    "length": len(word),
                    "cells": cells,
                }
            )
            if search(idx + 1):
                return True
            placements.pop()
            _undo(grid, undo)
        return False

    if not search(0):
        return None
    return placements


def _apply_placements(
    size: int, placements: list[dict[str, Any]]
) -> list[list[str | None]]:
    grid: list[list[str | None]] = [[None] * size for _ in range(size)]
    for p in placements:
        dr, dc = DIRS[p["direction"]]
        word = p["normalized"]
        for i, ch in enumerate(word):
            grid[p["row"] + dr * i][p["col"] + dc * i] = ch
    return grid


def _scan_word_occurrences(
    grid: list[list[str]],
    word: str,
    dirs: list[str],
) -> list[tuple[int, int, str]]:
    size = len(grid)
    found: list[tuple[int, int, str]] = []
    length = len(word)
    for dname in dirs:
        dr, dc = DIRS[dname]
        for r in range(size):
            for c in range(size):
                er = r + dr * (length - 1)
                ec = c + dc * (length - 1)
                if not (0 <= er < size and 0 <= ec < size):
                    continue
                match = True
                for i, ch in enumerate(word):
                    if grid[r + dr * i][c + dc * i] != ch:
                        match = False
                        break
                if match:
                    found.append((r, c, dname))
    return found


def _occurrence_cells(
    r: int, c: int, dname: str, length: int
) -> frozenset[tuple[int, int]]:
    dr, dc = DIRS[dname]
    return frozenset((r + dr * i, c + dc * i) for i in range(length))


def _unique_word_paths(
    grid: list[list[str]],
    word: str,
    dirs: list[str],
) -> set[frozenset[tuple[int, int]]]:
    paths: set[frozenset[tuple[int, int]]] = set()
    for r, c, dname in _scan_word_occurrences(grid, word, dirs):
        paths.add(_occurrence_cells(r, c, dname, len(word)))
    return paths


def _fill_and_validate(
    partial: list[list[str | None]],
    placements: list[dict[str, Any]],
    dirs: list[str],
    rng,
    *,
    grid_diacritics: bool,
    stats: GenerationStats,
) -> list[list[str]] | None:
    size = len(partial)
    weights = CZECH_FREQ_DIACRITIC if grid_diacritics else CZECH_FREQ_NORMALIZED
    intended_paths = {
        p["normalized"]: frozenset((cell[0], cell[1]) for cell in p["cells"])
        for p in placements
    }
    locked = set()
    for cells in intended_paths.values():
        locked |= cells

    alphabet = _freq_alphabet(weights, rng)
    grid: list[list[str]] = [[""] * size for _ in range(size)]
    for r in range(size):
        for c in range(size):
            if partial[r][c] is not None:
                grid[r][c] = partial[r][c]  # type: ignore[assignment]
            else:
                grid[r][c] = rng.choice(alphabet)

    for attempt in range(MAX_FILLER_RETRIES):
        if attempt:
            stats.filler_retries += 1
        ok = True
        conflict_cells: set[tuple[int, int]] = set()
        for word, intended in intended_paths.items():
            paths = _unique_word_paths(grid, word, dirs)
            if paths != {intended}:
                ok = False
                for path in paths:
                    if path != intended:
                        conflict_cells |= {cell for cell in path if cell not in locked}
        if ok:
            return grid
        if not conflict_cells:
            # Duplicate path lies entirely on locked answer cells — need new placement
            return None
        for r, c in conflict_cells:
            for _ in range(20):
                ch = rng.choice(alphabet)
                bad = False
                if c >= 3 and all(grid[r][c - i] == ch for i in range(1, 4)):
                    bad = True
                if r >= 3 and all(grid[r - i][c] == ch for i in range(1, 4)):
                    bad = True
                if not bad:
                    grid[r][c] = ch
                    break
            else:
                grid[r][c] = rng.choice(alphabet)
    return None


def generate_puzzle(
    *,
    seed: int,
    difficulty: Difficulty,
    theme: str,
    words: list[NounEntry],
    grid_diacritics: bool = False,
    stats: GenerationStats | None = None,
) -> PuzzleBase:
    if difficulty not in DIFFICULTY_SPEC:
        raise ValueError(f"unsupported difficulty: {difficulty}")
    spec = DIFFICULTY_SPEC[difficulty]
    size = int(spec["size"])
    dirs: list[str] = list(spec["dirs"])
    prefer = spec["prefer_overlap"]
    stats = stats or GenerationStats()
    base_rng = make_rng(seed)

    last_error = "unknown"
    for restart in range(MAX_PLACEMENT_RESTARTS):
        stats.restarts += 1 if restart else 0
        rng = make_rng(seed + restart * 9973 + 17)
        placements = _place_words_backtracking(
            words, size, dirs, rng, prefer, stats
        )
        if placements is None:
            last_error = "placement backtracking failed"
            continue
        partial = _apply_placements(size, placements)
        grid = _fill_and_validate(
            partial,
            placements,
            dirs,
            rng,
            grid_diacritics=grid_diacritics,
            stats=stats,
        )
        if grid is None:
            last_error = "filler accidental duplicates"
            continue
        stats.puzzles += 1
        title = THEME_TITLES_CS.get(theme, theme)
        display_words = [e.word for e in words]
        return PuzzleBase(
            kind="word_search",
            title=title,
            instructions=(
                "Najděte v mřížce všechna slova ze seznamu. "
                + (
                    "Slova jdou jen doprava nebo dolů."
                    if difficulty == Difficulty.easy
                    else "Slova mohou jít všemi směry včetně pozpátku."
                )
            ),
            difficulty=difficulty,
            seed=seed,
            data={
                "size": size,
                "grid": grid,
                "words": display_words,
                "words_normalized": [e.normalized for e in words],
                "theme": theme,
                "theme_title": title,
                "grid_diacritics": grid_diacritics,
                "list_columns": spec["list_columns"],
                "puzzle_number": None,
                "difficulty_marker": {
                    Difficulty.easy: "●○○",
                    Difficulty.medium: "●●○",
                    Difficulty.hard: "●●●",
                }[difficulty],
                "difficulty_label_cs": {
                    Difficulty.easy: "LEHKÁ",
                    Difficulty.medium: "STŘEDNÍ",
                    Difficulty.hard: "TĚŽKÁ",
                }[difficulty],
            },
            answer={"placements": placements},
        )
    raise ValueError(
        f"Could not generate word-search (theme={theme}, difficulty={difficulty}, "
        f"seed={seed}): {last_error}"
    )


def words_are_path_compatible(entries: list[NounEntry]) -> bool:
    """Reject sets where one normalized form is a contiguous substring of another."""
    norms = [e.normalized for e in entries]
    for i, a in enumerate(norms):
        rev = a[::-1]
        for j, b in enumerate(norms):
            if i == j:
                continue
            if a in b or rev in b or b in a:
                return False
    return True


def select_themed_words(
    *,
    difficulty: Difficulty,
    count: int,
    used: set[str],
    rng,
    preferred_themes: list[str] | None = None,
) -> tuple[str, list[NounEntry]]:
    vocab = load_vocabulary()
    level = difficulty.value  # type: ignore[assignment]
    themes = preferred_themes or categories_with_enough(
        vocab, difficulty=level, needed=count, used_normalized=used
    )
    if preferred_themes:
        # Fall back to any theme with enough unused words
        extras = categories_with_enough(
            vocab, difficulty=level, needed=count, used_normalized=used
        )
        themes = list(dict.fromkeys([*preferred_themes, *extras]))
    if not themes:
        raise ValueError(
            f"Not enough unused {difficulty.value} nouns for any theme "
            f"(need {count}). Expand data/word-search/cs-nouns.yaml."
        )
    rng.shuffle(themes)
    for theme in themes:
        pool = pool_for(
            vocab, difficulty=level, category=theme, used_normalized=used
        )
        if len(pool) < count:
            continue
        for _ in range(80):
            rng.shuffle(pool)
            chosen = pool[:count]
            if words_are_path_compatible(chosen):
                return theme, chosen
            # Try replacing conflicting tails
            chosen = []
            for entry in pool:
                trial = chosen + [entry]
                if words_are_path_compatible(trial):
                    chosen.append(entry)
                if len(chosen) == count:
                    return theme, chosen
    raise ValueError(
        f"Could not select {count} unused compatible {difficulty.value} words for one theme"
    )


@register
class WordSearchGenerator(GameGenerator):
    """Single-page generator (legacy theme YAML or curated nouns)."""

    kind = "word_search"

    def generate(
        self,
        *,
        seed: int,
        difficulty: Difficulty,
        title: str | None = None,
        params: dict[str, Any] | None = None,
    ) -> PuzzleBase:
        params = params or {}
        rng = make_rng(seed)
        grid_diacritics = bool(params.get("grid_diacritics", False))
        used: set[str] = set(params.get("used_normalized") or [])
        theme_param = params.get("theme")
        spec = DIFFICULTY_SPEC[difficulty]
        count = int(params.get("word_count") or spec["word_count"])

        if theme_param and theme_param in THEME_TITLES_CS:
            preferred = [theme_param]
        elif theme_param:
            # Legacy small theme YAML path
            from creobook.games.word_search_legacy import build_from_legacy_theme

            return build_from_legacy_theme(
                theme=theme_param,
                seed=seed,
                difficulty=difficulty,
                title=title,
                params=params,
            )
        else:
            preferred = None

        theme, words = select_themed_words(
            difficulty=difficulty,
            count=count,
            used=used,
            rng=rng,
            preferred_themes=preferred,
        )
        puzzle = generate_puzzle(
            seed=seed,
            difficulty=difficulty,
            theme=theme,
            words=words,
            grid_diacritics=grid_diacritics,
        )
        if title:
            puzzle.title = title
        return puzzle
