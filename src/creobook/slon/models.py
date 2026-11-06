"""Configuration for Najdi slona! booklets."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from creobook.coloring.models import (
    DEFAULT_TEXT_MODEL,
    IMAGE_MODELS,
    IMAGE_SIZES,
    ImageQuality,
)

PageFormat = Literal["A5", "A6"]
Difficulty = Literal["easy", "medium", "hard"]
AgeGroup = Literal["3-5", "6-8", "9-12"]

# Width of the elephant as a fraction of the scene width.
SCALES = {"easy": 0.11, "medium": 0.085, "hard": 0.06}


class SlonError(Exception):
    """A Najdi slona booklet cannot continue."""


class SlonConfig(BaseModel):
    theme: str
    title: str
    puzzle_count: int = Field(default=12, ge=1, le=24)
    age_group: AgeGroup = "6-8"
    difficulty: Difficulty = "medium"
    difficulties: list[Difficulty] = Field(default_factory=list)
    page_format: PageFormat = "A5"
    image_model: str = "gpt-image-2.5-flare"
    image_quality: ImageQuality = "medium"
    image_size: str = "1024x1536"
    text_model: str = DEFAULT_TEXT_MODEL
    include_solutions: bool = True
    output_directory: str
    max_new: int = Field(default=16, ge=0, le=25)

    @field_validator("theme", "title")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    @model_validator(mode="after")
    def _mix_matches_count(self) -> SlonConfig:
        if self.difficulties and len(self.difficulties) != self.puzzle_count:
            raise ValueError("mix length must equal puzzle_count")
        return self

    def page_difficulties(self) -> list[Difficulty]:
        if self.difficulties:
            return list(self.difficulties)
        return [self.difficulty] * self.puzzle_count

    def validate_image_options(self) -> None:
        if self.image_model not in IMAGE_MODELS:
            raise SlonError(
                f"Unsupported image model {self.image_model!r}. "
                f"Use one of: {', '.join(IMAGE_MODELS)}."
            )
        if self.image_quality not in ("low", "medium", "high"):
            raise SlonError(f"Unsupported quality {self.image_quality!r}.")
        if self.image_size not in IMAGE_SIZES:
            raise SlonError(
                f"Unsupported size {self.image_size!r}. Use one of: {', '.join(IMAGE_SIZES)}."
            )


class SceneSpec(BaseModel):
    id: str
    title: str
    description: str
    objects: list[str] = Field(default_factory=list)
    hiding_spots: list[str] = Field(default_factory=list)
    complexity: str = "medium"
    composition: str = ""


class Placement(BaseModel):
    scene_id: str
    asset_id: str = "elephant"
    cx: float
    cy: float
    scale: float
    rotation: float = 0
    manual: bool = False
    occlusion: str | None = None
    bbox_x: float = 0
    bbox_y: float = 0
    bbox_w: float = 0
    bbox_h: float = 0

    def clamped(self) -> None:
        if not 0.08 <= self.cx <= 0.92 or not 0.08 <= self.cy <= 0.92:
            raise SlonError("Elephant center must stay inside the picture (0.08–0.92).")
        if not 0.04 <= self.scale <= 0.2:
            raise SlonError("Elephant scale must stay between 4% and 20% of the picture width.")


def expand_mix(text: str) -> list[str]:
    """``easy:4,medium:4,hard:4`` becomes four easy pages, then four medium, then four hard."""
    items: list[str] = []
    for part in text.split(","):
        piece = part.strip()
        if not piece:
            continue
        if ":" not in piece:
            raise SlonError(f"Mix item {piece!r} must look like easy:4")
        raw_name, raw_count = piece.split(":", 1)
        name = raw_name.strip().lower()
        if name not in SCALES:
            raise SlonError(f"Unknown difficulty {name!r}. Use easy, medium, or hard.")
        try:
            count = int(raw_count.strip())
        except ValueError as exc:
            raise SlonError(f"Mix item {piece!r} must look like easy:4") from exc
        if count < 1:
            raise SlonError(f"Mix item {piece!r} has no pages")
        items.extend([name] * count)
    if not items:
        raise SlonError("Mix is empty")
    if len(items) > 24:
        raise SlonError("A booklet can hold at most 24 scenes")
    return items
