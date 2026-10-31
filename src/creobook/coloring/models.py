"""Configuration and illustration-plan models for coloring booklets."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

AgeGroup = Literal["3-5", "6-8", "9-12"]
PageFormat = Literal["A5", "A6"]
ImageQuality = Literal["low", "medium", "high"]
Complexity = Literal["simple", "medium", "detailed"]

IMAGE_MODELS = ("gpt-image-2.5-flare", "gpt-image-2.5-sunburst")
IMAGE_QUALITIES = ("low", "medium", "high")
# Portrait sizes accepted by GPT Image 2.5. The default stays at the smaller one.
IMAGE_SIZES = ("1024x1536", "2160x3840")
DEFAULT_IMAGE_MODEL = "gpt-image-2.5-flare"
DEFAULT_IMAGE_SIZE = "1024x1536"
DEFAULT_TEXT_MODEL = "gpt-6-astra"

PAGE_FORMATS: dict[str, dict[str, float]] = {
    "A5": {
        "width_mm": 148.0,
        "height_mm": 210.0,
        "sheet_width_mm": 297.0,
        "sheet_height_mm": 210.0,
        "margin_inside_mm": 12.0,
        "margin_outside_mm": 10.0,
        "margin_top_mm": 10.0,
        "margin_bottom_mm": 10.0,
    },
    "A6": {
        "width_mm": 105.0,
        "height_mm": 148.0,
        "sheet_width_mm": 210.0,
        "sheet_height_mm": 148.0,
        "margin_inside_mm": 10.0,
        "margin_outside_mm": 8.0,
        "margin_top_mm": 8.0,
        "margin_bottom_mm": 8.0,
    },
}


class ColoringError(Exception):
    """A coloring-booklet run cannot continue."""


class ProcessSettings(BaseModel):
    white_threshold: int = 235
    black_threshold: int = 90
    min_speck: int = 4

    @field_validator("white_threshold", "black_threshold")
    @classmethod
    def _byte(cls, value: int) -> int:
        if not 0 <= value <= 255:
            raise ValueError("thresholds must be between 0 and 255")
        return value


class ColoringConfig(BaseModel):
    theme: str
    title: str
    age_group: AgeGroup = "6-8"
    illustration_count: int = Field(default=8, ge=1, le=43)
    page_format: PageFormat = "A5"
    image_model: str = DEFAULT_IMAGE_MODEL
    image_quality: ImageQuality = "medium"
    image_size: str = DEFAULT_IMAGE_SIZE
    text_model: str = DEFAULT_TEXT_MODEL
    single_sided: bool = False
    output_directory: str
    max_new: int = Field(default=16, ge=0, le=43)
    process: ProcessSettings = Field(default_factory=ProcessSettings)

    @field_validator("theme", "title")
    @classmethod
    def _not_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be empty")
        return cleaned

    def validate_image_options(self) -> None:
        if self.image_model not in IMAGE_MODELS:
            raise ColoringError(
                f"Unsupported image model {self.image_model!r}. "
                f"Use one of: {', '.join(IMAGE_MODELS)}."
            )
        if self.image_quality not in IMAGE_QUALITIES:
            raise ColoringError(
                f"Unsupported quality {self.image_quality!r}. "
                f"Use one of: {', '.join(IMAGE_QUALITIES)}."
            )
        if self.image_size not in IMAGE_SIZES:
            raise ColoringError(
                f"Unsupported size {self.image_size!r} for {self.image_model}. "
                f"Portrait sizes: {', '.join(IMAGE_SIZES)}."
            )
        width, height = (int(part) for part in self.image_size.split("x"))
        if height <= width:
            raise ColoringError("Coloring illustrations must be portrait")


class Illustration(BaseModel):
    id: str
    title: str
    description: str
    complexity: Complexity
    subjects: list[str] = Field(default_factory=list)
    background: str = ""
    copyright_flags: list[str] = Field(default_factory=list)


class IllustrationPlan(BaseModel):
    theme: str
    age_group: AgeGroup
    illustrations: list[Illustration]
    theme_flags: list[str] = Field(default_factory=list)
