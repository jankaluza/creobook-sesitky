"""Coloring booklet tests. The OpenAI API is replaced with an in-memory fake."""

from __future__ import annotations

import json

import pytest
from PIL import Image

from creobook.coloring.booklet import filled_illustration_count, physical_reverse, reading_pages
from creobook.coloring.images import RetryableImageError, call_with_retry, require_api_key
from creobook.coloring.models import ColoringConfig, ColoringError, Illustration, IllustrationPlan
from creobook.coloring.planner import parse_plan
from creobook.coloring.process import ProcessSettings, assess, open_png, process_line_art
from creobook.coloring.prompts import image_prompt, plan_prompt
from creobook.coloring.workflow import run_coloring_book
from creobook.validation import check_a4_landscape_sheets, check_media_box, check_page_count
from tests.coloring.conftest import FakeColoringAPI, illustration, line_png, sample_config


def _plan_json(count: int = 1) -> str:
    plan = IllustrationPlan(
        theme="Forest animals",
        age_group="6-8",
        illustrations=[illustration(index) for index in range(1, count + 1)],
    )
    return plan.model_dump_json()


def test_config_rejects_unknown_model_and_landscape_size(tmp_path):
    config = sample_config(tmp_path, image_model="dall-e-3")
    with pytest.raises(ColoringError, match="Unsupported image model"):
        config.validate_image_options()
    portrait = sample_config(tmp_path, image_size="1536x1024")
    with pytest.raises(ColoringError, match="Unsupported size"):
        portrait.validate_image_options()
    with pytest.raises(ValueError):
        sample_config(tmp_path, age_group="1-2", illustration_count=1)


def test_plan_parsing_flags_and_prompt_text(tmp_path):
    config = sample_config(tmp_path, illustration_count=2)
    prompt = plan_prompt(config)
    assert "Forest animals" in prompt
    assert "copyrighted" in prompt
    assert "2" in prompt
    plan = parse_plan(_plan_json(2), config)
    assert [item.id for item in plan.illustrations] == ["animal-1", "animal-2"]

    copied = json.loads(_plan_json(2))
    copied["illustrations"][1]["description"] = copied["illustrations"][0]["description"]
    with pytest.raises(ColoringError, match="almost the same"):
        parse_plan(json.dumps(copied), config)

    flagged = json.loads(_plan_json(2))
    flagged["illustrations"][0]["description"] = "Pikachu standing alone in an empty snowy clearing"
    parsed = parse_plan(json.dumps(flagged), config)
    assert "pikachu" in parsed.illustrations[0].copyright_flags

    drawn = image_prompt(plan.illustrations[0], "6-8")
    assert "Pure black outlines" in drawn
    assert "Medium-weight" in drawn
    assert "smiling fox" in drawn
    thick = image_prompt(plan.illustrations[0], "3-5")
    assert "Very thick" in thick


def test_plan_request_does_not_send_temperature():
    from creobook.coloring.images import OpenAIColoringClient

    client = OpenAIColoringClient(api_key="sk-test-not-used")
    captured: dict = {}

    class _Responses:
        def create(self, **kwargs):
            captured.update(kwargs)

            class _Response:
                output_text = '{"ok": true}'

            return _Response()

    client._client.responses = _Responses()
    assert client.complete_text("plan", model="gpt-6-astra") == '{"ok": true}'
    assert "temperature" not in captured


def test_retry_backoff_and_missing_key(monkeypatch):
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RetryableImageError("rate limit")
        return b"ok"

    sleeps: list[float] = []
    assert call_with_retry(flaky, attempts=4, sleeper=sleeps.append) == b"ok"
    assert sleeps == [1, 2]

    def always():
        raise RetryableImageError("timeout")

    with pytest.raises(RetryableImageError):
        call_with_retry(always, attempts=3, sleeper=lambda _delay: None)

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ColoringError, match="OPENAI_API_KEY"):
        require_api_key()


def test_image_processing_keeps_lines_and_drops_specks():
    source = open_png(line_png())
    noisy = source.copy()
    noisy.putpixel((2, 2), 0)
    processed = process_line_art(noisy, ProcessSettings(min_speck=4), max_px=(200, 300))
    assert processed.size == source.size
    assert processed.getpixel((2, 2)) == 255
    assert processed.getpixel((8, 8)) == 0
    report = assess(processed)
    assert report.warnings == []
    assert report.white_ratio > 0.8

    big = Image.new("L", (40, 80), 255)
    shrunk = process_line_art(big, max_px=(20, 40))
    assert shrunk.size == (20, 40)


def test_dry_run_plans_without_images_and_reuses_the_plan(tmp_path):
    config = sample_config(tmp_path, illustration_count=3)
    api = FakeColoringAPI(_plan_json(3))
    first = run_coloring_book(config, dry_run=True, client=api)
    assert api.text_calls == 1
    assert api.image_calls == 0
    assert first.plan_path.is_file()
    assert not list((tmp_path / "book").glob("illustrations/**/*.png"))
    second = run_coloring_book(config, dry_run=True, client=api)
    assert api.text_calls == 1
    assert "Dry-run" in " ".join(second.notes)


