"""Plan, cache, generate, and bind a coloring booklet. Paid calls stay behind --generate."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from creobook.coloring.booklet import compile_coloring_pdfs, filled_illustration_count
from creobook.coloring.cache import (
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_text,
    illustration_dir,
    read_meta,
)
from creobook.coloring.images import GeneratedImage
from creobook.coloring.models import (
    PAGE_FORMATS,
    ColoringConfig,
    ColoringError,
    Illustration,
    IllustrationPlan,
)
from creobook.coloring.planner import apply_copyright_flags, parse_plan, request_plan, validate_plan
from creobook.coloring.process import assess, open_png, png_bytes, process_line_art
from creobook.coloring.prompts import image_prompt
from creobook.coloring.review import write_review
from creobook.theme import project_root


@dataclass
class RunReport:
    output_dir: Path
    plan_path: Path
    reading_pdf: Path | None = None
    print_pdf: Path | None = None
    review_html: Path | None = None
    notes: list[str] = field(default_factory=list)
    new_images: int = 0
    cached_images: int = 0
    api_calls: int = 0


def slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_text).strip("-").lower()
    return slug or "omalovanky"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _price_table() -> dict[str, Any] | None:
    path = project_root() / "config" / "coloring" / "pricing.json"
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def estimate_note(config: ColoringConfig, new_images: int) -> str:
    table = _price_table()
    per_image = None
    currency = "USD"
    if table:
        currency = str(table.get("currency") or currency)
        per_image = (
            (table.get("per_image") or {})
            .get(config.image_model, {})
            .get(config.image_quality)
        )
    if not isinstance(per_image, (int, float)):
        return (
            f"Nové obrázky: {new_images}. Model {config.image_model}, kvalita {config.image_quality}. "
            "Odhad ceny není nakonfigurovaný."
        )
    total = new_images * float(per_image)
    return (
        f"Nové obrázky: {new_images}. Odhad {total:.2f} {currency} "
        f"({config.image_model}, {config.image_quality})."
    )


def _slot(root: Path, index: int, item: Illustration) -> Path:
    return illustration_dir(root, index, item.id)


def _prompt_for(config: ColoringConfig, item: Illustration) -> str:
    return image_prompt(item, config.age_group)


def _is_cached(directory: Path, prompt: str, config: ColoringConfig) -> bool:
    meta = read_meta(directory)
    print_png = directory / "print.png"
    if meta is None or not print_png.is_file():
        return False
    return (
        meta.get("status") == "processed"
        and meta.get("prompt") == prompt
        and meta.get("model") == config.image_model
        and meta.get("quality") == config.image_quality
        and meta.get("size") == config.image_size
    )


def _max_pixels(config: ColoringConfig) -> tuple[int, int]:
    spec = PAGE_FORMATS[config.page_format]
    usable_w = spec["width_mm"] - spec["margin_inside_mm"] - spec["margin_outside_mm"]
    usable_h = spec["height_mm"] - spec["margin_top_mm"] - spec["margin_bottom_mm"]
    scale = 300 / 25.4
    return (max(1, int(usable_w * scale)), max(1, int(usable_h * scale)))


def _process_original(directory: Path, config: ColoringConfig) -> list[str]:
    image = process_line_art(
        open_png((directory / "original.png").read_bytes()),
        config.process,
        max_px=_max_pixels(config),
    )
    report = assess(image)
    atomic_write_bytes(directory / "print.png", png_bytes(image))
    meta = read_meta(directory) or {}
    meta["status"] = "processed"
    meta["warnings"] = report.warnings
    meta["width"] = report.width
    meta["height"] = report.height
    meta["processed_at"] = _now()
    atomic_write_json(directory / "meta.json", meta)
    thumb = image.copy()
    thumb.thumbnail((280, 400), Image.Resampling.LANCZOS)
    atomic_write_bytes(directory / "thumb.png", png_bytes(thumb))
    return report.warnings


def _write_generation(
    directory: Path,
    *,
    item: Illustration,
    prompt: str,
    generated: GeneratedImage,
    config: ColoringConfig,
) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    atomic_write_text(directory / "prompt.txt", prompt + "\n")
    atomic_write_json(
        directory / "meta.json",
        {
            "id": item.id,
            "title": item.title,
            "status": "original",
            "prompt": prompt,
            "model": generated.model or config.image_model,
            "quality": generated.quality or config.image_quality,
            "size": generated.size or config.image_size,
            "created_at": _now(),
            "usage": generated.usage,
        },
    )
    atomic_write_bytes(directory / "original.png", generated.png)
    return _process_original(directory, config)


def _load_plan(path: Path, config: ColoringConfig) -> IllustrationPlan:
    plan = IllustrationPlan.model_validate(json.loads(path.read_text(encoding="utf-8")))
    apply_copyright_flags(plan, config)
    validate_plan(plan, config)
    return plan


def _blocked(plan: IllustrationPlan) -> list[str]:
    hits = list(plan.theme_flags)
    for item in plan.illustrations:
        for flag in item.copyright_flags:
            hits.append(f"{item.id}: {flag}")
    return hits


def _review_rows(root: Path, plan: IllustrationPlan) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, item in enumerate(plan.illustrations, start=1):
        directory = _slot(root, index, item)
        meta = read_meta(directory) or {}
        thumb = directory / "thumb.png"
        relative = ""
        if thumb.is_file():
            relative = thumb.relative_to(root).as_posix()
        warnings = meta.get("warnings") or item.copyright_flags
        rows.append(
            {
                "number": str(index),
                "title": item.title,
                "status": str(meta.get("status") or "missing"),
                "warnings": ", ".join(warnings),
                "thumb": relative,
            }
        )
    return rows


def run_coloring_book(
    config: ColoringConfig,
    *,
    generate: bool = False,
    pdf_only: bool = False,
    dry_run: bool = False,
    regenerate_image: int | None = None,
    force_regenerate: bool = False,
    client: Any = None,
) -> RunReport:
    config.validate_image_options()
    fill_note = None
    if not config.single_sided:
        filled = filled_illustration_count(config.illustration_count)
        if filled != config.illustration_count:
            fill_note = (
                f"Počet ilustrací {config.illustration_count} by v sešitě nechal prázdné stránky. "
                f"Plán bude mít {filled} ilustrací ({filled + 1} stran včetně obálky)."
            )
            if filled > config.max_new:
                fill_note += f" Pro vygenerování všech zvedni --max-new alespoň na {filled}."
            config = config.model_copy(update={"illustration_count": filled})
    if pdf_only and (generate or dry_run or regenerate_image or force_regenerate):
        raise ColoringError("--pdf-only does not call OpenAI and ignores generation flags")
    if dry_run and generate:
        raise ColoringError("Choose either --dry-run or --generate")
    if force_regenerate and not generate:
        raise ColoringError("--force-regenerate needs --generate")

    output_dir = Path(config.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    config.output_directory = str(output_dir.resolve())
    atomic_write_json(output_dir / "config.json", config.model_dump(mode="json"))

    plan_path = output_dir / "plan.json"
    report = RunReport(output_dir=output_dir, plan_path=plan_path)
    if fill_note:
        report.notes.append(fill_note)

    if plan_path.is_file():
        plan = _load_plan(plan_path, config)
        atomic_write_json(plan_path, plan.model_dump(mode="json"))
        report.notes.append(f"Plán načten z {plan_path.name}")
    elif pdf_only:
        raise ColoringError("PDF-only potřebuje uložený plan.json")
    else:
        if client is None:
            from creobook.coloring.images import OpenAIColoringClient

            client = OpenAIColoringClient()
        plan = request_plan(
            config,
            lambda prompt: client.complete_text(prompt, model=config.text_model),
        )
        report.api_calls += 1
        atomic_write_json(plan_path, plan.model_dump(mode="json"))
        report.notes.append("Plán uložen. Lze ho ručně upravit před generováním obrázků.")

    blocked = _blocked(plan)
    if blocked:
        report.notes.append(
            "Autorská kontrola je jen pojistka, ne právní posudek. Nalezeno: " + "; ".join(blocked)
        )

    wanted: list[tuple[int, Illustration, Path, str]] = []
    for index, item in enumerate(plan.illustrations, start=1):
        directory = _slot(output_dir, index, item)
        prompt = _prompt_for(config, item)
        selected = regenerate_image == index or force_regenerate
        if selected or not _is_cached(directory, prompt, config):
            wanted.append((index, item, directory, prompt))
        else:
            report.cached_images += 1

    if regenerate_image is not None and not any(index == regenerate_image for index, *_ in wanted):
        if not 1 <= regenerate_image <= len(plan.illustrations):
            raise ColoringError(
                f"Obrázek {regenerate_image} v plánu není (1–{len(plan.illustrations)})"
            )

    needs_api = []
    local_only = []
    for index, item, directory, prompt in wanted:
        original = directory / "original.png"
        meta = read_meta(directory)
        same_request = (
            meta is not None
            and meta.get("prompt") == prompt
            and meta.get("model") == config.image_model
            and meta.get("quality") == config.image_quality
            and meta.get("size") == config.image_size
            and original.is_file()
            and not force_regenerate
            and regenerate_image != index
        )
        if same_request:
            local_only.append((index, item, directory, prompt))
        else:
            needs_api.append((index, item, directory, prompt))

    report.new_images = len(needs_api)
    report.notes.append(
        f"V mezipaměti: {report.cached_images}. Nově generovat: {report.new_images}. "
        f"Znovu zpracovat místně: {len(local_only)}."
    )
    report.notes.append(estimate_note(config, report.new_images))

    if dry_run:
        report.notes.append("Dry-run: obrázky se negenerují.")
        return report

    if blocked and (needs_api or regenerate_image or force_regenerate) and not pdf_only:
        raise ColoringError(
            "Generování je zastavené, dokud z plánu nezmizí označené chráněné odkazy."
        )

    if pdf_only and (needs_api or local_only):
        missing = [str(index) for index, *_rest in (*needs_api, *local_only)]
        raise ColoringError("PDF-only nemá všechny zpracované obrázky: " + ", ".join(missing))

    for index, _item, directory, _prompt in local_only:
        warnings = _process_original(directory, config)
        report.notes.append(f"Obrázek {index} zpracován z uloženého originálu. {'; '.join(warnings)}")

    if needs_api and not generate and regenerate_image is None:
        report.notes.append("Chybí obrázky. Placené generování spustí až --generate.")
        return report

    if regenerate_image is not None and not generate:
        generate = True

    if needs_api and generate:
        if len(needs_api) > config.max_new:
            raise ColoringError(
                f"Je potřeba {len(needs_api)} nových obrázků, limit je {config.max_new}. "
                "Zvyš --max-new, nebo generuj po dávkách."
            )
        if client is None:
            from creobook.coloring.images import OpenAIColoringClient

            client = OpenAIColoringClient()
        for index, item, directory, prompt in needs_api:
            generated = client.generate_image(
                prompt=prompt,
                model=config.image_model,
                size=config.image_size,
                quality=config.image_quality,
            )
            report.api_calls += 1
            warnings = _write_generation(
                directory,
                item=item,
                prompt=prompt,
                generated=generated,
                config=config,
            )
            usage = generated.usage
            usage_note = ""
            if usage:
                usage_note = " Usage: " + ", ".join(f"{key}={value}" for key, value in usage.items())
            report.notes.append(
                f"Vygenerován obrázek {index} ({item.title}). {'; '.join(warnings)}{usage_note}"
            )

    image_files: dict[str, Path] = {}
    for index, item in enumerate(plan.illustrations, start=1):
        print_png = _slot(output_dir, index, item) / "print.png"
        if not print_png.is_file():
            report.notes.append("PDF se neskládá, dokud nejsou všechny obrázky zpracované.")
            report.review_html = write_review(output_dir / "review.html", _review_rows(output_dir, plan))
            return report
        image_files[item.id] = print_png

    pdfs = compile_coloring_pdfs(config, plan.illustrations, image_files, output_dir)
    report.reading_pdf = pdfs["reading"]
    report.print_pdf = pdfs["print"]
    report.review_html = write_review(output_dir / "review.html", _review_rows(output_dir, plan))
    report.notes.append(f"Čtení: {report.reading_pdf.name}")
    report.notes.append(f"Tisk: {report.print_pdf.name}")
    return report
