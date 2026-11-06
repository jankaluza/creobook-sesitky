"""Connect-the-dots tests. The OpenAI API is replaced with an in-memory silhouette."""

from __future__ import annotations

import io

import pytest
from PIL import Image, ImageDraw

from creobook.coloring.images import GeneratedImage
from creobook.dots.geometry import (
    _segments_cross,
    geometry_from_png,
    mask_from_png,
    puzzle_svg,
    sample_closed,
    simplify_closed,
    trace_contour,
    validate_geometry,
)
from creobook.dots.models import DotsConfig, DotsError, content_size, expand_mix
from creobook.dots.workflow import run_dots_book
from creobook.validation import check_a4_landscape_sheets, check_media_box, check_page_count


def disk_png(width: int = 200, height: int = 240) -> bytes:
    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    draw.ellipse((36, 48, 164, 196), fill=0)
    draw.polygon([(150, 90), (188, 70), (168, 120)], fill=0)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class FakeDotsAPI:
    def __init__(self, png: bytes) -> None:
        self.png = png
        self.image_calls = 0
        self.fail = False

    def generate_image(self, *, prompt: str, model: str, size: str, quality: str) -> GeneratedImage:
        if self.fail:
            raise AssertionError("image API should not be called")
        self.image_calls += 1
        assert "silhouette" in prompt.lower() or "filled black" in prompt.lower()
        assert size == "1024x1024"
        return GeneratedImage(png=self.png, usage={"output_tokens": 4}, model=model, size=size, quality=quality)


def test_config_starts_at_zero_and_limits_the_maximum(tmp_path):
    with pytest.raises(ValueError):
        DotsConfig(theme="Animals", title="Spojovačky", output_directory=str(tmp_path), min_number=1)
    with pytest.raises(ValueError):
        DotsConfig(theme="Animals", title="Spojovačky", output_directory=str(tmp_path), max_number=9)
    config = DotsConfig(theme="dall-e-3", title="Spojovačky", output_directory=str(tmp_path), image_model="dall-e-3")
    with pytest.raises(DotsError, match="Unsupported image model"):
        config.validate_image_options()
    assert expand_mix("30:2,50:1") == [30, 30, 50]


def test_numbering_contour_and_labels_from_a_silhouette():
    png = disk_png()
    mask = mask_from_png(png)
    contour = trace_contour(mask)
    assert len(contour) > 30
    simplified = simplify_closed(contour, 1.8)
    assert 8 <= len(simplified) < len(contour)
    width, height = content_size("A5")
    geometry = geometry_from_png(
        png,
        max_number=10,
        content_width=width,
        content_height=height,
        page_format="A5",
    )
    numbers = [dot.number for dot in geometry.dots]
    assert numbers == list(range(11))
    assert len({(round(dot.x, 2), round(dot.y, 2)) for dot in geometry.dots}) == 11
    validate_geometry(geometry)
    puzzle = puzzle_svg(geometry, page_width=width, page_height=height, answer=False)
    answer = puzzle_svg(geometry, page_width=width, page_height=height, answer=True)
    assert "<polyline" not in puzzle
    assert "<polyline" in answer
    assert ">0<" in puzzle and ">10<" in puzzle
    assert answer.count("<circle") == puzzle.count("<circle")


def test_sharp_corners_receive_more_dots_than_a_straight_side():
    points: list[tuple[float, float]] = [(float(x), 0.0) for x in range(0, 120, 4)]
    points.append((120.0, 40.0))
    teeth = []
    for index, x in enumerate(range(120, 0, -4)):
        teeth.append((float(x), 80.0 if index % 2 else 40.0))
    points.extend(teeth)
    points.append((0.0, 40.0))
    sampled = sample_closed(points, 40)
    straight = sum(1 for x, y in sampled if y < 8)
    cornered = sum(1 for x, y in sampled if y > 32)
    assert cornered > straight


def test_crossing_segments_are_detected():
    assert _segments_cross((0, 0), (10, 10), (0, 10), (10, 0))
    assert not _segments_cross((0, 0), (1, 0), (1, 0), (1, 1))


def test_generate_caches_pdf_and_regenerate(tmp_path):
    png = disk_png()
    api = FakeDotsAPI(png)
    config = DotsConfig(
        theme="Animals",
        title="Spojovačky",
        puzzle_count=1,
        max_number=10,
        output_directory=str(tmp_path / "book"),
        max_new=4,
    )
    made = run_dots_book(config, generate=True, client=api)
    assert api.image_calls == 1
    assert made.reading_pdf is not None and made.print_pdf is not None
    assert check_page_count(made.reading_pdf, 4).ok
    assert check_media_box(made.reading_pdf, 148, 210).ok
    assert check_a4_landscape_sheets(made.print_pdf).ok
    assert check_page_count(made.print_pdf, 2).ok
    from pypdf import PdfReader

    reading_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(made.reading_pdf)).pages)
    assert "Řešení" not in reading_text
    solutions = tmp_path / "book" / "book-reseni.pdf"
    assert solutions.is_file()
    solution_text = "\n".join(page.extract_text() or "" for page in PdfReader(str(solutions)).pages)
    assert "Liška" in solution_text
    assert made.review_html is not None and "Liška" in made.review_html.read_text(encoding="utf-8")
    slot = tmp_path / "book" / "puzzles"
    puzzle_svg_path = next(slot.rglob("puzzle.svg"))
    answer_svg_path = puzzle_svg_path.with_name("answer.svg")
    assert "<polyline" not in puzzle_svg_path.read_text(encoding="utf-8")
    assert "<polyline" in answer_svg_path.read_text(encoding="utf-8")

    again = run_dots_book(config, generate=True, client=api)
    assert api.image_calls == 1
    assert again.cached_puzzles == 1

    dots = puzzle_svg_path.with_name("dots.json")
    saved = dots.read_bytes()
    dots.unlink()
    api.fail = True
    resumed = run_dots_book(config, client=api)
    assert api.image_calls == 1
    assert resumed.reading_pdf is not None
    assert dots.is_file() and dots.read_bytes() != b""

    api.fail = True
    offline = run_dots_book(config, pdf_only=True, client=api)
    assert api.image_calls == 1
    assert offline.print_pdf is not None

    api.fail = False
    regenerated = run_dots_book(config, regenerate_puzzle=1, client=api)
    assert api.image_calls == 2
    assert regenerated.new_images == 1
    assert saved


def test_max_new_stops_before_any_image_call(tmp_path):
    api = FakeDotsAPI(disk_png())
    config = DotsConfig(
        theme="Sea",
        title="Moře",
        puzzle_count=2,
        max_number=10,
        output_directory=str(tmp_path / "book"),
        max_new=1,
    )
    with pytest.raises(DotsError, match="limit"):
        run_dots_book(config, generate=True, client=api)
    assert api.image_calls == 0


def test_pdf_only_refuses_missing_geometry(tmp_path):
    api = FakeDotsAPI(disk_png())
    config = DotsConfig(
        theme="Nature",
        title="Příroda",
        puzzle_count=1,
        max_number=10,
        output_directory=str(tmp_path / "book"),
    )
    run_dots_book(config, dry_run=True, client=api)
    assert api.image_calls == 0
    api.fail = True
    with pytest.raises(DotsError, match="PDF-only"):
        run_dots_book(config, pdf_only=True, client=api)
    assert api.image_calls == 0


def test_labels_that_cannot_fit_are_rejected():
    with pytest.raises(DotsError):
        geometry_from_png(
            disk_png(),
            max_number=10,
            content_width=22,
            content_height=24,
            page_format="A6",
        )
