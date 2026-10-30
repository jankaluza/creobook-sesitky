"""Assemble the 24-page Czech crossword booklet (KŘÍŽOVKY)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from creobook.compiler import compile_template
from creobook.games.crossword import (
    DIFFICULTY_SPEC,
    GENERATOR_VERSION,
    CrosswordGenerationError,
    generate_crossword,
)
from creobook.games.crossword_data import (
    DATASET_VERSION,
    THEME_TITLES_CS,
    load_crossword_dataset,
    tajenka_key,
)
from creobook.games.models import Difficulty, PuzzleBase
from creobook.games.validation import validate_puzzle
from creobook.games.word_search_booklet import (
    EXPECTED_SPREADS,
    edition_date_from_seed,
    format_edition_date_cs,
)
from creobook.imposition import booklet_spreads, impose_booklet
from creobook.theme import Theme, load_theme, project_root

PUZZLE_COUNT = 20

# 20 puzzles across 3 solution pages
SOLUTION_BANDS = [
    (1, 7),
    (8, 14),
    (15, 20),
]

DIFFICULTY_PLAN: dict[str, tuple[int, int, int]] = {
    "easy": (20, 0, 0),
    "medium": (0, 20, 0),
    "hard": (0, 0, 20),
    "mixed": (7, 7, 6),
}

PRINT_INSTRUCTIONS_CS = """\
Tisk sešitu Křížovky:
• Papír A4, orientace na šířku (landscape).
• Oboustranný tisk, otočení podle krátké hrany (short edge / flip on short edge).
• Měřítko 100 % / skutečná velikost — nevypínat okraje tiskárnou přes „fit to page“.
• Vypněte vlastní režim sešitu tiskárny; PDF je už impositionované.
• Vytiskněte všech 12 stran (6 listů), listy v pořadí vložte do sebe, přehnout napůl
  a zasuňte pod gumičku CreoBook.
