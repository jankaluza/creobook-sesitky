"""Configuration for connect-the-dots booklets."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from creobook.coloring.models import IMAGE_MODELS, PAGE_FORMATS, ImageQuality

PageFormat = Literal["A5", "A6"]
Difficulty = Literal["easy", "medium", "hard"]
DIFFICULTY_MAX = {"easy": 30, "medium": 50, "hard": 100}


class DotsError(Exception):
    """A connect-the-dots run cannot continue."""


class DotsConfig(BaseModel):
    theme: str
    title: str
    puzzle_count: int = Field(default=8, ge=1, le=24)
    min_number: int = 0
    max_number: int = Field(default=50, ge=10, le=100)
    difficulty: Difficulty = "medium"
    max_numbers: list[int] = Field(default_factory=list)
    page_format: PageFormat = "A5"
    include_answers: bool = True
    output_directory: str
    image_model: str = "gpt-image-2.5-flare"
    image_quality: ImageQuality = "low"
    max_new: int = Field(default=16, ge=0, le=24)

    @field_validator("theme", "title")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @field_validator("min_number")
    @classmethod
    def _starts_at_zero(cls, value: int) -> int:
        if value != 0:
            raise ValueError("numbering always starts at 0")
        return value

    @field_validator("max_numbers")
    @classmethod
    def _each_maximum(cls, value: list[int]) -> list[int]:
        for item in value:
            if not 10 <= item <= 100:
                raise ValueError("each puzzle maximum must be from 10 to 100")
        return value

    @model_validator(mode="after")
    def _mix_matches_count(self) -> DotsConfig:
        if self.max_numbers and len(self.max_numbers) != self.puzzle_count:
            raise ValueError("mix length must equal puzzle_count")
        return self

    def validate_image_options(self) -> None:
        if self.image_model not in IMAGE_MODELS:
            raise DotsError(
                f"Unsupported image model {self.image_model!r}. "
                f"Use one of: {', '.join(IMAGE_MODELS)}."
            )
        if self.image_quality not in ("low", "medium", "high"):
            raise DotsError(f"Unsupported quality {self.image_quality!r}.")

    def maxima(self) -> list[int]:
        if self.max_numbers:
            return list(self.max_numbers)
        return [self.max_number] * self.puzzle_count


def expand_mix(text: str) -> list[int]:
    """``30:4,50:8`` becomes four 30s and eight 50s."""
    items: list[int] = []
    for part in text.split(","):
        piece = part.strip()
        if not piece:
            continue
        if ":" not in piece:
            raise DotsError(f"Mix item {piece!r} must look like 50:8")
        raw_max, raw_count = piece.split(":", 1)
        try:
            maximum = int(raw_max)
            count = int(raw_count)
        except ValueError as exc:
            raise DotsError(f"Mix item {piece!r} must look like 50:8") from exc
        if not 10 <= maximum <= 100 or count < 1:
            raise DotsError(f"Mix item {piece!r} is outside 10–100 dots or has no puzzles")
        items.extend([maximum] * count)
    if not items:
        raise DotsError("Mix is empty")
    if len(items) > 24:
        raise DotsError("A booklet can hold at most 24 puzzles")
    return items


def content_size(page_format: str) -> tuple[float, float]:
    spec = PAGE_FORMATS[page_format]
    width = spec["width_mm"] - spec["margin_inside_mm"] - spec["margin_outside_mm"]
    height = spec["height_mm"] - spec["margin_top_mm"] - spec["margin_bottom_mm"]
    return width, height
