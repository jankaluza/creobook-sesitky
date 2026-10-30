"""Assemble game booklet page data and compile to PDF."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from creobook.compiler import compile_template
from creobook.games import get_generator  # noqa: F401 — ensures registration
from creobook.games.base import get_generator as _get, resolve_difficulty
from creobook.games.models import (
    BookletBuildOptions,
    Difficulty,
    PackConfig,
    PageSpec,
    PuzzleBase,
)
from creobook.games.validation import validate_puzzle
from creobook.imposition import impose_booklet, pad_page_count
from creobook.theme import Theme, load_theme, project_root


def packs_dir() -> Path:
    return project_root() / "config" / "games" / "packs"


def load_pack(pack_id: str) -> PackConfig:
    path = packs_dir() / f"{pack_id}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Pack not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return PackConfig.model_validate(raw)


def _page_seed(base: int, index: int) -> int:
    return base * 1009 + index * 9176 + 13


def _meta_page(
    kind: str,
    title: str,
    seed: int,
    difficulty: Difficulty,
    *,
    instructions: str = "",
    data: dict[str, Any] | None = None,
) -> PuzzleBase:
    return PuzzleBase(
        kind=kind,
        title=title,
        instructions=instructions,
        difficulty=difficulty,
        seed=seed,
        data=data or {},
        answer={},
    )


def build_page(
    spec: PageSpec,
    *,
    seed: int,
    difficulty: Difficulty,
    pack: PackConfig,
    puzzle_index: int,
) -> PuzzleBase:
    kind = spec.kind
    params = dict(spec.params)
    if spec.theme:
        params.setdefault("theme", spec.theme)
    if spec.variant:
        params.setdefault("variant", spec.variant)
    if spec.size:
        params.setdefault("size", spec.size)

    if kind in {
        "cover",
        "instructions",
        "rules",
        "back",
        "solutions",
        "free_grid",
        "score_table",
    }:
        data: dict[str, Any] = {
            "pack_title": pack.title,
            "pack_subtitle": pack.subtitle,
            "pack_description": pack.description,
        }
        data.update(params)
        instructions = {
            "cover": pack.subtitle,
            "instructions": "Vyber hru, přečti si zadání a vyřeš tužkou. Řešení najdeš na konci sešitu.",
            "rules": "Krátký přehled pravidel pro hry v tomto sešitě.",
            "back": pack.description,
            "solutions": "Kompaktní řešení vybraných stran.",
            "free_grid": "Nakresli si vlastní hru nebo použij mřížku volně.",
            "score_table": "Zapisuj body jednotlivých her a partií.",
        }.get(kind, "")
        return _meta_page(
            kind,
            spec.title or kind,
            seed,
            difficulty,
            instructions=instructions,
            data=data,
        )

    if kind == "bonus":
        inner = params.get("game", "sudoku")
        gen = _get(inner)
        inner_params = {k: v for k, v in params.items() if k != "game"}
        puzzle = gen.generate(
            seed=seed,
            difficulty=difficulty,
            title=spec.title,
            params=inner_params,
        )
        validate_puzzle(puzzle)
        return puzzle

    gen = _get(kind)
    puzzle = gen.generate(
        seed=seed,
        difficulty=difficulty,
        title=spec.title,
        params=params,
    )
    validate_puzzle(puzzle)
    return puzzle


def build_booklet_pages(
    pack: PackConfig,
    *,
    sheets: int | None = None,
    difficulty: Difficulty | None = None,
    seed: int | None = None,
    answers: bool | None = None,
    edition_label: str | None = None,
) -> list[dict[str, Any]]:
    sheets = sheets if sheets is not None else pack.sheets
    difficulty = difficulty if difficulty is not None else pack.difficulty
    seed = seed if seed is not None else pack.seed
    include_answers = pack.answers if answers is None else answers

    target = sheets * 4
    pages_out: list[PuzzleBase] = []
    puzzle_pages: list[tuple[int, PuzzleBase]] = []  # 1-based logical index

    for i, spec in enumerate(pack.pages):
        diff = resolve_difficulty(spec, difficulty, i)
        page_seed = _page_seed(seed, i)
        puzzle = build_page(
            spec,
            seed=page_seed,
            difficulty=diff,
            pack=pack,
            puzzle_index=i,
        )
        pages_out.append(puzzle)
        if puzzle.kind not in {
            "cover",
            "instructions",
            "rules",
            "back",
            "solutions",
            "free_grid",
            "score_table",
        }:
            puzzle_pages.append((len(pages_out), puzzle))

    # Attach answer payloads into solutions pages
    for i, page in enumerate(pages_out):
        if page.kind != "solutions":
            continue
        fr = int(page.data.get("from", 1))
        to = int(page.data.get("to", fr))
        items = []
        for idx, pz in puzzle_pages:
            if not (fr <= idx <= to):
                continue
            if pz.kind == "sudoku" and len(pz.data.get("puzzles") or []) > 1:
                for slot, (puz, ans) in enumerate(
                    zip(pz.data["puzzles"], pz.answer["puzzles"], strict=True),
                    start=1,
                ):
                    items.append(
                        {
                            "page": idx,
                            "sub": slot,
                            "title": f"{pz.title} · {slot}",
                            "kind": "sudoku",
                            "answer": {"grid": ans["grid"]},
                            "data": {
                                "size": pz.data["size"],
                                "grid": puz["grid"],
                                "box": pz.data["box"],
                            },
                        }
                    )
            else:
                items.append(
                    {
                        "page": idx,
                        "title": pz.title,
                        "kind": pz.kind,
                        "answer": pz.answer,
                        "data": pz.data,
                    }
                )
        page.data["items"] = items
        if not include_answers:
            page.data["items"] = []
            page.instructions = "Řešení v tomto vydání nejsou zahrnuta."

    # Pad / trim to exact sheet capacity
    while len(pages_out) < target:
        pages_out.append(
            _meta_page(
                "free_grid",
                "Volná stránka",
                _page_seed(seed, len(pages_out)),
                Difficulty.easy,
                instructions="Volná stránka pro poznámky.",
                data={"grid": 10},
            )
        )
    if len(pages_out) > target:
        pages_out = pages_out[:target]

    assert len(pages_out) == target
    assert pad_page_count(len(pages_out)) == len(pages_out)
    if edition_label and pages_out and pages_out[0].kind == "cover":
        pages_out[0].data["edition_label"] = edition_label

    return [p.model_dump(mode="json") for p in pages_out]


def build_booklet_data(
    options: BookletBuildOptions,
    theme: Theme | None = None,
) -> dict[str, Any]:
    pack = load_pack(options.pack_id)
    theme = (theme or load_theme()).with_accent(options.accent)
    pages = build_booklet_pages(
        pack,
        sheets=options.sheets,
        difficulty=options.difficulty,
        seed=options.seed,
        answers=options.answers,
        edition_label=options.edition_label,
    )
    return {
        "page_type": "games_booklet",
        "pack": pack.model_dump(mode="json"),
        "pages": pages,
        "theme": theme.to_typst_dict(),
        "title": pack.title,
    }


def compile_games_booklet(
    options: BookletBuildOptions,
    output_pdf: Path | str,
    *,
    theme: Theme | None = None,
    impose: bool = True,
    booklet_output: Path | str | None = None,
) -> dict[str, Path]:
    """Compile logical A5 game booklet; optionally impose to A4 landscape."""
    theme = (theme or load_theme()).with_accent(options.accent)
    data = build_booklet_data(options, theme=theme)
    out = Path(output_pdf)
    out.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", data, out, theme=theme)
    result = {"pages": out}
    if impose:
        bout = Path(booklet_output) if booklet_output else out.with_name(
            out.stem + "-booklet.pdf"
        )
        impose_booklet(out, bout, theme=theme)
        result["booklet"] = bout
    return result


def compile_single_game(
    kind: str,
    output_pdf: Path | str,
    *,
    seed: int = 42,
    difficulty: Difficulty = Difficulty.easy,
    theme_name: str | None = None,
    params: dict[str, Any] | None = None,
    accent: str | None = None,
) -> Path:
    import creobook.games  # noqa: F401

    theme = load_theme().with_accent(accent)
    p = dict(params or {})
    if theme_name:
        p["theme"] = theme_name
    puzzle = _get(kind).generate(
        seed=seed, difficulty=difficulty, params=p
    )
    validate_puzzle(puzzle)
    data = {
        "page_type": "games_single",
        "theme": theme.to_typst_dict(),
        "pages": [puzzle.model_dump(mode="json")],
        "title": puzzle.title,
    }
    out = Path(output_pdf)
    out.parent.mkdir(parents=True, exist_ok=True)
    compile_template("games/booklet.typ", data, out, theme=theme)
    return out
