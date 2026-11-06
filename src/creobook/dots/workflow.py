"""Plan subjects locally, cache silhouettes, and bind a connect-the-dots booklet.

Paid image calls run only with ``generate=True``. Rebuilding a PDF from saved
dot geometry does not call the API.
"""

from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from creobook.coloring.cache import atomic_write_bytes, atomic_write_json, atomic_write_text
from creobook.coloring.prompts import find_flags
from creobook.coloring.workflow import slugify
from creobook.dots.booklet import compile_dots_pdfs
from creobook.dots.geometry import PuzzleGeometry, dot_payload, geometry_from_png, puzzle_svg
from creobook.dots.models import DotsConfig, DotsError, content_size
from creobook.dots.subjects import image_prompt, subjects_for


@dataclass
class PuzzleSpec:
    index: int
    name: str
    prompt: str
    max_number: int

    @property
    def slug(self) -> str:
        return f"{self.index:02d}-{slugify(self.name)}"


@dataclass
class RunReport:
    output_dir: Path
    plan_path: Path
    reading_pdf: Path | None = None
    print_pdf: Path | None = None
    review_html: Path | None = None
    notes: list[str] = field(default_factory=list)
    new_images: int = 0
    cached_puzzles: int = 0
    api_calls: int = 0


def build_plan(config: DotsConfig) -> list[PuzzleSpec]:
    maxima = config.maxima()
    subjects = subjects_for(config.theme, len(maxima))
    return [
        PuzzleSpec(index=index, name=name, prompt=image_prompt(english), max_number=maximum)
        for index, ((name, english), maximum) in enumerate(zip(subjects, maxima, strict=True), start=1)
    ]


def _slot(root: Path, puzzle: PuzzleSpec) -> Path:
    return root / "puzzles" / puzzle.slug


def _load_geometry(path: Path, puzzle: PuzzleSpec, page_format: str) -> PuzzleGeometry | None:
    if not path.is_file():
        return None
    import json

    raw = json.loads(path.read_text(encoding="utf-8"))
    if str(raw.get("page_format") or "A5") != page_format:
        return None
    if int(raw.get("max_number", -1)) != puzzle.max_number:
        return None
    if raw.get("prompt") != puzzle.prompt:
        return None
    dots = tuple(_dot(item) for item in raw.get("dots") or [])
    if len(dots) != puzzle.max_number + 1:
        return None
    width, height = content_size(page_format)
    return PuzzleGeometry(dots, float(raw["font_pt"]), width, height)


def _dot(item: dict[str, Any]):
    from creobook.dots.geometry import Dot

    return Dot(
        number=int(item["n"]),
        x=float(item["x"]),
        y=float(item["y"]),
        label_x=float(item["lx"]),
        label_y=float(item["ly"]),
        label_w=float(item["lw"]),
        label_h=float(item["lh"]),
    )


def _write_geometry(
    directory: Path,
    puzzle: PuzzleSpec,
    geometry: PuzzleGeometry,
    *,
    page_format: str,
    model: str,
) -> None:
    payload = {
        "name": puzzle.name,
        "prompt": puzzle.prompt,
        "model": model,
        "max_number": puzzle.max_number,
        "page_format": page_format,
        "font_pt": geometry.font_pt,
        "dots": [dot_payload(dot) for dot in geometry.dots],
    }
    atomic_write_json(directory / "dots.json", payload)
    width, height = content_size(page_format)
    atomic_write_text(
        directory / "puzzle.svg",
        puzzle_svg(geometry, page_width=width, page_height=height, answer=False),
    )
    atomic_write_text(
        directory / "answer.svg",
        puzzle_svg(geometry, page_width=width, page_height=height, answer=True),
    )


