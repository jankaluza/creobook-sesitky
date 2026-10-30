"""Assemble the 24-page Czech word-search booklet (OSMISMĚRKY)."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from creobook.compiler import compile_template
from creobook.games.base import make_rng
from creobook.games.models import Difficulty, PuzzleBase
from creobook.games.validation import validate_puzzle
from creobook.games.vocab import VOCAB_VERSION, count_pools, default_vocab_path, load_vocabulary
from creobook.games.word_search import (
    DIFFICULTY_SPEC,
    GENERATOR_VERSION,
    GenerationStats,
    generate_puzzle,
    select_themed_words,
)
from creobook.imposition import booklet_spreads, impose_booklet
from creobook.theme import Theme, load_theme, project_root


EXPECTED_SPREADS = [
    (24, 1),
    (2, 23),
    (22, 3),
    (4, 21),
    (20, 5),
    (6, 19),
    (18, 7),
    (8, 17),
    (16, 9),
    (10, 15),
    (14, 11),
    (12, 13),
]

SOLUTION_BANDS = [
    (1, 4),
    (5, 8),
    (9, 12),
    (13, 15),
    (16, 18),
]


def edition_date_from_seed(seed: int, *, today: date | None = None) -> date:
    """Interpret YYYYMMDD seeds as an edition date; otherwise use today."""
    text = str(seed)
    if len(text) == 8 and text.isdigit():
        try:
            return datetime.strptime(text, "%Y%m%d").date()
        except ValueError:
            pass
    return today or date.today()


def format_edition_date_cs(d: date) -> str:
    """Czech display form: DD. MM. YYYY."""
    return f"{d.day:02d}. {d.month:02d}. {d.year}"


def edition_infix(seed: int, *, today: date | None = None) -> str:
    """Filename infix YYYYMMDD derived from seed or today."""
    return edition_date_from_seed(seed, today=today).strftime("%Y%m%d")


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


def build_word_search_booklet_pages(
    *,
    seed: int = 20270101,
    language: str = "cs",
    easy: int = 6,
    medium: int = 6,
    hard: int = 6,
    grid_diacritics: bool = False,
    solutions: bool = True,
    stats: GenerationStats | None = None,
    preferred_theme: str | None = None,
    edition_date: date | None = None,
    edition_label: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if language != "cs":
        raise ValueError("Only Czech (cs) vocabulary is currently supported")
    total_puzzles = easy + medium + hard
    if total_puzzles != 18:
        raise ValueError(
            f"Booklet layout expects 18 puzzles (6+6+6); got {easy}+{medium}+{hard}={total_puzzles}"
        )

    edition = edition_date or edition_date_from_seed(seed)
    edition_cs = format_edition_date_cs(edition)

    vocab = load_vocabulary()
    pools = count_pools(vocab)
    stats = stats or GenerationStats()
    used: set[str] = set()
    puzzles: list[PuzzleBase] = []
    puzzle_number = 0

    plan: list[tuple[Difficulty, int]] = [
        (Difficulty.easy, easy),
        (Difficulty.medium, medium),
        (Difficulty.hard, hard),
    ]
    preferred = [preferred_theme] if preferred_theme else None

    for difficulty, count in plan:
        for i in range(count):
            puzzle_number += 1
            page_seed = seed * 1009 + puzzle_number * 9176 + {
                Difficulty.easy: 1,
                Difficulty.medium: 2,
                Difficulty.hard: 3,
            }[difficulty]
            rng = make_rng(page_seed)
            theme, words = select_themed_words(
                difficulty=difficulty,
                count=int(DIFFICULTY_SPEC[difficulty]["word_count"]),
                used=used,
                rng=rng,
                preferred_themes=preferred,
            )
            for w in words:
                if w.normalized in used:
                    raise ValueError(f"Word reuse detected: {w.normalized}")
                used.add(w.normalized)
            puzzle = generate_puzzle(
                seed=page_seed,
                difficulty=difficulty,
                theme=theme,
                words=words,
                grid_diacritics=grid_diacritics,
                stats=stats,
            )
            puzzle.data["puzzle_number"] = puzzle_number
            validate_puzzle(puzzle)
            puzzles.append(puzzle)

    cover = _meta_page(
        "ws_cover",
        "OSMISMĚRKY",
        seed,
        instructions=(
            "Najděte v mřížce všechna slova uvedená pod osmisměrkou. "
            "Slova mohou být ukrytá vodorovně, svisle nebo šikmo a u náročnějších "
            "úloh také pozpátku. V mřížce jsou slova uvedena bez diakritiky "
            "(pokud není zapnuta diakritika). Písmeno CH zabírá dvě políčka."
            if not grid_diacritics
            else "Najděte v mřížce všechna slova. Slova mohou jít všemi směry. "
            "Písmeno CH zabírá dvě políčka."
        ),
        data={
            "pack_title": "OSMISMĚRKY",
            "pack_subtitle": "Tři úrovně obtížnosti · 18 osmisměrek",
            "easy": easy,
            "medium": medium,
            "hard": hard,
            "grid_diacritics": grid_diacritics,
            "edition_date": edition_cs,
            "edition_label": edition_label or "",
            "legend": [
                {"label": "LEHKÁ", "marker": "●○○", "detail": "10×10 · jen doprava a dolů"},
                {"label": "STŘEDNÍ", "marker": "●●○", "detail": "13×13 · všechny směry"},
                {"label": "TĚŽKÁ", "marker": "●●●", "detail": "16×16 · všechny směry"},
            ],
        },
    )

    pages_out: list[PuzzleBase] = [cover, *puzzles]

    # Solution pages
    for band_i, (fr, to) in enumerate(SOLUTION_BANDS, start=1):
        items = []
        for pz in puzzles:
            num = int(pz.data["puzzle_number"])
            if fr <= num <= to:
                items.append(
                    {
                        "page": num + 1,  # logical booklet page (cover=1)
                        "puzzle_number": num,
                        "title": pz.title,
                        "kind": "word_search",
                        "difficulty": pz.difficulty.value,
                        "answer": pz.answer,
                        "data": {
                            "size": pz.data["size"],
                            "grid": pz.data["grid"],
                            "theme": pz.data["theme"],
                            "theme_title": pz.data["theme_title"],
                            "difficulty_label_cs": pz.data["difficulty_label_cs"],
                            "difficulty_marker": pz.data["difficulty_marker"],
                        },
                    }
                )
        sol = _meta_page(
            "ws_solutions",
            f"Řešení {fr}–{to}",
            seed + 50_000 + band_i,
            instructions="Černá políčka s bílými písmeny ukazují umístění hledaných slov.",
            data={"from": fr, "to": to, "items": items if solutions else []},
        )
        if not solutions:
            sol.instructions = "Řešení v tomto vydání nejsou zahrnuta."
        pages_out.append(sol)

    if len(pages_out) != 24:
        raise ValueError(f"Expected 24 pages, got {len(pages_out)}")

    meta = {
        "generator_version": GENERATOR_VERSION,
        "vocabulary_version": VOCAB_VERSION,
        "vocabulary_path": str(default_vocab_path().relative_to(project_root())),
        "seed": seed,
        "locale": language,
        "difficulty_configuration": {
            "easy": easy,
            "medium": medium,
            "hard": hard,
            "specs": {
                k.value: {
                    "size": v["size"],
                    "word_count": v["word_count"],
                    "dirs": v["dirs"],
                }
                for k, v in DIFFICULTY_SPEC.items()
            },
        },
        "grid_diacritics": grid_diacritics,
        "solutions": solutions,
        "word_pools": pools,
        "generation_stats": stats.as_dict(),
        "used_word_count": len(used),
        "edition_date": edition_cs,
        "edition_date_iso": edition.isoformat(),
    }
    return [p.model_dump(mode="json") for p in pages_out], meta


def export_booklet_json(
    pages: list[dict[str, Any]],
    meta: dict[str, Any],
    path: Path | str,
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    puzzles = [p for p in pages if p["kind"] == "word_search"]
    payload = {
        **meta,
        "page_count": len(pages),
        "puzzle_count": len(puzzles),
        "puzzles": [
            {
                "puzzle_number": p["data"]["puzzle_number"],
                "theme": p["data"]["theme"],
                "theme_title": p["data"]["theme_title"],
                "difficulty": p["difficulty"],
                "original_words": p["data"]["words"],
                "normalized_words": p["data"]["words_normalized"],
                "grid": p["data"]["grid"],
                "placements": p["answer"]["placements"],
                "seed": p["seed"],
                "validation": {"placements_match_words": True},
            }
            for p in puzzles
        ],
        "pages": pages,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def compile_word_search_booklet(
    *,
    seed: int = 20270101,
    language: str = "cs",
    easy: int = 6,
    medium: int = 6,
    hard: int = 6,
    grid_diacritics: bool = False,
    solutions: bool = True,
    fold_guide: bool = True,
    output: Path | str | None = None,
    pages_output: Path | str | None = None,
    json_output: Path | str | None = None,
    theme: Theme | None = None,
    impose: bool = True,
    preferred_theme: str | None = None,
    edition_date: date | None = None,
    edition_label: str | None = None,
) -> dict[str, Path]:
    theme = theme or load_theme()
    stats = GenerationStats()
    edition = edition_date or edition_date_from_seed(seed)
    infix = edition.strftime("%Y%m%d")
    pages, meta = build_word_search_booklet_pages(
        seed=seed,
        language=language,
        easy=easy,
        medium=medium,
        hard=hard,
        grid_diacritics=grid_diacritics,
        solutions=solutions,
        stats=stats,
        preferred_theme=preferred_theme,
        edition_date=edition,
        edition_label=edition_label,
    )

    json_path = Path(json_output) if json_output else (
        project_root() / "generated" / f"word-search-{language}-seed-{seed}.json"
    )
    export_booklet_json(pages, meta, json_path)

    data = {
        "page_type": "word_search_booklet",
        "theme": theme.to_typst_dict(),
        "pages": pages,
        "title": "OSMISMĚRKY",
        "meta": meta,
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
            / f"creobook-{infix}-osmismerky-{language}-a5.pdf"
        )
    pages_pdf.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", data, pages_pdf, theme=theme)

    result: dict[str, Path] = {"pages": pages_pdf, "json": json_path}

    if impose:
        booklet_pdf = Path(output) if output else (
            project_root()
            / "output"
            / "booklet"
            / f"creobook-{infix}-osmismerky.pdf"
        )
        booklet_pdf.parent.mkdir(parents=True, exist_ok=True)
        impose_booklet(pages_pdf, booklet_pdf, theme=theme, fold_guide=fold_guide)
        result["booklet"] = booklet_pdf

        spreads = booklet_spreads(24)
        if spreads != EXPECTED_SPREADS:
            raise ValueError(f"Unexpected booklet order: {spreads}")

    return result
