"""Curated Czech crossword clues and tajenka phrases."""

from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from creobook.theme import project_root

DifficultyTag = Literal["easy", "medium", "hard"]
ThemeId = Literal["animals", "nature", "everyday", "school", "mixed"]

THEME_TITLES_CS: dict[str, str] = {
    "animals": "Zvířata",
    "nature": "Příroda",
    "everyday": "Každodenní život",
    "school": "Škola",
    "mixed": "Smíšené",
}

DATASET_VERSION = "1.0.0"

# Letters allowed in answers/tajenky (Czech + CH as C+H).
_ALLOWED = set("AÁBCČDĎEÉĚFGHIÍJKLMNŇOÓPQRŘSŠTŤUÚŮVWXYÝZŽ")


def nfc_upper(text: str) -> str:
    return unicodedata.normalize("NFC", text.strip().upper())


def answer_cells(answer: str) -> list[str]:
    """Uppercase NFC letters without spaces; CH occupies two cells (C and H)."""
    return [ch for ch in nfc_upper(answer) if not ch.isspace()]


def tajenka_letters(phrase: str) -> list[str]:
    return [ch for ch in nfc_upper(phrase) if not ch.isspace()]


def tajenka_key(phrase: str) -> str:
    return "".join(tajenka_letters(phrase))


class ClueEntry(BaseModel):
    answer: str
    clue: str
    themes: list[str]
    difficulty: list[DifficultyTag]

    @field_validator("answer")
    @classmethod
    def _answer_ok(cls, value: str) -> str:
        value = nfc_upper(value).replace(" ", "")
        if len(value) < 2 or len(value) > 14:
            raise ValueError(f"answer length out of range: {value!r}")
        if any(ch not in _ALLOWED for ch in value):
            raise ValueError(f"answer has unsupported characters: {value!r}")
        return value

    @field_validator("clue")
    @classmethod
    def _clue_ok(cls, value: str) -> str:
        value = unicodedata.normalize("NFC", value.strip())
        if len(value) < 3:
            raise ValueError("clue too short")
        return value

    @field_validator("themes")
    @classmethod
    def _themes_ok(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("themes must be non-empty")
        for theme in value:
            if theme not in THEME_TITLES_CS:
                raise ValueError(f"unknown theme: {theme!r}")
        return value

    @field_validator("difficulty")
    @classmethod
    def _diff_ok(cls, value: list[DifficultyTag]) -> list[DifficultyTag]:
        if not value:
            raise ValueError("difficulty must be non-empty")
        return value

    @property
    def cells(self) -> list[str]:
        return answer_cells(self.answer)


class TajenkaEntry(BaseModel):
    phrase: str
    themes: list[str]
    difficulty: list[DifficultyTag]

    @field_validator("phrase")
    @classmethod
    def _phrase_ok(cls, value: str) -> str:
        value = nfc_upper(value)
        parts = value.split()
        value = " ".join(parts)
        letters = "".join(parts)
        if len(letters) < 5 or len(letters) > 14:
            raise ValueError(f"tajenka letter count out of range: {value!r}")
        if any(ch not in _ALLOWED for ch in letters):
            raise ValueError(f"tajenka has unsupported characters: {value!r}")
        return value

    @field_validator("themes")
    @classmethod
    def _themes_ok(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("themes must be non-empty")
        for theme in value:
            if theme not in THEME_TITLES_CS:
                raise ValueError(f"unknown theme: {theme!r}")
        return value

    @property
    def letters(self) -> list[str]:
        return tajenka_letters(self.phrase)

    @property
    def key(self) -> str:
        return tajenka_key(self.phrase)


class CrosswordDataset(BaseModel):
    version: str = DATASET_VERSION
    language: str = "cs"
    themes: dict[str, str] = Field(default_factory=lambda: dict(THEME_TITLES_CS))
    clues: list[ClueEntry]
    tajenky: list[TajenkaEntry]

    @model_validator(mode="after")
    def _nonempty(self) -> CrosswordDataset:
        if len(self.clues) < 50:
            raise ValueError("dataset needs at least 50 clues")
        if len(self.tajenky) < 20:
            raise ValueError("dataset needs at least 20 tajenky")
        return self


def default_dataset_path() -> Path:
    return project_root() / "data" / "crossword" / "cs-clues.yaml"


@lru_cache(maxsize=2)
def load_crossword_dataset(path: str | None = None) -> CrosswordDataset:
    import yaml

    dataset_path = Path(path) if path else default_dataset_path()
    with dataset_path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return CrosswordDataset.model_validate(raw)


def clues_for(
    dataset: CrosswordDataset,
    *,
    difficulty: DifficultyTag,
    theme: str | None = None,
) -> list[ClueEntry]:
    out: list[ClueEntry] = []
    for clue in dataset.clues:
        if difficulty not in clue.difficulty:
            continue
        if theme and theme != "mixed":
            if theme not in clue.themes and "mixed" not in clue.themes:
                continue
        out.append(clue)
    return out


def tajenky_for(
    dataset: CrosswordDataset,
    *,
    difficulty: DifficultyTag,
    theme: str | None = None,
    letter_min: int,
    letter_max: int,
) -> list[TajenkaEntry]:
    out: list[TajenkaEntry] = []
    for item in dataset.tajenky:
        if difficulty not in item.difficulty:
            continue
        n = len(item.letters)
        if n < letter_min or n > letter_max:
            continue
        if theme and theme != "mixed":
            if theme not in item.themes and "mixed" not in item.themes:
                continue
        out.append(item)
    return out
