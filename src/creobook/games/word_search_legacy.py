"""Legacy theme-YAML word lists for single-page `games word-search --theme`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from creobook.games.base import make_rng
from creobook.games.models import Difficulty, PuzzleBase
from creobook.games.vocab import NounEntry, normalize_czech
from creobook.theme import project_root


def words_dir() -> Path:
    return project_root() / "config" / "games" / "words"


def load_theme_words(theme: str) -> list[str]:
    path = words_dir() / f"{theme}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Word theme not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    words = [str(w).strip() for w in raw.get("words", [])]
    words = [w for w in words if w]
    if len(words) < 5:
        raise ValueError(f"Theme {theme} needs at least 5 words")
    return words


def build_from_legacy_theme(
    *,
    theme: str,
    seed: int,
    difficulty: Difficulty,
    title: str | None,
    params: dict[str, Any],
) -> PuzzleBase:
    from creobook.games.word_search import (
        DIFFICULTY_SPEC,
        generate_puzzle,
    )

    raw_words = load_theme_words(theme)
    rng = make_rng(seed)
    spec = DIFFICULTY_SPEC[difficulty]
    count = int(params.get("word_count") or spec["word_count"])
    size = int(spec["size"])
    # Legacy lists are often uppercase without diacritics — treat as display+normalized
    entries: list[NounEntry] = []
    for w in raw_words:
        display = w.lower() if w.isupper() else w
        norm = normalize_czech(display)
        if len(norm) > size:
            continue
        lo, hi = {
            Difficulty.easy: (4, 8),
            Difficulty.medium: (5, 10),
            Difficulty.hard: (6, 12),
        }[difficulty]
        if not (lo <= len(norm) <= hi):
            continue
        try:
            entries.append(
                NounEntry(
                    word=display,
                    normalized=norm,
                    category="objects",
                    difficulty=[difficulty.value],  # type: ignore[list-item]
                    plural_only=False,
                    child_safe=True,
                )
            )
        except ValueError:
            continue
    rng.shuffle(entries)
    chosen = entries[:count]
    if len(chosen) < min(5, count):
        raise ValueError(f"Theme {theme} has too few placeable words for {difficulty}")
    puzzle = generate_puzzle(
        seed=seed,
        difficulty=difficulty,
        theme="objects",
        words=chosen,
        grid_diacritics=bool(params.get("grid_diacritics", False)),
    )
    theme_titles = {
        "zvířata": "Osmisměrka — zvířata",
        "cestování": "Osmisměrka — cestování",
        "vesmír": "Osmisměrka — vesmír",
        "knihy": "Osmisměrka — knihy",
        "příroda": "Osmisměrka — příroda",
    }
    puzzle.title = title or theme_titles.get(theme, f"Osmisměrka — {theme}")
    puzzle.data["theme"] = theme
    puzzle.data["theme_title"] = puzzle.title
    return puzzle
