"""Najdi slona tests. The OpenAI API is replaced with an in-memory fake."""

from __future__ import annotations

import base64
import io
import json

import pytest
from PIL import Image, ImageDraw
from pypdf import PdfReader

from creobook.coloring.images import GeneratedImage, OpenAIColoringClient
from creobook.slon.booklet import PuzzleView, reading_pages
from creobook.slon.composite import (
    circle_mm,
    composite_elephant,
    elephant_view,
    find_open_center,
    knockout_background,
    prepare_elephant,
    slice_elephant,
)
from creobook.slon.models import Placement, SceneSpec, SlonConfig, SlonError, expand_mix
from creobook.slon.planner import mentions_elephant, parse_plan
from creobook.slon.prompts import elephant_prompt, scene_prompt
from creobook.slon.workflow import run_slon_book
from creobook.validation import check_a4_landscape_sheets, check_media_box, check_page_count


def elephant_png() -> bytes:
    image = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 12, 56, 52), outline=0, width=3)
    draw.ellipse((6, 16, 20, 34), outline=0, width=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def scene_png() -> bytes:
    image = Image.new("RGB", (80, 120), "white")
    draw = ImageDraw.Draw(image)
    draw.line((0, 60, 79, 60), fill=0, width=2)
    draw.rectangle((8, 8, 28, 30), outline=0, width=2)
    draw.rectangle((48, 78, 74, 110), outline=0, width=2)
    draw.ellipse((30, 20, 50, 40), outline=0, width=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def sample_config(tmp_path, **overrides) -> SlonConfig:
    data = {
        "theme": "Circus",
        "title": "Najdi slona – Cirkus",
        "puzzle_count": 1,
        "age_group": "6-8",
        "difficulty": "medium",
        "page_format": "A5",
        "output_directory": str(tmp_path / "book"),
        "max_new": 4,
    }
    data.update(overrides)
    return SlonConfig.model_validate(data)


def _plan_json(count: int = 1, description: str | None = None) -> str:
    scenes = []
    for index in range(1, count + 1):
        scenes.append(
            {
                "id": f"stan-{index}",
                "title": f"Pokladna {index}",
                "description": description
                or f"A circus ticket booth with visitors, flags, and snack carts number {index}",
                "objects": ["ticket booth", "flags", "snack cart"],
                "hiding_spots": ["beside the snack cart"],
                "complexity": "medium",
                "composition": "slightly elevated view of the circus entrance",
            }
        )
    return json.dumps({"theme": "Circus", "scenes": scenes})


class FakeSlonAPI:
    def __init__(self, plan_json: str) -> None:
        self.plan_json = plan_json
        self.text_calls = 0
        self.image_calls = 0
        self.fail_images = False
        self.backgrounds: list[str] = []
        self.prompts: list[str] = []

    def complete_text(self, prompt: str, *, model: str) -> str:
        self.text_calls += 1
        assert model
        assert "Circus" in prompt
        assert "elephant" in prompt.lower()
        return self.plan_json

    def generate_image(
        self,
        *,
        prompt: str,
        model: str,
        size: str,
        quality: str,
        background: str = "opaque",
    ) -> GeneratedImage:
        if self.fail_images:
            raise AssertionError("image API should not be called")
        self.image_calls += 1
        self.backgrounds.append(background)
        self.prompts.append(prompt)
        png = scene_png() if "Do not include" in prompt else elephant_png()
        return GeneratedImage(png=png, usage={"output_tokens": 4}, model=model, size=size, quality=quality)


def test_config_rejects_unknown_model_and_bad_counts(tmp_path):
    config = sample_config(tmp_path, image_model="dall-e-3")
    with pytest.raises(SlonError, match="Unsupported image model"):
        config.validate_image_options()
    with pytest.raises(ValueError):
        sample_config(tmp_path, puzzle_count=0)
    with pytest.raises(ValueError):
        sample_config(tmp_path, difficulty="ultra")


def test_plan_parsing_and_scene_prompt_forbids_elephants(tmp_path):
    config = sample_config(tmp_path, puzzle_count=2)
    scenes = parse_plan(_plan_json(2), config)
    assert [scene.id for scene in scenes] == ["stan-1", "stan-2"]
    prompt = scene_prompt(config, scenes[0])
    assert "Do not include" in prompt
    assert "elephant" in prompt.lower()
    assert "black outlines" in prompt.lower()
    character = elephant_prompt(config)
    assert "bow tie" in character
    assert "Do not include" not in character
    assert expand_mix("easy:2,medium:1,hard:1") == ["easy", "easy", "medium", "hard"]
    with pytest.raises(SlonError, match="Unknown difficulty"):
        expand_mix("ultra:1")
    mixed = sample_config(tmp_path, puzzle_count=2, difficulties=["easy", "hard"])
    assert "several open white areas" in scene_prompt(mixed, scenes[0], "easy")
    hard = scene_prompt(mixed, scenes[1], "hard").lower()
    assert "farther away" in hard
    assert "many people" in hard
    copied = json.loads(_plan_json(1))
    copied["scenes"][0]["description"] = "a carved elephant statue beside the gate"
    parsed = parse_plan(json.dumps(copied), config.model_copy(update={"puzzle_count": 1}))
    assert mentions_elephant(parsed[0])


def test_knockout_keeps_interior_white_opaque():
    asset = knockout_background(Image.open(io.BytesIO(elephant_png())))
    assert asset.getpixel((0, 0))[3] == 0
    assert asset.getpixel((32, 32)) == (255, 255, 255, 255)
    assert asset.getpixel((8, 32))[0] == 0
    assert asset.getpixel((8, 32))[3] == 255


def test_composite_clears_only_the_silhouette():
    scene = Image.new("L", (100, 140), 0)
    scene.putpixel((0, 70), 0)
    elephant = prepare_elephant(Image.open(io.BytesIO(elephant_png())))
    composed, placement = composite_elephant(
        scene,
        elephant,
        scene_id="stan",
        cx=0.5,
        cy=0.5,
        scale=0.4,
    )
    left = round(placement.bbox_x * composed.width)
    top = round(placement.bbox_y * composed.height)
    center_x = int((placement.bbox_x + placement.bbox_w / 2) * composed.width)
    center_y = int((placement.bbox_y + placement.bbox_h / 2) * composed.height)
    assert composed.getpixel((left, top)) == 0
    assert composed.getpixel((center_x, center_y)) == 255
    assert composed.getpixel((0, 70)) == 0
    with pytest.raises(SlonError, match="clipped"):
        composite_elephant(
            scene,
            elephant,
            scene_id="stan",
            cx=0.02,
            cy=0.5,
            scale=0.2,
            manual=True,
        )


def _gap_scene() -> Image.Image:
    scene = Image.new("L", (160, 200), 0)
    draw = ImageDraw.Draw(scene)
    draw.rectangle((8, 40, 58, 100), fill=255)
    draw.rectangle((102, 40, 152, 100), fill=255)
    return scene


def test_each_page_hides_a_different_piece_of_the_elephant():
    first = elephant_view(1, "easy")
    second = elephant_view(2, "easy")
    assert first != second
    assert elephant_view(9, "hard")[0] == "trunk"
    whole = Image.new("RGBA", (80, 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(whole)
    draw.ellipse((8, 10, 72, 90), outline=(0, 0, 0, 255), width=3)
    draw.ellipse((4, 18, 24, 40), outline=(0, 0, 0, 255), width=2)
    full = slice_elephant(whole, "full", False)
    trunk = slice_elephant(whole, "trunk", False)
    mirrored = slice_elephant(whole, "trunk", True)
    assert trunk.size[0] < full.size[0]
    assert trunk.getchannel("A").getbbox() is not None
    assert trunk.tobytes() != mirrored.tobytes()


def test_elephant_sits_in_an_open_gap():
    scene = _gap_scene()
    elephant = Image.new("RGBA", (40, 40), (0, 0, 0, 255))
    first = find_open_center(scene, elephant, scale=0.15, used=[], index=0)
    second = find_open_center(scene, elephant, scale=0.15, used=[(first[0], first[1])], index=1)
    assert first[2] is True
    assert second[2] is True

    def gap(cx: float, cy: float) -> str:
        x = cx * 160
        y = cy * 200
        if 8 <= x <= 58 and 40 <= y <= 100:
            return "left"
        if 102 <= x <= 152 and 40 <= y <= 100:
            return "right"
        return "outside"

    assert gap(first[0], first[1]) in {"left", "right"}
    assert gap(second[0], second[1]) in {"left", "right"}
    assert gap(first[0], first[1]) != gap(second[0], second[1])


def test_solution_circle_follows_the_bounding_box():
    placement = Placement(
        scene_id="stan",
        cx=0.5,
        cy=0.5,
        scale=0.1,
        bbox_x=0.4,
        bbox_y=0.6,
        bbox_w=0.1,
        bbox_h=0.08,
    )
    center_x, center_y, radius = circle_mm(placement, 10, 20, 50, 80)
    assert center_x == pytest.approx(10 + 0.45 * 50)
    assert center_y == pytest.approx(20 + 0.64 * 80)
    assert radius == pytest.approx(max(0.1 * 50, 0.08 * 80) / 2 * 1.35)


def test_pages_keep_the_puzzle_unmarked_and_pad(tmp_path):
    config = sample_config(tmp_path)
    placement = Placement(
        scene_id="stan-1",
        cx=0.3,
        cy=0.4,
        scale=0.085,
        bbox_x=0.25,
        bbox_y=0.35,
        bbox_w=0.085,
        bbox_h=0.06,
    )
    pages = reading_pages(config, [PuzzleView(1, "stan-1", placement, 80, 120)])
    assert [page["kind"] for page in pages] == ["cover", "puzzle", "solution", "blank"]
    assert "r_mm" not in pages[1]
    assert pages[1]["elephant"] == "slon-images/elephant.png"
    assert pages[2]["thumbs"][0]["image"] == pages[1]["image"]
    assert pages[2]["thumbs"][0]["r_mm"] > 0


def test_image_request_can_ask_for_a_transparent_background():
    client = OpenAIColoringClient(api_key="sk-test-not-used")
    captured: dict = {}

    class _Images:
        def generate(self, **kwargs):
            captured.update(kwargs)

            class _Item:
                b64_json = base64.b64encode(b"png").decode()

            class _Result:
                data = [_Item()]
                usage = None

            return _Result()

    client._client.images = _Images()
    client.generate_image(
        prompt="elephant",
        model="gpt-image-2.5-flare",
        size="1024x1536",
        quality="low",
        background="transparent",
    )
    assert captured["background"] == "transparent"


def test_dry_run_plans_without_images(tmp_path):
    config = sample_config(tmp_path)
    api = FakeSlonAPI(_plan_json())
    report = run_slon_book(config, dry_run=True, client=api)
    assert api.text_calls == 1
    assert api.image_calls == 0
    assert report.plan_path.is_file()
    again = run_slon_book(config, dry_run=True, client=api)
    assert api.text_calls == 1
    assert "Dry-run" in " ".join(again.notes)


def test_generate_caches_pdf_move_resume_and_pdf_only(tmp_path):
    config = sample_config(tmp_path)
    api = FakeSlonAPI(_plan_json())
    made = run_slon_book(config, generate=True, client=api)
    assert api.image_calls == 2
    assert api.backgrounds == ["transparent", "opaque"]
    assert "Do not include" in api.prompts[1]
    assert made.reading_pdf is not None and made.print_pdf is not None
    assert check_page_count(made.reading_pdf, 4).ok
    assert check_media_box(made.reading_pdf, 148, 210).ok
    assert check_a4_landscape_sheets(made.print_pdf).ok
    assert check_page_count(made.print_pdf, 2).ok
    text = "\n".join(page.extract_text() or "" for page in PdfReader(str(made.reading_pdf)).pages)
    assert "Najdi slona" in text
    assert "Řešení" in text
    assert "Pokladna" not in text
    scene_dir = next((tmp_path / "book" / "scenes").iterdir())
    placement = json.loads((scene_dir / "placement.json").read_text(encoding="utf-8"))
    assert placement["asset_id"] == "elephant"
    assert 0 < placement["bbox_w"] < 0.2
    review = (tmp_path / "book" / "review.html").read_text(encoding="utf-8")
    assert "Pokladna" in review
    assert "x=" in review

    again = run_slon_book(config, generate=True, client=api)
    assert api.image_calls == 2
    assert again.cached_images == 2

    (scene_dir / "composed.png").unlink()
    (tmp_path / "book" / "elephant" / "asset.png").unlink()
    api.fail_images = True
    resumed = run_slon_book(config, client=api)
    assert api.image_calls == 2
    assert (scene_dir / "composed.png").is_file()
    assert (tmp_path / "book" / "elephant" / "asset.png").is_file()
    assert resumed.reading_pdf is not None

    offline = run_slon_book(config, pdf_only=True, client=api)
    assert api.image_calls == 2
    assert offline.print_pdf is not None

    api.fail_images = False
    regenerated = run_slon_book(config, regenerate_scene=1, client=api)
    assert api.image_calls == 3

    moved = run_slon_book(config, move_elephant=1, position=(0.4, 0.62), client=api)
    assert api.image_calls == 3
    updated = json.loads((scene_dir / "placement.json").read_text(encoding="utf-8"))
    assert updated["manual"] is True
    assert updated["cx"] == pytest.approx(0.4, abs=0.02)
    assert updated["cy"] == pytest.approx(0.62, abs=0.02)
    assert moved.reading_pdf is not None


def test_max_new_stops_before_any_image_call(tmp_path):
    config = sample_config(tmp_path, max_new=1)
    api = FakeSlonAPI(_plan_json())
    with pytest.raises(SlonError, match="limit"):
        run_slon_book(config, generate=True, client=api)
    assert api.image_calls == 0


def test_plan_that_mentions_an_elephant_blocks_generation(tmp_path):
    config = sample_config(tmp_path)
    api = FakeSlonAPI(_plan_json(description="a carved elephant statue beside the gate"))
    run_slon_book(config, dry_run=True, client=api)
    with pytest.raises(SlonError, match="zmínky"):
        run_slon_book(config, generate=True, client=api)
    assert api.image_calls == 0


def test_pdf_only_refuses_missing_pictures_without_api(tmp_path):
    config = sample_config(tmp_path)
    api = FakeSlonAPI(_plan_json())
    run_slon_book(config, dry_run=True, client=api)
    api.fail_images = True
    with pytest.raises(SlonError, match="PDF-only"):
        run_slon_book(config, pdf_only=True, client=api)
    assert api.image_calls == 0


def test_resume_rebuilds_a_saved_scene_without_buying_the_missing_one(tmp_path):
    config = sample_config(tmp_path, puzzle_count=2, max_new=4)
    api = FakeSlonAPI(_plan_json(2))
    run_slon_book(config, generate=True, client=api)
    assert api.image_calls == 3
    first, second = sorted((tmp_path / "book" / "scenes").iterdir())
    (first / "composed.png").unlink()
    (second / "original.png").unlink()
    api.fail_images = True
    report = run_slon_book(config, client=api)
    assert api.image_calls == 3
    assert (first / "composed.png").is_file()
    assert report.reading_pdf is None
    assert "Chybí obrázky" in " ".join(report.notes)


def test_scene_spec_accepts_the_saved_plan_shape():
    scene = SceneSpec.model_validate(
        {
            "id": "stan",
            "title": "Pokladna",
            "description": "A ticket booth",
            "objects": ["booth"],
            "hiding_spots": ["behind the booth"],
            "complexity": "medium",
            "composition": "elevated view",
        }
    )
    assert scene.id == "stan"
