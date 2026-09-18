"""Czech word-search puzzles with deterministic placement."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from creobook.games.base import GameGenerator, make_rng, register
from creobook.games.models import Difficulty, PuzzleBase
from creobook.theme import project_root

DIRS = {
    "E": (0, 1),
    "S": (1, 0),
    "SE": (1, 1),
    "SW": (1, -1),
    "W": (0, -1),
    "N": (-1, 0),
    "NE": (-1, 1),
    "NW": (-1, -1),
}


def words_dir() -> Path:
    return project_root() / "config" / "games" / "words"


def load_theme_words(theme: str) -> list[str]:
    path = words_dir() / f"{theme}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Word theme not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    words = [str(w).strip().upper() for w in raw.get("words", [])]
    words = [w for w in words if w]
    if len(words) < 5:
        raise ValueError(f"Theme {theme} needs at least 5 words")
    return words


def _allowed_dirs(difficulty: Difficulty) -> list[str]:
    if difficulty == Difficulty.easy:
        return ["E", "S"]
    if difficulty == Difficulty.medium:
        return ["E", "S", "SE", "SW"]
    return list(DIRS.keys())


def _can_place(
    grid: list[list[str | None]], word: str, r: int, c: int, dr: int, dc: int
) -> bool:
    rows, cols = len(grid), len(grid[0])
    for i, ch in enumerate(word):
        rr, cc = r + dr * i, c + dc * i
        if not (0 <= rr < rows and 0 <= cc < cols):
            return False
        cell = grid[rr][cc]
        if cell is not None and cell != ch:
            return False
    return True


def _place(
    grid: list[list[str | None]], word: str, r: int, c: int, dr: int, dc: int
) -> None:
    for i, ch in enumerate(word):
        grid[r + dr * i][c + dc * i] = ch


def build_word_search(
    words: list[str],
    size: int,
    dirs: list[str],
    rng,
) -> tuple[list[list[str]], list[dict[str, Any]]]:
    grid: list[list[str | None]] = [[None] * size for _ in range(size)]
    placements: list[dict[str, Any]] = []
    ordered = sorted(words, key=len, reverse=True)
    for word in ordered:
        placed = False
        attempts = list(range(200))
        rng.shuffle(attempts)
        dir_names = dirs[:]
        rng.shuffle(dir_names)
        for _ in attempts:
            dname = rng.choice(dir_names)
            dr, dc = DIRS[dname]
            r = rng.randrange(size)
            c = rng.randrange(size)
            if _can_place(grid, word, r, c, dr, dc):
                _place(grid, word, r, c, dr, dc)
                placements.append(
                    {
                        "word": word,
                        "row": r,
                        "col": c,
                        "direction": dname,
                        "length": len(word),
                    }
                )
                placed = True
                break
        if not placed:
            raise ValueError(f"Could not place word {word}")
    alphabet = "AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPRŘSŠTŤUÚŮVXYÝZŽ"
    for r in range(size):
        for c in range(size):
            if grid[r][c] is None:
                grid[r][c] = rng.choice(alphabet)
    # Verify placements still match
    for p in placements:
        dr, dc = DIRS[p["direction"]]
        built = "".join(
            grid[p["row"] + dr * i][p["col"] + dc * i] for i in range(p["length"])
        )
        if built != p["word"]:
            raise ValueError(f"Placement broken for {p['word']}")
    return [[cell or "?" for cell in row] for row in grid], placements


@register
class WordSearchGenerator(GameGenerator):
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
        theme = params.get("theme") or "zvířata"
        all_words = load_theme_words(theme)
        count = {Difficulty.easy: 8, Difficulty.medium: 10, Difficulty.hard: 12}[
            difficulty
        ]
        size = {Difficulty.easy: 10, Difficulty.medium: 12, Difficulty.hard: 14}[
            difficulty
        ]
        words = all_words[:]
        rng.shuffle(words)
        words = words[:count]
        # Prefer words that fit
        words = [w for w in words if len(w) <= size]
        if len(words) < 5:
            words = [w for w in all_words if len(w) <= size][:count]
        grid, placements = build_word_search(
            words, size, _allowed_dirs(difficulty), rng
        )
        theme_titles = {
            "zvířata": "Osmisměrka — zvířata",
            "cestování": "Osmisměrka — cestování",
            "vesmír": "Osmisměrka — vesmír",
            "knihy": "Osmisměrka — knihy",
            "příroda": "Osmisměrka — příroda",
        }
        return PuzzleBase(
            kind=self.kind,
            title=title or theme_titles.get(theme, f"Osmisměrka — {theme}"),
            instructions=(
                "Najdi všechna slova v mřížce. Slova jsou napsaná bez mezer. "
                "Odškrtni si každé nalezené slovo ze seznamu."
            ),
            difficulty=difficulty,
            seed=seed,
            data={
                "size": size,
                "grid": grid,
                "words": words,
                "theme": theme,
            },
            answer={"placements": placements},
        )
