"""Shared models for CreoBook game puzzles and booklets."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"
    mixed = "mixed"


class GameKind(str, Enum):
    cover = "cover"
    instructions = "instructions"
    back = "back"
    sudoku = "sudoku"
    maze = "maze"
    word_search = "word_search"
    nonogram = "nonogram"
    connect_dots = "connect_dots"
    spot_difference = "spot_difference"
    cipher = "cipher"
    two_player = "two_player"
    solutions = "solutions"
    bonus = "bonus"
    free_grid = "free_grid"
    score_table = "score_table"
    rules = "rules"


class PuzzleBase(BaseModel):
    kind: str
    title: str
    instructions: str
    difficulty: Difficulty = Difficulty.easy
    seed: int
    show_answer: bool = False
    answer: dict[str, Any] = Field(default_factory=dict)
    data: dict[str, Any] = Field(default_factory=dict)


class PageSpec(BaseModel):
    """One slot in a booklet pack YAML."""

    kind: str
    title: str | None = None
    difficulty: Difficulty | None = None
    theme: str | None = None
    variant: str | None = None
    size: int | None = None
    params: dict[str, Any] = Field(default_factory=dict)


class PackConfig(BaseModel):
    id: str
    title: str
    subtitle: str = ""
    description: str = ""
    sheets: int = 4
    difficulty: Difficulty = Difficulty.mixed
    seed: int = 20260917
    answers: bool = True
    language: Literal["cs"] = "cs"
    pages: list[PageSpec]


class BookletBuildOptions(BaseModel):
    pack_id: str
    sheets: int | None = None
    difficulty: Difficulty | None = None
    seed: int | None = None
    answers: bool | None = None
    accent: str | None = None