def test_short_booklet_asks_for_more_illustrations_instead_of_blank_pages(tmp_path):
    assert filled_illustration_count(16) == 19
    assert filled_illustration_count(15) == 15
    config = sample_config(tmp_path, illustration_count=1)
    api = FakeColoringAPI(_plan_json(3))
    report = run_coloring_book(config, dry_run=True, client=api)
    saved = json.loads((tmp_path / "book" / "config.json").read_text(encoding="utf-8"))
    plan = json.loads(report.plan_path.read_text(encoding="utf-8"))
    assert saved["illustration_count"] == 3
    assert len(plan["illustrations"]) == 3
    assert "prázdné stránky" in " ".join(report.notes)

    pages = reading_pages(
        sample_config(tmp_path, illustration_count=19),
        [illustration(index) for index in range(1, 20)],
    )
    assert len(pages) == 20
    assert all(page["kind"] != "blank" for page in pages)
    with pytest.raises(ColoringError, match="prázdné stránky"):
        reading_pages(config, [illustration(1)])


def test_generate_caches_regenerate_resume_and_pdf_only(tmp_path):
    config = sample_config(tmp_path, illustration_count=3, max_new=4)
    api = FakeColoringAPI(_plan_json(3))
    made = run_coloring_book(config, generate=True, client=api)
    assert api.image_calls == 3
    assert made.reading_pdf is not None and made.reading_pdf.is_file()
    assert made.print_pdf is not None and made.print_pdf.is_file()
    assert check_page_count(made.reading_pdf, 4).ok
    assert check_media_box(made.reading_pdf, 148, 210).ok
    assert check_a4_landscape_sheets(made.print_pdf).ok
    assert check_page_count(made.print_pdf, 2).ok
    assert made.review_html is not None and made.review_html.is_file()
    review = (tmp_path / "book" / "review.html").read_text(encoding="utf-8")
    assert "Zvíře 1" in review

    again = run_coloring_book(config, generate=True, client=api)
    assert api.image_calls == 3
    assert again.cached_images == 3

    slot = next((tmp_path / "book" / "illustrations").iterdir())
    (slot / "print.png").unlink()
    (slot / "thumb.png").unlink()
    api.fail_images = True
    resumed = run_coloring_book(config, client=api)
    assert api.image_calls == 3
    assert (slot / "print.png").is_file()
    assert resumed.reading_pdf is not None

    api.fail_images = True
    offline = run_coloring_book(config, pdf_only=True, client=api)
    assert api.image_calls == 3
    assert offline.print_pdf is not None

    api.fail_images = False
    regenerated = run_coloring_book(config, regenerate_image=1, client=api)
    assert api.image_calls == 4
    assert regenerated.new_images == 1


def test_max_new_stops_before_any_image_call(tmp_path):
    config = sample_config(tmp_path, illustration_count=3, max_new=1)
    api = FakeColoringAPI(_plan_json(3))
    with pytest.raises(ColoringError, match="limit"):
        run_coloring_book(config, generate=True, client=api)
    assert api.image_calls == 0


def test_copyright_flag_blocks_generation(tmp_path):
    config = sample_config(tmp_path, illustration_count=3)
    raw = json.loads(_plan_json(3))
    raw["illustrations"][0]["subjects"] = ["Pikachu"]
    api = FakeColoringAPI(json.dumps(raw))
    run_coloring_book(config, dry_run=True, client=api)
    with pytest.raises(ColoringError, match="chráněné"):
        run_coloring_book(config, generate=True, client=api)
    assert api.image_calls == 0


def test_single_sided_backs_are_blank_and_a6_sheet(tmp_path):
    config = sample_config(tmp_path, illustration_count=2, single_sided=True)
    pages = reading_pages(
        config,
        [illustration(1), illustration(2)],
    )
    assert len(pages) % 4 == 0
    assert pages[0]["kind"] == "cover"
    for number, page in enumerate(pages, start=1):
        if page["kind"] == "blank":
            continue
        reverse = physical_reverse(number, len(pages))
        assert pages[reverse - 1]["kind"] == "blank"

    api = FakeColoringAPI(_plan_json(3))
    a6 = sample_config(tmp_path / "a6", illustration_count=3, page_format="A6", single_sided=False)
    made = run_coloring_book(a6, generate=True, client=api)
    assert made.reading_pdf is not None and made.print_pdf is not None
    assert check_media_box(made.reading_pdf, 105, 148).ok
    assert check_media_box(made.print_pdf, 210, 148).ok
    assert check_page_count(made.print_pdf, 2).ok


def test_pdf_only_refuses_missing_images_without_api(tmp_path):
    config = sample_config(tmp_path, illustration_count=3)
    api = FakeColoringAPI(_plan_json(3))
    run_coloring_book(config, dry_run=True, client=api)
    api.fail_images = True
    with pytest.raises(ColoringError, match="PDF-only"):
        run_coloring_book(config, pdf_only=True, client=api)
    assert api.image_calls == 0
