"""Shared fixtures for coloring-book tests. No network and no OpenAI calls."""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

from creobook.coloring.images import GeneratedImage
from creobook.coloring.models import ColoringConfig, Illustration


def line_png(width: int = 80, height: int = 120) -> bytes:
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, width - 9, height - 9), outline=0, width=2)
    draw.ellipse((28, 40, 52, 64), outline=0, width=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def sample_config(tmp_path, **overrides) -> ColoringConfig:
    data = {
        "theme": "Forest animals",
        "title": "Lesní kamarádi",
        "age_group": "6-8",
        "illustration_count": 1,
        "page_format": "A5",
        "output_directory": str(tmp_path / "book"),
        "max_new": 8,
    }
    data.update(overrides)
    return ColoringConfig.model_validate(data)


_SCENES = {
    1: "A smiling fox sitting under an oak tree with one mushroom",
    2: "A hedgehog carrying an apple along a river bank",
    3: "Two rabbits playing beside a meadow of daisies",
    4: "A squirrel collecting acorns on a pine branch",
}


def illustration(index: int = 1) -> Illustration:
    return Illustration(
        id=f"animal-{index}",
        title=f"Zvíře {index}",
        description=_SCENES.get(index, f"An original forest creature labeled only as visitor {index} {index * 13}"),
        complexity="medium",
        subjects=[f"creature-{index}"],
        background="open white space with one plant",
    )


class FakeColoringAPI:
    def __init__(self, plan_json: str, png: bytes | None = None) -> None:
        self.plan_json = plan_json
        self.png = png if png is not None else line_png()
        self.text_calls = 0
        self.image_calls = 0
        self.fail_images = False

    def complete_text(self, prompt: str, *, model: str) -> str:
        self.text_calls += 1
        assert model
        assert "Forest" in prompt or "theme" in prompt.lower()
        return self.plan_json

    def generate_image(self, *, prompt: str, model: str, size: str, quality: str) -> GeneratedImage:
        if self.fail_images:
            raise AssertionError("image API should not be called")
        self.image_calls += 1
        assert "black outlines" in prompt.lower() or "Pure black" in prompt
        return GeneratedImage(png=self.png, usage={"output_tokens": 12}, model=model, size=size, quality=quality)


@pytest.fixture
def png_bytes() -> bytes:
    return line_png()
