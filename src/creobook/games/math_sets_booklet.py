"""Assemble one of the three 8-page Grade-2 maths booklets (2 A4 sheets)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from creobook.compiler import compile_template
from creobook.games.math_sets import (
    GENERATOR_VERSION,
    PAGE_COUNT,
    SETS,
    generate_math_set,
)
from creobook.games.word_search_booklet import (
    edition_date_from_seed,
    format_edition_date_cs,
)
from creobook.imposition import booklet_spreads, impose_booklet
from creobook.theme import Theme, load_theme, project_root

# 8 A5 pages → 4 A4 landscape sides → 2 nested sheets.
# Outside sheet: 8 | 1, back 2 | 7. Inside sheet: 6 | 3, back 4 | 5.
EXPECTED_SPREADS = [
    (8, 1),
    (2, 7),
    (6, 3),
    (4, 5),
]

PRINT_INSTRUCTIONS_CS = """\
Tisk sešitu (8 stran A5, 2 listy A4):
• Papír A4, orientace na šířku (landscape).
• Oboustranný tisk, otočení podle krátké hrany (flip on short edge).
• Měřítko 100 % / skutečná velikost. Nepřizpůsobovat stránce.
• Vypněte režim sešitu v tiskárně — stránky už jsou vyřazené.
• Strany A5 se při vyřazení nezmenšují.
• 2 listy, zvenku dovnitř:
  1. vnější list: líc 8 | 1, rub 2 | 7
  2. vnitřní list: líc 6 | 3, rub 4 | 5
• Vložte vnitřní list do vnějšího, přehněte napůl, zasuňte pod gumičku CreoBook.
• Nejprve ověřte, že po otočení listu podle krátké hrany je rub správně čitelný.
Řešení pro rodiče je v samostatném PDF (*-odpovedi.pdf), není součástí osmi stran.
"""


def build_math_set_pages(
    set_id: str,
    *,
    seed: int = 20261026,
    edition_date: date | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pages, meta = generate_math_set(set_id, seed=seed)
    edition = edition_date or edition_date_from_seed(seed)
    meta["edition_date"] = format_edition_date_cs(edition)
    meta["edition_date_iso"] = edition.isoformat()
    if len(pages) != PAGE_COUNT:
        raise ValueError(f"Expected {PAGE_COUNT} pages, got {len(pages)}")
    if booklet_spreads(PAGE_COUNT) != EXPECTED_SPREADS:
        raise ValueError(f"Unexpected spreads: {booklet_spreads(PAGE_COUNT)}")
    return pages, meta


def build_answer_pages(meta: dict[str, Any], *, seed: int) -> list[dict[str, Any]]:
    answers = meta["answers"]
    chunk_size = 2
    chunks = [answers[i : i + chunk_size] for i in range(0, len(answers), chunk_size)]
    title = meta["title"]
    out: list[dict[str, Any]] = []
    for i, chunk in enumerate(chunks, start=1):
        out.append(
            {
                "kind": "math_set_answers",
                "title": f"Řešení — {title}",
                "instructions": (
                    "Pro rodiče a vyučující. Nepatří do sešitu dítěte. "
                    "Tisk pracovních stran: A4 na šířku, oboustranně, otočení podle "
                    "krátké hrany, měřítko 100 % bez přizpůsobení stránce."
                ),
                "difficulty": "easy",
                "seed": seed + i,
                "data": {
                    "booklet_title": title,
                    "edition_date": meta.get("edition_date", ""),
                    "part": i,
                    "parts": len(chunks),
                    "items": chunk,
                },
                "answer": {},
            }
        )
    return out


def compile_math_set_booklet(
    set_id: str,
    *,
    seed: int = 20261026,
    fold_guide: bool = True,
    output: Path | str | None = None,
    pages_output: Path | str | None = None,
    answers_output: Path | str | None = None,
    json_output: Path | str | None = None,
    theme: Theme | None = None,
    impose: bool = True,
    edition_date: date | None = None,
) -> dict[str, Path]:
    if set_id not in SETS:
        raise ValueError(f"unknown set {set_id}")
    spec = SETS[set_id]
    theme = theme or load_theme()
    edition = edition_date or edition_date_from_seed(seed)
    infix = edition.strftime("%Y%m%d")
    pages, meta = build_math_set_pages(set_id, seed=seed, edition_date=edition)
    slug = spec["slug"]

    json_path = Path(json_output) if json_output else (
        project_root() / "generated" / f"math-set-{slug}-seed-{seed}.json"
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {**meta, "pages": pages}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    data = {
        "page_type": "math_set_booklet",
        "theme": theme.to_typst_dict(),
        "pages": pages,
        "title": spec["title"],
        "meta": {k: v for k, v in meta.items() if k != "answers"},
    }

    if pages_output is not None:
        pages_pdf = Path(pages_output)
    elif output is not None:
        out = Path(output)
        pages_pdf = out.with_name(out.stem + "-pages.pdf")
    else:
        pages_pdf = project_root() / "output" / "pages" / f"creobook-{infix}-{slug}-a5.pdf"
    pages_pdf.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", data, pages_pdf, theme=theme)

    answer_pages = build_answer_pages(meta, seed=seed)
    answers_data = {
        "page_type": "math_set_answers",
        "theme": theme.to_typst_dict(),
        "pages": answer_pages,
        "title": f"Řešení — {spec['title']}",
        "meta": {"seed": seed, "generator_version": GENERATOR_VERSION},
    }
    if answers_output is not None:
        answers_pdf = Path(answers_output)
    elif output is not None:
        answers_pdf = Path(output).with_name(Path(output).stem + "-odpovedi.pdf")
    else:
        answers_pdf = project_root() / "output" / "pages" / f"creobook-{infix}-{slug}-odpovedi.pdf"
    answers_pdf.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", answers_data, answers_pdf, theme=theme)

    result: dict[str, Path] = {"pages": pages_pdf, "answers": answers_pdf, "json": json_path}
    if impose:
        booklet_pdf = Path(output) if output else (
            project_root() / "output" / "booklet" / f"creobook-{infix}-{slug}.pdf"
        )
        booklet_pdf.parent.mkdir(parents=True, exist_ok=True)
        impose_booklet(pages_pdf, booklet_pdf, theme=theme, fold_guide=fold_guide)
        result["booklet"] = booklet_pdf
    return result
