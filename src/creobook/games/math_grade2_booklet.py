"""Assemble the 20-page Czech Grade-2 mathematics booklet (5 A4 sheets)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from creobook.compiler import compile_template
from creobook.games.math_grade2 import (
    GENERATOR_VERSION,
    PAGE_COUNT,
    generate_math_grade2_pages,
)
from creobook.games.word_search_booklet import (
    edition_date_from_seed,
    format_edition_date_cs,
)
from creobook.imposition import booklet_spreads, impose_booklet
from creobook.theme import Theme, load_theme, project_root

# 20 A5 pages → 10 A4 landscape sides → 5 nested sheets.
# Outside in: (20|1, 2|19), (18|3, 4|17), (16|5, 6|15), (14|7, 8|13), (12|9, 10|11).
EXPECTED_SPREADS = [
    (20, 1),
    (2, 19),
    (18, 3),
    (4, 17),
    (16, 5),
    (6, 15),
    (14, 7),
    (8, 13),
    (12, 9),
    (10, 11),
]

PRINT_INSTRUCTIONS_CS = """\
Tisk sešitu Matematika – 2. třída:
• Papír A4, orientace na šířku (landscape).
• Oboustranný tisk, otočení podle krátké hrany (flip on short edge).
• Měřítko 100 % / skutečná velikost. Nepřizpůsobovat stránce.
• Vypněte režim sešitu v tiskárně — stránky už jsou vyřazené.
• Strany A5 se při vyřazení nezmenšují. Úsečky na stranách 18 a 19 mají délku 4 cm a 7 cm.
• 5 listů, zvenku dovnitř:
  1. líc 20 | 1, rub 2 | 19
  2. líc 18 | 3, rub 4 | 17
  3. líc 16 | 5, rub 6 | 15
  4. líc 14 | 7, rub 8 | 13
  5. líc 12 | 9, rub 10 | 11
• Vložte listy do sebe, přehněte napůl, zasuňte pod gumičku CreoBook.
• Nejprve ověřte orientaci rubu na jednom listu.
Řešení pro rodiče je v samostatném PDF (*-odpovedi.pdf), není součástí dvaceti stran.
"""


def build_math_grade2_booklet_pages(
    *,
    seed: int = 20261026,
    edition_date: date | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    pages, meta = generate_math_grade2_pages(seed=seed)
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
    chunk_size = 4
    chunks = [answers[i : i + chunk_size] for i in range(0, len(answers), chunk_size)]
    out: list[dict[str, Any]] = []
    for i, chunk in enumerate(chunks, start=1):
        out.append(
            {
                "kind": "math_grade2_answers",
                "title": "Řešení — Matematika – 2. třída",
                "instructions": (
                    "Pro rodiče a vyučující. Nepatří do sešitu dítěte. "
                    "Tisk pracovních stran: A4 na šířku, oboustranně, otočení podle "
                    "krátké hrany, měřítko 100 % bez přizpůsobení stránce."
                ),
                "difficulty": "easy",
                "seed": seed + i,
                "data": {
                    "booklet_title": "Matematika – 2. třída",
                    "edition_date": meta.get("edition_date", ""),
                    "part": i,
                    "parts": len(chunks),
                    "items": chunk,
                },
                "answer": {},
            }
        )
    return out


def export_math_grade2_json(
    pages: list[dict[str, Any]], meta: dict[str, Any], path: Path | str
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {**meta, "pages": pages}
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def compile_math_grade2_booklet(
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
    theme = theme or load_theme()
    edition = edition_date or edition_date_from_seed(seed)
    infix = edition.strftime("%Y%m%d")
    pages, meta = build_math_grade2_booklet_pages(seed=seed, edition_date=edition)

    json_path = Path(json_output) if json_output else (
        project_root() / "generated" / f"math-grade2-seed-{seed}.json"
    )
    export_math_grade2_json(pages, meta, json_path)

    data = {
        "page_type": "math_grade2_booklet",
        "theme": theme.to_typst_dict(),
        "pages": pages,
        "title": "Matematika – 2. třída",
        "meta": {k: v for k, v in meta.items() if k != "answers"},
    }

    if pages_output is not None:
        pages_pdf = Path(pages_output)
    elif output is not None:
        out = Path(output)
        pages_pdf = out.with_name(out.stem + "-pages.pdf")
    else:
        pages_pdf = (
            project_root()
            / "output"
            / "pages"
            / f"creobook-{infix}-matematika-2trida-a5.pdf"
        )
    pages_pdf.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", data, pages_pdf, theme=theme)

    answer_pages = build_answer_pages(meta, seed=seed)
    answers_data = {
        "page_type": "math_grade2_answers",
        "theme": theme.to_typst_dict(),
        "pages": answer_pages,
        "title": "Řešení — Matematika – 2. třída",
        "meta": {"seed": seed, "generator_version": GENERATOR_VERSION},
    }
    if answers_output is not None:
        answers_pdf = Path(answers_output)
    elif output is not None:
        answers_pdf = Path(output).with_name(Path(output).stem + "-odpovedi.pdf")
    else:
        answers_pdf = (
            project_root()
            / "output"
            / "pages"
            / f"creobook-{infix}-matematika-2trida-odpovedi.pdf"
        )
    answers_pdf.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", answers_data, answers_pdf, theme=theme)

    result: dict[str, Path] = {
        "pages": pages_pdf,
        "answers": answers_pdf,
        "json": json_path,
    }

    if impose:
        booklet_pdf = Path(output) if output else (
            project_root()
            / "output"
            / "booklet"
            / f"creobook-{infix}-matematika-2trida.pdf"
        )
        booklet_pdf.parent.mkdir(parents=True, exist_ok=True)
        impose_booklet(pages_pdf, booklet_pdf, theme=theme, fold_guide=fold_guide)
        result["booklet"] = booklet_pdf
        if booklet_spreads(PAGE_COUNT) != EXPECTED_SPREADS:
            raise ValueError("Unexpected booklet order")

    return result