• Nejprve ověřte orientaci na jednom listu — nastavení tiskáren se liší.
"""


def _meta_page(
    kind: str,
    title: str,
    seed: int,
    *,
    instructions: str = "",
    data: dict[str, Any] | None = None,
) -> PuzzleBase:
    return PuzzleBase(
        kind=kind,
        title=title,
        instructions=instructions,
        difficulty=Difficulty.easy,
        seed=seed,
        data=data or {},
        answer={},
    )


def _plan_counts(difficulty: str, easy: int | None, medium: int | None, hard: int | None) -> tuple[int, int, int]:
    if easy is not None or medium is not None or hard is not None:
        e = int(easy or 0)
        m = int(medium or 0)
        h = int(hard or 0)
    else:
        if difficulty not in DIFFICULTY_PLAN:
            raise ValueError(
                f"Unknown difficulty {difficulty!r}; use easy/medium/hard/mixed"
            )
        e, m, h = DIFFICULTY_PLAN[difficulty]
    if e + m + h != PUZZLE_COUNT:
        raise ValueError(
            f"Booklet expects {PUZZLE_COUNT} crosswords; got {e}+{m}+{h}={e + m + h}"
        )
    return e, m, h


def build_crossword_booklet_pages(
    *,
    seed: int = 20270101,
    difficulty: str = "mixed",
    theme: str | None = None,
    easy: int | None = None,
    medium: int | None = None,
    hard: int | None = None,
    solutions: bool = True,
    edition_date: date | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if theme is not None and theme not in THEME_TITLES_CS:
        raise ValueError(f"Unknown theme: {theme!r}. Known: {sorted(THEME_TITLES_CS)}")

    e, m, h = _plan_counts(difficulty, easy, medium, hard)
    edition = edition_date or edition_date_from_seed(seed)
    edition_cs = format_edition_date_cs(edition)
    dataset = load_crossword_dataset()

    used_answers: set[str] = set()
    used_tajenky: set[str] = set()
    puzzles: list[PuzzleBase] = []
    puzzle_number = 0
    attempt_total = 0

    plan = [
        (Difficulty.easy, e),
        (Difficulty.medium, m),
        (Difficulty.hard, h),
    ]
    for diff, count in plan:
        for _ in range(count):
            puzzle_number += 1
            page_seed = seed * 1009 + puzzle_number * 9176 + {
                Difficulty.easy: 1,
                Difficulty.medium: 2,
                Difficulty.hard: 3,
            }[diff]
            try:
                puzzle = generate_crossword(
                    seed=page_seed,
                    difficulty=diff,
                    theme=theme,
                    puzzle_number=puzzle_number,
                    used_answers=used_answers,
                    used_tajenky=used_tajenky,
                    dataset=dataset,
                    title=f"Křížovka {puzzle_number}",
                )
            except CrosswordGenerationError as exc:
                raise CrosswordGenerationError(
                    f"Booklet generation failed at puzzle {puzzle_number} "
                    f"({diff.value}): {exc}"
                ) from exc
            validate_puzzle(puzzle)
            for ans in puzzle.answer["answers"]:
                if ans in used_answers:
                    raise CrosswordGenerationError(f"Answer reused across booklet: {ans}")
                used_answers.add(ans)
            t_key = tajenka_key(puzzle.answer["tajenka"])
            if t_key in used_tajenky:
                raise CrosswordGenerationError(f"Tajenka reused: {puzzle.answer['tajenka']}")
            used_tajenky.add(t_key)
            attempt_total += int(puzzle.data["generation"]["attempt"])
            puzzles.append(puzzle)

    theme_title = THEME_TITLES_CS[theme or "mixed"]
    if difficulty == "easy":
        subtitle = "Lehká obtížnost · 20 křížovek"
    elif difficulty == "medium":
        subtitle = "Střední obtížnost · 20 křížovek"
    elif difficulty == "hard":
        subtitle = "Těžká obtížnost · 20 křížovek"
    else:
        subtitle = f"Smíšená obtížnost · {e} lehké · {m} střední · {h} těžké"
    if theme and theme != "mixed":
        subtitle = f"{theme_title} · {subtitle}"

    cover = _meta_page(
        "cw_cover",
        "CreoBook – Křížovky",
        seed,
        instructions=(
            "Doplňte vodorovná slova podle číslovaných nápověd. Zvýrazněný svislý "
            "sloupec skládá tajenku shora dolů (mezery v tajence se do mřížky "
            "nezapisují). Písmeno CH zabírá dvě políčka (C + H). Řešení najdete "
            "na stranách 22–24."
        ),
        data={
            "pack_title": "CreoBook – Křížovky",
            "pack_subtitle": subtitle,
            "edition_date": edition_cs,
            "theme": theme or "mixed",
            "theme_title": theme_title,
            "difficulty": difficulty,
            "easy": e,
            "medium": m,
            "hard": h,
            "legend": [
                {
                    "label": "LEHKÁ",
                    "marker": "●○○",
                    "detail": "kratší tajenka · kratší slova · větší políčka",
                },
                {
                    "label": "STŘEDNÍ",
                    "marker": "●●○",
                    "detail": "delší tajenka · běžná slovní zásoba",
                },
                {
                    "label": "TĚŽKÁ",
                    "marker": "●●●",
                    "detail": "delší tajenka · náročnější nápovědy",
                },
            ],
            "print_hint": (
                "Tisk: A4 na šířku · duplex · krátká hrana · 100 % · bez režimu sešitu tiskárny"
            ),
        },
    )

    pages_out: list[PuzzleBase] = [cover, *puzzles]

    for band_i, (fr, to) in enumerate(SOLUTION_BANDS, start=1):
        items = []
        for pz in puzzles:
            num = int(pz.data["puzzle_number"])
            if fr <= num <= to:
                items.append(
                    {
                        "page": num + 1,
                        "puzzle_number": num,
                        "title": pz.title,
                        "kind": "crossword",
                        "difficulty": pz.difficulty.value,
                        "answer": pz.answer,
                        "data": {
                            "rows": pz.data["rows"],
                            "cols": pz.data["cols"],
                            "grid": pz.data["grid"],
                            "tajenka_col": pz.data["tajenka_col"],
                            "tajenka_phrase": pz.data["tajenka_phrase"],
                            "tajenka_letters": pz.data["tajenka_letters"],
                            "clues": pz.data["clues"],
                            "difficulty_label_cs": pz.data["difficulty_label_cs"],
                            "difficulty_marker": pz.data["difficulty_marker"],
                            "theme_title": pz.data["theme_title"],
                        },
                    }
                )
        sol = _meta_page(
            "cw_solutions",
            f"Řešení {fr}–{to}",
            seed + 70_000 + band_i,
            instructions="Vyplněná mřížka a tajenka pro každou křížovku.",
            data={"from": fr, "to": to, "items": items if solutions else []},
        )
        if not solutions:
            sol.instructions = "Řešení v tomto vydání nejsou zahrnuta."
        pages_out.append(sol)

    if len(pages_out) != 24:
        raise ValueError(f"Expected 24 pages, got {len(pages_out)}")

    meta = {
        "generator_version": GENERATOR_VERSION,
        "dataset_version": DATASET_VERSION,
        "seed": seed,
        "language": "cs",
        "difficulty": difficulty,
        "theme": theme or "mixed",
        "theme_title": theme_title,
        "solutions": solutions,
        "edition_date": edition_cs,
        "edition_date_iso": edition.isoformat(),
        "difficulty_configuration": {
            "easy": e,
            "medium": m,
            "hard": h,
            "specs": {k.value: v for k, v in DIFFICULTY_SPEC.items()},
        },
        "generation_stats": {
            "total_attempts": attempt_total,
            "average_attempts_per_puzzle": attempt_total / PUZZLE_COUNT,
            "unique_answers": len(used_answers),
            "unique_tajenky": len(used_tajenky),
        },
        "print_instructions_cs": PRINT_INSTRUCTIONS_CS,
    }
    return [p.model_dump(mode="json") for p in pages_out], meta


def export_crossword_json(
    pages: list[dict[str, Any]], meta: dict[str, Any], path: Path | str
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    puzzles = [p for p in pages if p["kind"] == "crossword"]
    payload = {
        **meta,
        "page_count": len(pages),
        "puzzle_count": len(puzzles),
        "puzzles": [
            {
                "puzzle_number": p["data"]["puzzle_number"],
                "difficulty": p["difficulty"],
                "theme": p["data"]["theme"],
                "tajenka": p["answer"]["tajenka"],
                "answers": p["answer"]["answers"],
                "rows": p["data"]["rows"],
                "cols": p["data"]["cols"],
                "tajenka_col": p["data"]["tajenka_col"],
                "seed": p["seed"],
                "validation": {"ok": True},
            }
            for p in puzzles
        ],
        "pages": pages,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def compile_crossword_booklet(
    *,
    seed: int = 20270101,
    difficulty: str = "mixed",
    theme: str | None = None,
    easy: int | None = None,
    medium: int | None = None,
    hard: int | None = None,
    solutions: bool = True,
    fold_guide: bool = True,
    output: Path | str | None = None,
    pages_output: Path | str | None = None,
    json_output: Path | str | None = None,
    theme_obj: Theme | None = None,
    impose: bool = True,
    edition_date: date | None = None,
) -> dict[str, Path]:
    theme_obj = theme_obj or load_theme()
    edition = edition_date or edition_date_from_seed(seed)
    infix = edition.strftime("%Y%m%d")
    pages, meta = build_crossword_booklet_pages(
        seed=seed,
        difficulty=difficulty,
        theme=theme,
        easy=easy,
        medium=medium,
        hard=hard,
        solutions=solutions,
        edition_date=edition,
    )

    json_path = Path(json_output) if json_output else (
        project_root() / "generated" / f"crossword-cs-seed-{seed}.json"
    )
    export_crossword_json(pages, meta, json_path)

    data = {
        "page_type": "crossword_booklet",
        "theme": theme_obj.to_typst_dict(),
        "pages": pages,
        "title": "CreoBook – Křížovky",
        "meta": meta,
    }

    if pages_output is not None:
        pages_pdf = Path(pages_output)
    elif output is not None:
        out = Path(output)
        pages_pdf = out.with_name(out.stem + "-pages.pdf")
    else:
        pages_pdf = (
            project_root() / "output" / "pages" / f"creobook-{infix}-krizovky-a5.pdf"
        )
    pages_pdf.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", data, pages_pdf, theme=theme_obj)

    result: dict[str, Path] = {"pages": pages_pdf, "json": json_path}

    if impose:
        booklet_pdf = Path(output) if output else (
            project_root() / "output" / "booklet" / f"creobook-{infix}-krizovky.pdf"
        )
        booklet_pdf.parent.mkdir(parents=True, exist_ok=True)
        impose_booklet(pages_pdf, booklet_pdf, theme=theme_obj, fold_guide=fold_guide)
        result["booklet"] = booklet_pdf
        if booklet_spreads(24) != EXPECTED_SPREADS:
            raise ValueError("Unexpected booklet order")

    return result