def _review(path: Path, rows: list[dict[str, str]]) -> None:
    cards = []
    for row in rows:
        cards.append(
            "<article>"
            f"<h2>{html.escape(row['title'])}</h2>"
            f"<p>{html.escape(row['meta'])}</p>"
            f"<object data=\"{html.escape(row['svg'])}\" type=\"image/svg+xml\"></object>"
            "</article>"
        )
    document = (
        "<!DOCTYPE html><html lang=\"cs\"><meta charset=\"utf-8\">"
        "<title>Spojovačky</title>"
        "<style>body{font-family:sans-serif} article{display:inline-block;width:220px;"
        "margin:8px;vertical-align:top} object{width:200px;height:280px;border:1px solid #ddd}</style>"
        f"<h1>Náhled spojovaček</h1>{''.join(cards)}</html>"
    )
    atomic_write_text(path, document)


def run_dots_book(
    config: DotsConfig,
    *,
    generate: bool = False,
    pdf_only: bool = False,
    dry_run: bool = False,
    regenerate_puzzle: int | None = None,
    force_regenerate: bool = False,
    client: Any = None,
) -> RunReport:
    config.validate_image_options()
    if pdf_only and (generate or dry_run or regenerate_puzzle or force_regenerate):
        raise DotsError("--pdf-only does not call OpenAI and ignores generation flags")
    if dry_run and generate:
        raise DotsError("Choose either --dry-run or --generate")
    if force_regenerate and not generate:
        raise DotsError("--force-regenerate needs --generate")
    flags = find_flags(config.theme, config.title)
    if flags and (generate or regenerate_puzzle or force_regenerate):
        raise DotsError(
            "Generování je zastavené, téma obsahuje chráněný odkaz: " + ", ".join(flags)
        )

    output_dir = Path(config.output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    config.output_directory = str(output_dir.resolve())
    atomic_write_json(output_dir / "config.json", config.model_dump(mode="json"))

    plan_path = output_dir / "plan.json"
    report = RunReport(output_dir=output_dir, plan_path=plan_path)
    if plan_path.is_file() and regenerate_puzzle is None and not force_regenerate:
        import json

        saved = json.loads(plan_path.read_text(encoding="utf-8"))
        plan = [
            PuzzleSpec(
                index=int(item["index"]),
                name=str(item["name"]),
                prompt=str(item["prompt"]),
                max_number=int(item["max_number"]),
            )
            for item in saved
        ]
        if len(plan) != config.puzzle_count or [item.max_number for item in plan] != config.maxima():
            raise DotsError(
                "Uložený plán má jiný počet úloh. Použijte nový adresář, nebo smažte plan.json."
            )
        report.notes.append("Plán načten z plan.json")
    else:
        plan = build_plan(config)
        atomic_write_json(
            plan_path,
            [
                {
                    "index": item.index,
                    "name": item.name,
                    "prompt": item.prompt,
                    "max_number": item.max_number,
                }
                for item in plan
            ],
        )
        report.notes.append("Plán předmětů uložen. Obrázky se kreslí až s --generate.")

    if flags:
        report.notes.append("Autorská kontrola našla: " + ", ".join(flags))
    if dry_run:
        report.notes.append("Dry-run: siluety se negenerují.")
        return report

    if regenerate_puzzle is not None and not 1 <= regenerate_puzzle <= len(plan):
        raise DotsError(f"Úloha {regenerate_puzzle} v plánu není (1–{len(plan)})")
    if regenerate_puzzle is not None and not generate:
        generate = True

    width, height = content_size(config.page_format)
    ready: list[tuple[PuzzleSpec, PuzzleGeometry]] = []
    pending: list[PuzzleSpec] = []
    for puzzle in plan:
        directory = _slot(output_dir, puzzle)
        selected = regenerate_puzzle == puzzle.index or force_regenerate
        geometry = None if selected else _load_geometry(directory / "dots.json", puzzle, config.page_format)
        if geometry is not None:
            ready.append((puzzle, geometry))
            report.cached_puzzles += 1
        else:
            pending.append(puzzle)

    if pdf_only and pending:
        missing = ", ".join(str(item.index) for item in pending)
        raise DotsError("PDF-only nemá geometrii úloh: " + missing)

    report.new_images = 0
    local: list[PuzzleSpec] = []
    paid: list[PuzzleSpec] = []
    for puzzle in pending:
        directory = _slot(output_dir, puzzle)
        selected = regenerate_puzzle == puzzle.index or force_regenerate
        if selected or not (directory / "original.png").is_file():
            paid.append(puzzle)
        else:
            local.append(puzzle)
    report.new_images = len(paid)
    report.notes.append(
        f"V mezipaměti: {report.cached_puzzles}. Nové siluety: {report.new_images}. "
        f"Znovu zpracovat místně: {len(local)}."
    )
    if paid and not generate:
        report.notes.append("Chybí siluety. Placené generování spustí až --generate.")
        return report
    if paid and len(paid) > config.max_new:
        raise DotsError(
            f"Je potřeba {len(paid)} nových siluet, limit je {config.max_new}. "
            "Zvyš --max-new, nebo generuj po dávkách."
        )

    for puzzle in [*local, *paid]:
        directory = _slot(output_dir, puzzle)
        directory.mkdir(parents=True, exist_ok=True)
        atomic_write_text(directory / "prompt.txt", puzzle.prompt)
        png_path = directory / "original.png"
        selected = regenerate_puzzle == puzzle.index or force_regenerate
        if selected or not png_path.is_file():
            if client is None:
                from creobook.coloring.images import OpenAIColoringClient

                client = OpenAIColoringClient()
            generated = client.generate_image(
                prompt=puzzle.prompt,
                model=config.image_model,
                size="1024x1024",
                quality=config.image_quality,
            )
            report.api_calls += 1
            atomic_write_bytes(png_path, generated.png)
            atomic_write_json(
                directory / "meta.json",
                {
                    "status": "original",
                    "model": generated.model or config.image_model,
                    "prompt": puzzle.prompt,
                    "usage": generated.usage,
                },
            )
        try:
            geometry = geometry_from_png(
                png_path.read_bytes(),
                max_number=puzzle.max_number,
                content_width=width,
                content_height=height,
                page_format=config.page_format,
            )
        except DotsError as exc:
            atomic_write_json(
                directory / "meta.json",
                {"status": "rejected", "prompt": puzzle.prompt, "error": str(exc)},
            )
            raise DotsError(
                f"Úloha {puzzle.index} ({puzzle.name}) nejde použít: {exc} "
                f"Zkuste --regenerate-puzzle {puzzle.index}."
            ) from exc
        _write_geometry(
            directory,
            puzzle,
            geometry,
            page_format=config.page_format,
            model=config.image_model,
        )
        ready.append((puzzle, geometry))
        report.notes.append(
            f"Úloha {puzzle.index}: {puzzle.name}, čísla 0–{puzzle.max_number}."
        )

    ready.sort(key=lambda item: item[0].index)
    puzzles = [(puzzle.name, geometry) for puzzle, geometry in ready]
    pdfs = compile_dots_pdfs(config, puzzles, output_dir)
    report.reading_pdf = pdfs["reading"]
    report.print_pdf = pdfs["print"]
    report.notes.append(f"Čtení: {report.reading_pdf.name}")
    report.notes.append(f"Tisk: {report.print_pdf.name}")
    if "solutions" in pdfs:
        report.notes.append(f"Řešení bokem, nejsou v sešitku: {pdfs['solutions'].name}")
    rows = []
    for puzzle, _geometry in ready:
        rows.append(
            {
                "title": f"{puzzle.index}. {puzzle.name}",
                "meta": f"0–{puzzle.max_number}",
                "svg": f"puzzles/{puzzle.slug}/puzzle.svg",
            }
        )
    report.review_html = output_dir / "review.html"
    _review(report.review_html, rows)
    return report
