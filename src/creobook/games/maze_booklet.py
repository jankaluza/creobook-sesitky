"""Assemble the 24-page Czech maze booklet (BLUDIŠTĚ)."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from creobook.compiler import compile_template
from creobook.games.maze import (
    GENERATOR_VERSION,
    SCORE_RANGES,
    SCORE_WEIGHTS,
    generate_scored_maze,
    scored_to_puzzle,
)
from creobook.games.models import Difficulty, PuzzleBase
from creobook.games.validation import validate_puzzle
from creobook.games.word_search_booklet import (
    EXPECTED_SPREADS,
    SOLUTION_BANDS,
    edition_date_from_seed,
    format_edition_date_cs,
)
from creobook.imposition import booklet_spreads, impose_booklet
from creobook.theme import Theme, load_theme, project_root


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


def build_maze_booklet_pages(
    *,
    seed: int = 20270101,
    locale: str = "cs-CZ",
    easy: int = 6,
    medium: int = 6,
    hard: int = 6,
    maze_style: str = "rectangular",
    solutions: bool = True,
    edition_date: date | None = None,
    edition_label: str | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if locale not in {"cs", "cs-CZ"}:
        raise ValueError("Only Czech locale (cs / cs-CZ) is supported")
    if maze_style != "rectangular":
        raise ValueError(f"Unsupported maze style: {maze_style}")
    total = easy + medium + hard
    if total != 18:
        raise ValueError(
            f"Booklet expects 18 mazes (6+6+6); got {easy}+{medium}+{hard}={total}"
        )

    edition = edition_date or edition_date_from_seed(seed)
    edition_cs = format_edition_date_cs(edition)

    puzzles: list[PuzzleBase] = []
    maze_number = 0
    attempt_total = 0
    scores: dict[str, list[float]] = {"easy": [], "medium": [], "hard": []}

    plan = [
        (Difficulty.easy, easy),
        (Difficulty.medium, medium),
        (Difficulty.hard, hard),
    ]
    for difficulty, count in plan:
        for _ in range(count):
            maze_number += 1
            page_seed = seed * 1009 + maze_number * 9176 + {
                Difficulty.easy: 1,
                Difficulty.medium: 2,
                Difficulty.hard: 3,
            }[difficulty]
            scored = generate_scored_maze(seed=page_seed, difficulty=difficulty)
            attempt_total += scored.attempt
            scores[difficulty.value].append(scored.metrics.difficulty_score)
            puzzle = scored_to_puzzle(
                scored,
                difficulty=difficulty,
                maze_number=maze_number,
                title=f"Bludiště {maze_number}",
            )
            puzzle.data["maze_style"] = maze_style
            validate_puzzle(puzzle)
            puzzles.append(puzzle)

    cover = _meta_page(
        "maze_cover",
        "BLUDIŠTĚ",
        seed,
        instructions=(
            "Najděte cestu od značky START až k CÍLI. Čáru veďte pouze volnými "
            "průchody a nepřekračujte stěny bludiště. Pokud se cesta uzavře, vraťte "
            "se k poslednímu rozcestí a vyzkoušejte jiný směr."
        ),
        data={
            "pack_title": "BLUDIŠTĚ",
            "pack_subtitle": "Lehká, střední a těžká",
            "edition_date": edition_cs,
            "edition_label": edition_label or "",
            "legend": [
                {"label": "LEHKÁ", "marker": "●○○", "detail": "12×16 · kratší cesta"},
                {"label": "STŘEDNÍ", "marker": "●●○", "detail": "18×24 · více odboček"},
                {"label": "TĚŽKÁ", "marker": "●●●", "detail": "26×34 · husté bludiště"},
            ],
        },
    )

    pages_out: list[PuzzleBase] = [cover, *puzzles]

    for band_i, (fr, to) in enumerate(SOLUTION_BANDS, start=1):
        items = []
        for pz in puzzles:
            num = int(pz.data["maze_number"])
            if fr <= num <= to:
                items.append(
                    {
                        "puzzle_number": num,
                        "title": pz.title,
                        "kind": "maze",
                        "difficulty": pz.difficulty.value,
                        "answer": pz.answer,
                        "data": {
                            "rows": pz.data["rows"],
                            "cols": pz.data["cols"],
                            "edges": pz.data["edges"],
                            "start": pz.data["start"],
                            "goal": pz.data["goal"],
                            "difficulty_label_cs": pz.data["difficulty_label_cs"],
                            "difficulty_marker": pz.data["difficulty_marker"],
                            "wall_pt": pz.data["wall_pt"],
                        },
                    }
                )
        sol = _meta_page(
            "maze_solutions",
            f"Řešení {fr}–{to}",
            seed + 60_000 + band_i,
            instructions="Šedá čára vyznačuje cestu od START k CÍLI.",
            data={"from": fr, "to": to, "items": items if solutions else []},
        )
        if not solutions:
            sol.instructions = "Řešení v tomto vydání nejsou zahrnuta."
        pages_out.append(sol)

    if len(pages_out) != 24:
        raise ValueError(f"Expected 24 pages, got {len(pages_out)}")

    def _avg(vals: list[float]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    meta = {
        "generator_version": GENERATOR_VERSION,
        "seed": seed,
        "locale": locale,
        "maze_style": maze_style,
        "solutions": solutions,
        "edition_date": edition_cs,
        "edition_date_iso": edition.isoformat(),
        "difficulty_configuration": {
            "easy": easy,
            "medium": medium,
            "hard": hard,
            "score_ranges": {k.value: list(v) for k, v in SCORE_RANGES.items()},
            "score_weights": SCORE_WEIGHTS,
        },
        "generation_stats": {
            "total_attempts": attempt_total,
            "average_attempts_per_maze": attempt_total / 18,
            "average_scores": {k: _avg(v) for k, v in scores.items()},
            "scores": scores,
        },
    }
    return [p.model_dump(mode="json") for p in pages_out], meta


def export_maze_json(
    pages: list[dict[str, Any]], meta: dict[str, Any], path: Path | str
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    mazes = [p for p in pages if p["kind"] == "maze"]
    payload = {
        **meta,
        "page_count": len(pages),
        "maze_count": len(mazes),
        "mazes": [
            {
                "maze_number": m["data"]["maze_number"],
                "difficulty": m["difficulty"],
                "rows": m["data"]["rows"],
                "cols": m["data"]["cols"],
                "start": m["data"]["start"],
                "goal": m["data"]["goal"],
                "start_opening": m["data"]["start_opening"],
                "goal_opening": m["data"]["goal_opening"],
                "walls": m["data"]["walls"],
                "cells": m["data"]["cells"],
                "solution_path": m["answer"]["path"],
                "metrics": m["data"]["metrics"],
                "generation": m["data"]["generation"],
                "validation": {"ok": True},
                "seed": m["seed"],
            }
            for m in mazes
        ],
        "pages": pages,
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def compile_maze_booklet(
    *,
    seed: int = 20270101,
    locale: str = "cs-CZ",
    easy: int = 6,
    medium: int = 6,
    hard: int = 6,
    maze_style: str = "rectangular",
    solutions: bool = True,
    fold_guide: bool = True,
    output: Path | str | None = None,
    pages_output: Path | str | None = None,
    json_output: Path | str | None = None,
    theme: Theme | None = None,
    impose: bool = True,
    edition_date: date | None = None,
    edition_label: str | None = None,
) -> dict[str, Path]:
    theme = theme or load_theme()
    edition = edition_date or edition_date_from_seed(seed)
    infix = edition.strftime("%Y%m%d")
    pages, meta = build_maze_booklet_pages(
        seed=seed,
        locale=locale,
        easy=easy,
        medium=medium,
        hard=hard,
        maze_style=maze_style,
        solutions=solutions,
        edition_date=edition,
        edition_label=edition_label,
    )

    json_path = Path(json_output) if json_output else (
        project_root() / "generated" / f"maze-cs-seed-{seed}.json"
    )
    export_maze_json(pages, meta, json_path)

    data = {
        "page_type": "maze_booklet",
        "theme": theme.to_typst_dict(),
        "pages": pages,
        "title": "BLUDIŠTĚ",
        "meta": meta,
    }

    if pages_output is not None:
        pages_pdf = Path(pages_output)
    elif output is not None:
        out = Path(output)
        pages_pdf = out.with_name(out.stem + "-pages.pdf")
    else:
        pages_pdf = (
            project_root() / "output" / "pages" / f"creobook-{infix}-bludiste-a5.pdf"
        )
    pages_pdf.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", data, pages_pdf, theme=theme)

    result: dict[str, Path] = {"pages": pages_pdf, "json": json_path}

    if impose:
        booklet_pdf = Path(output) if output else (
            project_root() / "output" / "booklet" / f"creobook-{infix}-bludiste.pdf"
        )
        booklet_pdf.parent.mkdir(parents=True, exist_ok=True)
        impose_booklet(pages_pdf, booklet_pdf, theme=theme, fold_guide=fold_guide)
        result["booklet"] = booklet_pdf
        if booklet_spreads(24) != EXPECTED_SPREADS:
            raise ValueError("Unexpected booklet order")

    return result
