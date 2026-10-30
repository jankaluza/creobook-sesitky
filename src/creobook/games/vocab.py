"""Curated Czech noun vocabulary for word-search puzzles."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from creobook.theme import project_root

DifficultyTag = Literal["easy", "medium", "hard"]

DIACRITIC_MAP = str.maketrans(
    {
        "Á": "A",
        "Ä": "A",
        "Č": "C",
        "Ď": "D",
        "É": "E",
        "Ě": "E",
        "Í": "I",
        "Ň": "N",
        "Ó": "O",
        "Ö": "O",
        "Ř": "R",
        "Š": "S",
        "Ť": "T",
        "Ú": "U",
        "Ů": "U",
        "Ü": "U",
        "Ý": "Y",
        "Ž": "Z",
    }
)

SUPPORTED_NORMALIZED = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
WORD_RE = re.compile(r"^[a-záäčďéěíňóöřšťúůüýž]+$", re.IGNORECASE)

THEME_TITLES_CS: dict[str, str] = {
    "animals": "Zvířata",
    "nature": "V přírodě",
    "home": "Doma",
    "food": "Jídlo",
    "school": "Ve škole",
    "professions": "Povolání",
    "travel": "Na cestách",
    "sport": "Sport",
    "culture": "Kultura",
    "tools": "Nástroje",
    "clothing": "Oblečení",
    "body": "Tělo",
    "city": "Ve městě",
    "countryside": "Na zahradě",
    "objects": "Předměty",
    "science": "Věda",
    "emotions": "Pocity",
    "weather": "Počasí",
}

LENGTH_BOUNDS: dict[str, tuple[int, int]] = {
    "easy": (4, 8),
    "medium": (5, 10),
    "hard": (6, 12),
}

VOCAB_VERSION = "1.0.0"


def normalize_czech(word: str) -> str:
    """Uppercase and strip diacritics for grid placement (CH stays as C+H)."""
    upper = word.strip().upper()
    # Decompose then drop combining marks as a safety net, then map leftovers.
    nfkd = unicodedata.normalize("NFKD", upper)
    base = "".join(ch for ch in nfkd if not unicodedata.combining(ch))
    return base.translate(DIACRITIC_MAP)


class NounEntry(BaseModel):
    word: str
    normalized: str
    category: str
    difficulty: list[DifficultyTag]
    plural_only: bool = False
    child_safe: bool = True
    pos: Literal["noun"] = "noun"

    @field_validator("word")
    @classmethod
    def _word_form(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("word must be non-empty")
        if not WORD_RE.match(value):
            raise ValueError(f"invalid Czech word form: {value!r}")
        if any(ch.isdigit() or ch in " -'./\\" for ch in value):
            raise ValueError(f"word contains forbidden characters: {value!r}")
        return value

    @field_validator("normalized")
    @classmethod
    def _normalized_form(cls, value: str) -> str:
        value = value.strip().upper()
        if not value or any(ch not in SUPPORTED_NORMALIZED for ch in value):
            raise ValueError(f"normalized must be A–Z only: {value!r}")
        return value

    @field_validator("category")
    @classmethod
    def _known_category(cls, value: str) -> str:
        if value not in THEME_TITLES_CS:
            raise ValueError(f"unknown category: {value!r}")
        return value

    @field_validator("difficulty")
    @classmethod
    def _difficulty_nonempty(cls, value: list[DifficultyTag]) -> list[DifficultyTag]:
        if not value:
            raise ValueError("difficulty must list at least one level")
        return list(dict.fromkeys(value))

    @model_validator(mode="after")
    def _check_normalized_matches(self) -> NounEntry:
        expected = normalize_czech(self.word)
        if self.normalized != expected:
            raise ValueError(
                f"normalized mismatch for {self.word!r}: "
                f"got {self.normalized!r}, expected {expected!r}"
            )
        if not self.child_safe:
            raise ValueError(f"entry marked not child-safe: {self.word!r}")
        if self.pos != "noun":
            raise ValueError(f"only nouns allowed: {self.word!r}")
        return self


class VocabularyFile(BaseModel):
    version: str = VOCAB_VERSION
    language: Literal["cs"] = "cs"
    nouns: list[NounEntry] = Field(default_factory=list)


def default_vocab_path() -> Path:
    return project_root() / "data" / "word-search" / "cs-nouns.yaml"


def load_vocabulary(path: Path | None = None) -> VocabularyFile:
    import yaml

    vocab_path = path or default_vocab_path()
    raw = yaml.safe_load(vocab_path.read_text(encoding="utf-8"))
    vocab = VocabularyFile.model_validate(raw)
    validate_vocabulary(vocab)
    return vocab


def validate_vocabulary(vocab: VocabularyFile) -> None:
    """Raise ValueError if the curated list has structural problems."""
    seen_norm: set[str] = set()
    seen_word: set[str] = set()
    for entry in vocab.nouns:
        key = entry.normalized
        if key in seen_norm:
            raise ValueError(f"duplicate normalized word: {key}")
        seen_norm.add(key)
        low = entry.word.casefold()
        if low in seen_word:
            raise ValueError(f"duplicate Czech word: {entry.word}")
        seen_word.add(low)
        if entry.word != entry.word.lower() and not entry.word.islower():
            # Reject Title Case / ALL CAPS proper-name style entries
            if entry.word[0].isupper() and entry.word[1:].islower():
                raise ValueError(f"looks like a proper name: {entry.word!r}")
        for level in entry.difficulty:
            lo, hi = LENGTH_BOUNDS[level]
            n = len(entry.normalized)
            if not (lo <= n <= hi):
                raise ValueError(
                    f"{entry.word!r} length {n} outside {level} bounds {lo}-{hi}"
                )


def pool_for(
    vocab: VocabularyFile,
    *,
    difficulty: DifficultyTag,
    category: str | None = None,
    used_normalized: set[str] | None = None,
) -> list[NounEntry]:
    used = used_normalized or set()
    lo, hi = LENGTH_BOUNDS[difficulty]
    out: list[NounEntry] = []
    for entry in vocab.nouns:
        if difficulty not in entry.difficulty:
            continue
        if category is not None and entry.category != category:
            continue
        if entry.normalized in used:
            continue
        if not (lo <= len(entry.normalized) <= hi):
            continue
        if not entry.child_safe:
            continue
        out.append(entry)
    return out


def count_pools(vocab: VocabularyFile) -> dict[str, int]:
    return {
        level: len(pool_for(vocab, difficulty=level))  # type: ignore[arg-type]
        for level in ("easy", "medium", "hard")
    }


def categories_with_enough(
    vocab: VocabularyFile,
    *,
    difficulty: DifficultyTag,
    needed: int,
    used_normalized: set[str] | None = None,
) -> list[str]:
    cats: list[str] = []
    for cat in THEME_TITLES_CS:
        if len(pool_for(vocab, difficulty=difficulty, category=cat, used_normalized=used_normalized)) >= needed:
            cats.append(cat)
    return cats
