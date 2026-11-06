"""Plan, cache, compose, and bind a Najdi slona booklet. Image calls stay behind --generate."""

from __future__ import annotations

import io
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from creobook.coloring.cache import atomic_write_bytes, atomic_write_json, atomic_write_text, read_meta
from creobook.coloring.models import PAGE_FORMATS
from creobook.coloring.process import assess, open_png, process_line_art
from creobook.slon.booklet import PuzzleView, compile_slon_pdfs
from creobook.slon.composite import (
    composite_elephant,
    elephant_view,
    find_open_center,
    slice_elephant,
    draw_solution,
    placement_warnings,
    prepare_elephant,
)
from creobook.slon.models import SCALES, Placement, SceneSpec, SlonConfig, SlonError
from creobook.slon.planner import copyright_hits, elephant_hits, parse_plan, request_plan
from creobook.slon.prompts import elephant_prompt, scene_prompt
from creobook.slon.review import write_review


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


def run_slon_book(
    config: SlonConfig,
    *,
    generate: bool = False,
    pdf_only: bool = False,
    dry_run: bool = False,
    regenerate_scene: int | None = None,
    regenerate_elephant: bool = False,
    force_regenerate: bool = False,
    move_elephant: int | None = None,
    position: tuple[float, float] | None = None,
    client: Any = None,
) -> RunReport:
    config.validate_image_options()
    if pdf_only and (generate or dry_run or regenerate_scene or regenerate_elephant or force_regenerate):
        raise SlonError("--pdf-only does not call OpenAI and ignores generation flags")
    if dry_run and (generate or move_elephant is not None):
        raise SlonError("Choose either --dry-run or a generation or placement change")
    if force_regenerate and not generate:
        raise SlonError("--force-regenerate needs --generate")
    if (move_elephant is None) != (position is None):
        raise SlonError("--move-elephant needs --position x,y")
    if regenerate_scene is not None and not generate:
        generate = True
    if regenerate_elephant and not generate:
        generate = True

    output_dir = Path(config.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    config.output_directory = str(output_dir.resolve())
    atomic_write_json(output_dir / "config.json", config.model_dump(mode="json"))

    plan_path = output_dir / "plan.json"
    report = RunReport(output_dir=output_dir, plan_path=plan_path)
    scenes = _load_or_plan(config, plan_path, report, pdf_only=pdf_only, client=client)
    if client is None and report.api_calls:
        from creobook.coloring.images import OpenAIColoringClient

        client = OpenAIColoringClient()

    blocked = copyright_hits(config, scenes)
    named = elephant_hits(scenes)
    if blocked:
        report.notes.append(
            "Autorská kontrola je jen pojistka, ne právní posudek. Nalezeno: " + "; ".join(blocked)
        )
    if named:
        report.notes.append(
            "Plán zmiňuje slona ve scénách "
            + ", ".join(named)
            + ". Uprav plan.json, scéna ho nesmí kreslit."
        )
    if dry_run:
        report.notes.append("Dry-run: obrázky se negenerují.")
        return report
    if regenerate_scene is not None and not 1 <= regenerate_scene <= len(scenes):
        raise SlonError(f"Scéna {regenerate_scene} v plánu není (1–{len(scenes)})")
    if move_elephant is not None and not 1 <= move_elephant <= len(scenes):
        raise SlonError(f"Scéna {move_elephant} v plánu není (1–{len(scenes)})")
    if (blocked or named) and generate and not pdf_only:
        raise SlonError("Generování je zastavené, dokud z plánu tyto zmínky nezmizí.")

    elephant_dir = output_dir / "elephant"
    elephant_mode = _elephant_mode(
        config,
        elephant_dir,
        regenerate=regenerate_elephant or force_regenerate,
    )
    levels = config.page_difficulties()
    scene_modes = [
        _scene_mode(
            config,
            scene,
            _scene_dir(output_dir, index, scene),
            difficulty=levels[index - 1],
            regenerate=force_regenerate or regenerate_scene == index,
        )
        for index, scene in enumerate(scenes, start=1)
    ]
    api_count = int(elephant_mode == "api") + sum(mode == "api" for mode in scene_modes)
    local_count = int(elephant_mode == "local") + sum(mode == "local" for mode in scene_modes)
    report.new_images = api_count
    report.cached_images = sum(mode == "cached" for mode in scene_modes) + int(elephant_mode == "cached")
    report.notes.append(
        f"V mezipaměti: {report.cached_images}. Nově generovat: {report.new_images}. "
        f"Znovu zpracovat místně: {local_count}."
    )

    missing_numbers = [str(index) for index, mode in enumerate(scene_modes, start=1) if mode != "cached"]
    if elephant_mode != "cached":
        missing_numbers.insert(0, "slon")
    if pdf_only and missing_numbers and move_elephant is None:
        raise SlonError("PDF-only nemá všechny složené obrázky: " + ", ".join(missing_numbers))
    if pdf_only and move_elephant is not None and any(mode == "api" for mode in scene_modes):
        raise SlonError("PDF-only nemá podklady pro přesun slona.")
    if generate and api_count > config.max_new:
        raise SlonError(
            f"Je potřeba {api_count} nových obrázků, limit je {config.max_new}. "
            "Zvyš --max-new, nebo generuj po jedné scéně."
        )
    if api_count and not generate:
        report.notes.append("Chybí obrázky. Placené generování spustí až --generate.")

    if elephant_mode == "api" and generate:
        _generate_elephant(config, elephant_dir, client, report)
    elif elephant_mode == "local":
        _process_elephant(elephant_dir)
        report.notes.append("Slon zpracován z uloženého originálu.")
    if not (elephant_dir / "asset.png").is_file():
        report.notes.append("PDF se neskládá, dokud není hotová postava slona.")
        _write_review(output_dir, scenes, report)
        return report
    elephant = Image.open(elephant_dir / "asset.png")

    used: list[tuple[float, float]] = []
    puzzles: list[PuzzleView] = []
    for index, scene in enumerate(scenes, start=1):
        directory = _scene_dir(output_dir, index, scene)
        mode = scene_modes[index - 1]
        level = levels[index - 1]
        if mode == "api":
            if not generate:
                continue
            _generate_scene(config, scene, directory, client, report, index, level)
        elif mode == "local" or not (directory / "processed.png").is_file():
            if (directory / "original.png").is_file():
                _process_scene(directory, config)
                report.notes.append(f"Scéna {index} zpracována z uloženého originálu.")
        if not (directory / "processed.png").is_file():
            continue
        scene_image = Image.open(directory / "processed.png")
        part_name, flip = elephant_view(index, level)
        part = slice_elephant(elephant, part_name, flip)
        shown = f"{part_name}-flip" if flip else part_name
        placement, clear = _placement_for(
            config, directory, scene, scene_image, part, index, used, level
        )
        if move_elephant == index and position is not None:
            placement = Placement(
                scene_id=scene.id,
                cx=position[0],
                cy=position[1],
                scale=placement.scale,
                rotation=placement.rotation,
                manual=True,
            )
            placement.clamped()
            clear = True
        view = _compose(
            config,
            scene,
            index,
            directory,
            part,
            placement,
            manual=placement.manual,
            clear=clear,
            difficulty=level,
            occlusion=shown,
        )
        used.append((view.placement.cx, view.placement.cy))
        puzzles.append(view)
        if view.warnings:
            report.notes.append(f"Scéna {index}: {'; '.join(view.warnings)}")

    if len(puzzles) != len(scenes):
        report.notes.append("PDF se neskládá, dokud nejsou všechny scény zpracované.")
        _write_review(output_dir, scenes, report)
        return report

    image_files = {}
    for puzzle in puzzles:
        directory = _scene_dir(output_dir, puzzle.index, _scene_of(scenes, puzzle.scene_id))
        image_files[puzzle.scene_id] = directory / "composed.png"
        image_files[f"{puzzle.scene_id}-ref"] = directory / "reference.png"
    pdfs = compile_slon_pdfs(
        config,
        puzzles,
        image_files,
        elephant_dir / "asset.png",
        output_dir,
    )
    report.reading_pdf = pdfs["reading"]
    report.print_pdf = pdfs["print"]
    _write_review(output_dir, scenes, report)
    sheet = "A4" if config.page_format == "A5" else "A5"
    report.notes.append(f"Čtení: {report.reading_pdf.name}")
    report.notes.append(
        f"Tisk: {report.print_pdf.name} — {sheet} na šířku, oboustranně, přes krátkou hranu, 100 %."
    )
    report.notes.append(
        "Kontrola nepozná, jestli je ve scéně ještě jeden slon, ani jak těžké je ho najít. "
        "Prohlédni review.html."
    )
    return report


def _scene_of(scenes: list[SceneSpec], scene_id: str) -> SceneSpec:
    for scene in scenes:
        if scene.id == scene_id:
            return scene
    raise SlonError(f"Unknown scene {scene_id}")


def _load_or_plan(
    config: SlonConfig,
    plan_path: Path,
    report: RunReport,
    *,
    pdf_only: bool,
    client: Any,
) -> list[SceneSpec]:
    if plan_path.is_file():
        scenes = parse_plan(plan_path.read_text(encoding="utf-8"), config)
        atomic_write_json(plan_path, {"theme": config.theme, "scenes": [scene.model_dump() for scene in scenes]})
        report.notes.append(f"Plán načten z {plan_path.name}")
        return scenes
    if pdf_only:
        raise SlonError("PDF-only potřebuje uložený plan.json")
    if client is None:
        from creobook.coloring.images import OpenAIColoringClient

        client = OpenAIColoringClient()
    scenes = request_plan(config, lambda prompt: client.complete_text(prompt, model=config.text_model))
    report.api_calls += 1
    atomic_write_json(plan_path, {"theme": config.theme, "scenes": [scene.model_dump() for scene in scenes]})
    report.notes.append("Plán uložen. Lze ho ručně upravit před generováním obrázků.")
    return scenes


def _scene_dir(root: Path, index: int, scene: SceneSpec) -> Path:
    return root / "scenes" / f"{index:02d}-{scene.id}"


def _matches(meta: dict[str, Any] | None, *, prompt: str, model: str, quality: str, size: str, background: str) -> bool:
    return bool(
        meta
        and meta.get("prompt") == prompt
        and meta.get("model") == model
        and meta.get("quality") == quality
        and meta.get("size") == size
        and meta.get("background") == background
    )


def _elephant_mode(config: SlonConfig, directory: Path, *, regenerate: bool) -> str:
    prompt = elephant_prompt(config)
    meta = read_meta(directory)
    original = directory / "original.png"
    asset = directory / "asset.png"
    if regenerate or not _matches(
        meta,
        prompt=prompt,
        model=config.image_model,
        quality=config.image_quality,
        size=config.image_size,
        background="transparent",
    ):
        return "api"
    if not original.is_file():
        return "api"
    if not asset.is_file():
        return "local"
    return "cached"


def _scene_mode(
    config: SlonConfig,
    scene: SceneSpec,
    directory: Path,
    *,
    difficulty: str,
    regenerate: bool,
) -> str:
    prompt = scene_prompt(config, scene, difficulty)
    meta = read_meta(directory)
    if regenerate or not _matches(
        meta,
        prompt=prompt,
        model=config.image_model,
        quality=config.image_quality,
        size=config.image_size,
        background="opaque",
    ):
        return "api"
    if not (directory / "original.png").is_file():
        return "api"
    if not (directory / "composed.png").is_file() or not (directory / "processed.png").is_file():
        return "local"
    saved = _read_placement(directory, scene.id)
    if saved is None or (not saved.manual and abs(saved.scale - SCALES[difficulty]) > 0.001):
        return "local"
    return "cached"


def _read_placement(directory: Path, scene_id: str) -> Placement | None:
    path = directory / "placement.json"
    if not path.is_file():
        return None
    placement = Placement.model_validate_json(path.read_text(encoding="utf-8"))
    if placement.scene_id != scene_id:
        return None
    return placement


def _placement_for(
    config: SlonConfig,
    directory: Path,
    scene: SceneSpec,
    scene_image: Image.Image,
    elephant: Image.Image,
    index: int,
    used: list[tuple[float, float]],
    difficulty: str,
) -> tuple[Placement, bool]:
    saved = _read_placement(directory, scene.id)
    if saved is not None and saved.manual:
        return saved, True
    cx, cy, clear = find_open_center(
        scene_image,
        elephant,
        scale=SCALES[difficulty],
        used=used,
        index=index - 1,
    )
    return Placement(scene_id=scene.id, cx=cx, cy=cy, scale=SCALES[difficulty]), clear


def _compose(
    config: SlonConfig,
    scene: SceneSpec,
    index: int,
    directory: Path,
    elephant: Image.Image,
    placement: Placement,
    *,
    manual: bool,
    clear: bool = True,
    difficulty: str = "medium",
    occlusion: str | None = None,
) -> PuzzleView:
    scene_image = Image.open(directory / "processed.png")
    composed, stored = composite_elephant(
        scene_image,
        elephant,
        scene_id=scene.id,
        cx=placement.cx,
        cy=placement.cy,
        scale=placement.scale,
        rotation=placement.rotation,
        manual=manual,
        allow_nudge=not manual,
        occlusion=occlusion,
    )
    _write_png(directory / "reference.png", elephant)
    _write_png(directory / "composed.png", composed)
    solution = draw_solution(composed, stored)
    _write_png(directory / "solution.png", solution)
    atomic_write_json(directory / "placement.json", stored.model_dump(mode="json"))
    warnings = assess(composed).warnings + placement_warnings(stored, difficulty)
    if not clear:
        warnings.append("ve scéně není čistá mezera, slon překrývá kresbu")
    meta = read_meta(directory) or {}
    meta["warnings"] = warnings
    meta["placement"] = stored.model_dump(mode="json")
    atomic_write_json(directory / "meta.json", meta)
    return PuzzleView(
        index=index,
        scene_id=scene.id,
        placement=stored,
        width=composed.width,
        height=composed.height,
        warnings=warnings,
        difficulty=difficulty,
        reference=f"slon-images/{index:02d}-{scene.id}-ref.png",
    )


def _generate_elephant(config: SlonConfig, directory: Path, client: Any, report: RunReport) -> None:
    if client is None:
        from creobook.coloring.images import OpenAIColoringClient

        client = OpenAIColoringClient()
    prompt = elephant_prompt(config)
    generated = client.generate_image(
        prompt=prompt,
        model=config.image_model,
        size=config.image_size,
        quality=config.image_quality,
        background="transparent",
    )
    report.api_calls += 1
    _store_original(
        directory,
        png=generated.png,
        prompt=prompt,
        config=config,
        background="transparent",
        usage=generated.usage,
    )
    _process_elephant(directory)
    report.notes.append("Vygenerována postava slona.")


def _process_elephant(directory: Path) -> None:
    prepared = prepare_elephant(open_png((directory / "original.png").read_bytes()))
    _write_png(directory / "asset.png", prepared)
    opaque = prepared.getchannel("A").histogram()[255]
    total = prepared.width * prepared.height
    meta = read_meta(directory) or {}
    warnings: list[str] = []
    if total and opaque / total < 0.02:
        warnings.append("elephant silhouette looks incomplete")
    meta["warnings"] = warnings
    meta["status"] = "ready"
    atomic_write_json(directory / "meta.json", meta)


def _generate_scene(
    config: SlonConfig,
    scene: SceneSpec,
    directory: Path,
    client: Any,
    report: RunReport,
    index: int,
    difficulty: str,
) -> None:
    if client is None:
        from creobook.coloring.images import OpenAIColoringClient

        client = OpenAIColoringClient()
    prompt = scene_prompt(config, scene, difficulty)
    generated = client.generate_image(
        prompt=prompt,
        model=config.image_model,
        size=config.image_size,
        quality=config.image_quality,
        background="opaque",
    )
    report.api_calls += 1
    _store_original(
        directory,
        png=generated.png,
        prompt=prompt,
        config=config,
        background="opaque",
        usage=generated.usage,
    )
    warnings = _process_scene(directory, config)
    report.notes.append(f"Vygenerována scéna {index} ({scene.title}). {'; '.join(warnings)}")


def _process_scene(directory: Path, config: SlonConfig) -> list[str]:
    spec = PAGE_FORMATS[config.page_format]
    # 300 dpi of the printable page. Never upscale.
    max_px = (round(spec["width_mm"] / 25.4 * 300), round(spec["height_mm"] / 25.4 * 300))
    processed = process_line_art(open_png((directory / "original.png").read_bytes()), max_px=max_px)
    _write_png(directory / "processed.png", processed)
    warnings = assess(processed).warnings
    meta = read_meta(directory) or {}
    meta["warnings"] = warnings
    meta["status"] = "processed"
    atomic_write_json(directory / "meta.json", meta)
    return warnings


def _store_original(
    directory: Path,
    *,
    png: bytes,
    prompt: str,
    config: SlonConfig,
    background: str,
    usage: dict[str, Any],
) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    atomic_write_bytes(directory / "original.png", png)
    atomic_write_text(directory / "prompt.txt", prompt + "\n")
    atomic_write_json(
        directory / "meta.json",
        {
            "prompt": prompt,
            "model": config.image_model,
            "quality": config.image_quality,
            "size": config.image_size,
            "background": background,
            "text_model": config.text_model,
            "usage": usage,
            "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "status": "original",
        },
    )


def _write_png(path: Path, image: Image.Image) -> None:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    atomic_write_bytes(path, buffer.getvalue())


def _write_review(output_dir: Path, scenes: list[SceneSpec], report: RunReport) -> None:
    rows: list[dict[str, str]] = []
    for index, scene in enumerate(scenes, start=1):
        directory = _scene_dir(output_dir, index, scene)
        meta = read_meta(directory) or {}
        composed = directory / "composed.png"
        solution = directory / "solution.png"
        placement = _read_placement(directory, scene.id)
        coordinates = ""
        if placement is not None:
            part = f", část={placement.occlusion}" if placement.occlusion else ""
            coordinates = (
                f"x={placement.cx:.3f}, y={placement.cy:.3f}, "
                f"šířka={placement.bbox_w:.3f}, výška={placement.bbox_h:.3f}{part}"
            )
        warnings = meta.get("warnings") or []
        rows.append(
            {
                "number": str(index),
                "title": scene.title,
                "status": str(meta.get("status") or "missing"),
                "warnings": ", ".join(warnings),
                "thumb": composed.relative_to(output_dir).as_posix() if composed.is_file() else "",
                "solution": solution.relative_to(output_dir).as_posix() if solution.is_file() else "",
                "coordinates": coordinates,
            }
        )
    report.review_html = write_review(output_dir / "review.html", rows)


__all__ = ["RunReport", "run_slon_book"]
