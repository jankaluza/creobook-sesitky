"""32-page CreoBook booklet „Hry pro dva“.

Four pencil-and-paper games, mixed so the same game does not form a long
block. Lodě and Město, jméno, zvíře, věc stay in facing pairs for two players.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from creobook.compiler import compile_template
from creobook.imposition import booklet_spreads, impose_booklet
from creobook.theme import Theme, load_theme, project_root
from creobook.validation import (
    check_a4_landscape_sheets,
    check_a5_pages,
    check_content_within_media_box,
    check_page_count,
    extract_page_text,
)

PAGE_COUNT = 32
SHEET_COUNT = 8

# After the cover and the rules page. Counts: 10 + 8 + 6 + 6 = 30.
GAME_PATTERN: tuple[str, ...] = (
    "piskvorky",
    "ctverecky",
    "lode",
    "lode",
    "piskvorky",
    "mesto",
    "mesto",
    "ctverecky",
    "piskvorky",
    "lode",
    "lode",
    "ctverecky",
    "piskvorky",
    "piskvorky",
    "mesto",
    "mesto",
    "piskvorky",
    "lode",
    "lode",
    "ctverecky",
    "piskvorky",
    "mesto",
    "mesto",
    "ctverecky",
    "piskvorky",
    "lode",
    "lode",
    "ctverecky",
    "piskvorky",
    "piskvorky",
)

EXPECTED_COUNTS = {
    "cover": 1,
    "rules": 1,
    "piskvorky": 10,
    "lode": 8,
    "ctverecky": 6,
    "mesto": 6,
}

# A5 body inside the booklet margins. The spine side is wider.
LAYOUT: dict[str, Any] = {
    "page_width_mm": 148.0,
    "page_height_mm": 210.0,
    "margin_inside_mm": 12.0,
    "margin_outside_mm": 9.0,
    "margin_top_mm": 8.0,
    "margin_bottom_mm": 9.0,
    "piskvorky": {
        "cols": 23,
        "rows": 32,
        "cell_mm": 5.5,
        "title_mm": 5.0,
        "space_mm": 1.2,
        "names_mm": 6.5,
    },
    "lode": {
        "size": 10,
        "cell_mm": 7.5,
        "label_mm": 4.2,
        "title_mm": 8.0,
        "fleet_mm": 0.0,
        "sample_mm": 5.0,
        "space_mm": 2.0,
        "columns": list("ABCDEFGHIJ"),
        "rows": list(range(1, 11)),
        "fleet": (
            {"count": 1, "length": 4},
            {"count": 2, "length": 3},
            {"count": 3, "length": 2},
            {"count": 4, "length": 1},
        ),
    },
    "ctverecky": {
        "cols": 15,
        "rows": 19,
        "gap_mm": 8.9,
        "dot_radius_mm": 0.55,
        "title_mm": 5.0,
        "space_mm": 1.5,
        "score_gap_mm": 4.0,
        "score_mm": 12.0,
    },
    "mesto": {
        "rows": 18,
        "row_mm": 8.5,
        "header_mm": 7.0,
        "total_mm": 8.0,
        "title_mm": 4.5,
        "name_mm": 6.5,
        "space_mm": 1.5,
        "columns": (
            {"title": "Písmeno", "width_mm": 18.0},
            {"title": "Město", "width_mm": 25.0},
            {"title": "Jméno", "width_mm": 25.0},
            {"title": "Zvíře", "width_mm": 23.0},
            {"title": "Věc", "width_mm": 23.0},
            {"title": "Body", "width_mm": 13.0},
        ),
    },
}


def content_size(layout: dict[str, Any] | None = None) -> tuple[float, float]:
    layout = layout or LAYOUT
    width = layout["page_width_mm"] - layout["margin_inside_mm"] - layout["margin_outside_mm"]
    height = layout["page_height_mm"] - layout["margin_top_mm"] - layout["margin_bottom_mm"]
    return width, height


def _content_box() -> tuple[float, float]:
    return content_size(LAYOUT)


def validate_layout(layout: dict[str, Any] | None = None) -> None:
    """Reject a board that would leave the A5 body or break the size brief."""
    layout = layout or LAYOUT
    width, height = content_size(layout)
    errors: list[str] = []

    pisk = layout["piskvorky"]
    grid_w = pisk["cols"] * pisk["cell_mm"]
    grid_h = pisk["rows"] * pisk["cell_mm"]
    pisk_h = pisk["title_mm"] + pisk["space_mm"] + grid_h + pisk["space_mm"] + pisk["names_mm"]
    if not 5.0 <= pisk["cell_mm"] <= 6.0:
        errors.append(f"piškvorky cell {pisk['cell_mm']} mm is outside 5–6 mm")
    if grid_w > width + 0.05:
        errors.append(f"piškvorky grid width {grid_w:.1f} mm exceeds {width:.1f} mm")
    if pisk_h > height + 0.05:
        errors.append(f"piškvorky page height {pisk_h:.1f} mm exceeds {height:.1f} mm")

    lode = layout["lode"]
    board_w = lode["label_mm"] + lode["size"] * lode["cell_mm"]
    board_h = lode["label_mm"] + lode["size"] * lode["cell_mm"]
    lode_h = (
        lode["title_mm"]
        + lode["fleet_mm"]
        + lode["space_mm"]
        + board_h
        + lode["space_mm"]
        + board_h
    )
    if lode["columns"] != list("ABCDEFGHIJ") or lode["rows"] != list(range(1, 11)):
        errors.append("lodě coordinates must be A–J and 1–10")
    if lode["size"] != 10:
        errors.append("lodě grid must be 10×10")
    fleet = lode["fleet"]
    expected_fleet = ((1, 4), (2, 3), (3, 2), (4, 1))
    actual_fleet = tuple((item["count"], item["length"]) for item in fleet)
    if actual_fleet != expected_fleet:
        errors.append(f"fleet {actual_fleet} != {expected_fleet}")
    legend_w = 8.0 + lode["sample_mm"]
    side_gap = (width - board_w) / 2
    if legend_w > side_gap - 1.5:
        errors.append(
            f"lodě shape key is {legend_w:.1f} mm wide and the side gap is only {side_gap:.1f} mm"
        )
    if board_w > width + 0.05:
        errors.append(f"lodě board width {board_w:.1f} mm exceeds {width:.1f} mm")
    if lode_h > height + 0.05:
        errors.append(f"lodě page height {lode_h:.1f} mm exceeds {height:.1f} mm")

    dots = layout["ctverecky"]
    radius = dots["dot_radius_mm"]
    field_w = (dots["cols"] - 1) * dots["gap_mm"] + 2 * radius
    field_h = (dots["rows"] - 1) * dots["gap_mm"] + 2 * radius
    dots_h = (
        dots["title_mm"]
        + dots["space_mm"]
        + field_h
        + dots["score_gap_mm"]
        + dots["score_mm"]
    )
    if not 8.0 <= dots["gap_mm"] <= 10.0:
        errors.append(f"čtverečky gap {dots['gap_mm']} mm is outside 8–10 mm")
    if field_w > width + 0.05:
        errors.append(f"čtverečky width {field_w:.1f} mm exceeds {width:.1f} mm")
    if dots_h > height + 0.05:
        errors.append(f"čtverečky page height {dots_h:.1f} mm exceeds {height:.1f} mm")

    city = layout["mesto"]
    columns = city["columns"]
    titles = [column["title"] for column in columns]
    if titles != ["Písmeno", "Město", "Jméno", "Zvíře", "Věc", "Body"]:
        errors.append(f"unexpected category columns: {titles}")
    col_w = sum(column["width_mm"] for column in columns)
    if col_w > width + 0.05:
        errors.append(f"category table width {col_w:.1f} mm exceeds {width:.1f} mm")
    if city["row_mm"] < 8.0:
        errors.append(f"category row {city['row_mm']} mm is tight for handwriting")
    city_h = (
        city["title_mm"]
        + city["name_mm"]
        + city["space_mm"]
        + city["header_mm"]
        + city["rows"] * city["row_mm"]
        + city["total_mm"]
    )
    if city_h > height + 0.05:
        errors.append(f"category page height {city_h:.1f} mm exceeds {height:.1f} mm")
    word_widths = [column["width_mm"] for column in columns if column["title"] != "Body"]
    points = next(column["width_mm"] for column in columns if column["title"] == "Body")
    if points >= min(word_widths):
        errors.append("the points column should be narrower than the word columns")

    if errors:
        raise ValueError("\n".join(errors))


def _pair_heading(kind_pages: list[dict[str, Any]]) -> None:
    match = 0
    index = 0
    while index < len(kind_pages):
        page = kind_pages[index]
        nxt = kind_pages[index + 1] if index + 1 < len(kind_pages) else None
        if nxt is None or nxt["number"] != page["number"] + 1:
            raise ValueError(f"{page['kind']} on page {page['number']} is not part of a pair")
        match += 1
        for player, item in ((1, page), (2, nxt)):
            item["match"] = match
            item["player"] = player
            item["heading"] = f"Partie {match} — Hráč {player}"
        index += 2


def build_page_plan() -> list[dict[str, Any]]:
    """Return the 32 pages in reading order and check the brief before rendering."""
    validate_layout()
    pages: list[dict[str, Any]] = [
        {
            "kind": "cover",
            "number": 1,
            "title": "HRY PRO DVA",
            "subtitle": "Stačí tužka, papír a spoluhráč.",
            "footer": "CreoBook.cz",
        },
        {
            "kind": "rules",
            "number": 2,
            "title": "Pravidla",
        },
    ]
    for offset, kind in enumerate(GAME_PATTERN, start=3):
        page: dict[str, Any] = {"kind": kind, "number": offset}
        if kind == "piskvorky":
            page["title"] = "PIŠKVORKY"
        elif kind == "lode":
            page["title"] = "LODĚ"
        elif kind == "ctverecky":
            page["title"] = "ČTVEREČKY"
        elif kind == "mesto":
            page["title"] = "MĚSTO, JMÉNO, ZVÍŘE, VĚC"
        else:
            raise ValueError(f"unknown game {kind}")
        pages.append(page)

    _pair_heading([page for page in pages if page["kind"] == "lode"])
    _pair_heading([page for page in pages if page["kind"] == "mesto"])
    validate_plan(pages)
    return pages


def validate_plan(pages: list[dict[str, Any]]) -> None:
    errors: list[str] = []
    if len(pages) != PAGE_COUNT:
        errors.append(f"expected {PAGE_COUNT} pages, got {len(pages)}")
    numbers = [page["number"] for page in pages]
    if numbers != list(range(1, PAGE_COUNT + 1)):
        errors.append("page numbers are not 1..32 in order")

    counts: dict[str, int] = {}
    for page in pages:
        counts[page["kind"]] = counts.get(page["kind"], 0) + 1
    if counts != EXPECTED_COUNTS:
        errors.append(f"page counts {counts} != {EXPECTED_COUNTS}")

    if pages and (pages[0]["kind"] != "cover" or pages[1]["kind"] != "rules"):
        errors.append("booklet must open with the cover and the rules")

    kinds = [page["kind"] for page in pages]
    run = 1
    for prev, kind in zip(kinds, kinds[1:]):
        run = run + 1 if kind == prev else 1
        if run > 2:
            errors.append(f"{kind} repeats {run} times in a row")

    games = [page for page in pages if page["kind"] not in {"cover", "rules"}]
    for index, page in enumerate(games):
        if page["kind"] != "ctverecky":
            continue
        neighbors = []
        if index > 0:
            neighbors.append(games[index - 1]["kind"])
        if index + 1 < len(games):
            neighbors.append(games[index + 1]["kind"])
        if "ctverecky" in neighbors:
            errors.append(f"čtverečky on page {page['number']} touch another dots page")

    for kind in ("lode", "mesto"):
        grouped = [page for page in pages if page["kind"] == kind]
        if len(grouped) % 2:
            errors.append(f"{kind} page count is odd")
        for index in range(0, len(grouped), 2):
            first, second = grouped[index], grouped[index + 1]
            if second["number"] != first["number"] + 1:
                errors.append(f"{kind} pair is not on neighbouring pages")
            if first.get("player") != 1 or second.get("player") != 2:
                errors.append(f"{kind} pair is not labelled Hráč 1 then Hráč 2")
            if first.get("match") != second.get("match"):
                errors.append(f"{kind} pair does not share a match number")

    game_counts = {kind: counts.get(kind, 0) for kind in ("piskvorky", "lode", "ctverecky", "mesto")}
    if game_counts["piskvorky"] <= max(game_counts["lode"], game_counts["ctverecky"], game_counts["mesto"]):
        errors.append("piškvorky should be the most frequent game")

    if errors:
        raise ValueError("\n".join(errors))


def booklet_data(theme: Theme | None = None) -> dict[str, Any]:
    theme = theme or load_theme()
    return {
        "page_type": "hry_pro_dva",
        "theme": theme.to_typst_dict(),
        "title": "Hry pro dva",
        "layout": LAYOUT,
        "pages": build_page_plan(),
    }


def expected_print_order() -> list[tuple[int, int]]:
    """Front and back of each A4 sheet. First sheet is (32, 1) then (2, 31)."""
    spreads = booklet_spreads(PAGE_COUNT)
    if any(left is None or right is None for left, right in spreads):
        raise ValueError("32-page booklet must not contain blank pads")
    return [(int(left), int(right)) for left, right in spreads]


def _check(result_ok: bool, messages: list[str], sink: list[str]) -> None:
    sink.extend(messages)
    if not result_ok:
        raise ValueError("; ".join(messages))


def check_outputs(pages_pdf: Path, print_pdf: Path) -> list[str]:
    """Open both PDFs and check the brief: counts, size, language, imposition."""
    notes: list[str] = []
    for path in (pages_pdf, print_pdf):
        if not path.is_file() or path.stat().st_size < 1000:
            raise ValueError(f"missing or empty PDF: {path}")
    notes.append(f"A5 {pages_pdf.name} ({pages_pdf.stat().st_size} B)")
    notes.append(f"A4 {print_pdf.name} ({print_pdf.stat().st_size} B)")

    count = check_page_count(pages_pdf, PAGE_COUNT)
    _check(count.ok, count.messages, notes)
    sheets = check_page_count(print_pdf, SHEET_COUNT * 2)
    _check(sheets.ok, sheets.messages, notes)
    a5 = check_a5_pages(pages_pdf)
    _check(a5.ok, a5.messages, notes)
    a4 = check_a4_landscape_sheets(print_pdf)
    _check(a4.ok, a4.messages, notes)
    for pdf in (pages_pdf, print_pdf):
        boxes = check_content_within_media_box(pdf)
        _check(boxes.ok, boxes.messages, notes)

    texts = extract_page_text(pages_pdf)
    if len(texts) != PAGE_COUNT:
        raise ValueError("could not read 32 A5 pages")
    joined = "\n".join(texts)
    for token in ("Piškvorky", "Lodě", "Čtverečky", "Město", "zvíře", "věc", "diagonálně"):
        if token not in joined:
            raise ValueError(f"Czech text {token!r} missing from the A5 PDF")
    notes.append("Czech diacritics present")

    def titled(marker: str) -> int:
        return sum(1 for text in texts if marker in text)

    found = {
        "piskvorky": titled("PIŠKVORKY"),
        "lode": titled("LODĚ"),
        "ctverecky": titled("ČTVEREČKY"),
        "mesto": titled("MĚSTO, JMÉNO, ZVÍŘE, VĚC"),
    }
    for kind, expected in (
        ("piskvorky", 10),
        ("lode", 8),
        ("ctverecky", 6),
        ("mesto", 6),
    ):
        if found[kind] != expected:
            raise ValueError(f"{kind}: found {found[kind]} pages, expected {expected}")
    notes.append("game page counts match the brief")

    if "HRY PRO DVA" not in texts[0] or "CreoBook.cz" not in texts[0]:
        raise ValueError("cover is missing the title or CreoBook.cz")
    if "Pravidla" not in texts[1]:
        raise ValueError("rules page is missing")

    lode_text = "\n".join(text for text in texts if "Moje lodě" in text)
    for label in list("ABCDEFGHIJ") + ["10", "Moje střely"]:
        if label not in lode_text:
            raise ValueError(f"lodě page is missing {label!r}")
    for match in range(1, 5):
        if f"Partie {match}" not in lode_text:
            raise ValueError(f"missing lodě Partie {match}")
    notes.append("lodě coordinates, fleet pages and match labels OK")

    order = expected_print_order()
    if order[0] != (32, 1) or order[1] != (2, 31):
        raise ValueError(f"unexpected first sheet: {order[:2]}")
    imposed = extract_page_text(print_pdf)
    if "HRY PRO DVA" not in imposed[0] or "PIŠKVORKY" not in imposed[0]:
        raise ValueError("first A4 side should carry pages 32 and 1")
    if "Pravidla" not in imposed[1] or "PIŠKVORKY" not in imposed[1]:
        raise ValueError("second A4 side should carry pages 2 and 31")
    notes.append("booklet order (32|1) then (2|31)")
    return notes


def render_previews(pages_pdf: Path, preview_dir: Path) -> list[Path]:
    """Raster previews of one page of each kind, for a visual check."""
    binary = shutil.which("pdftoppm")
    if binary is None:
        raise RuntimeError("pdftoppm is not installed")
    pages = build_page_plan()
    preview_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    seen: set[str] = set()
    for page in pages:
        kind = page["kind"]
        if kind in seen:
            continue
        seen.add(kind)
        dest = preview_dir / f"hry-pro-dva-{kind}"
        subprocess.run(
            [
                binary,
                "-f",
                str(page["number"]),
                "-l",
                str(page["number"]),
                "-png",
                "-r",
                "130",
                "-singlefile",
                str(pages_pdf),
                str(dest),
            ],
            check=True,
            capture_output=True,
        )
        written.append(dest.with_suffix(".png"))
    return written


def compile_hry_pro_dva(
    *,
    output_dir: Path | str | None = None,
    preview_dir: Path | str | None = None,
    theme: Theme | None = None,
    previews: bool = True,
) -> dict[str, Any]:
    """Write the A5 reading-order PDF and the A4 landscape booklet PDF."""
    theme = theme or load_theme()
    root = project_root()
    out = Path(output_dir) if output_dir else root / "output" / "booklet"
    out.mkdir(parents=True, exist_ok=True)
    pages_pdf = out / "hry-pro-dva-a5.pdf"
    print_pdf = out / "hry-pro-dva-tisk-a4.pdf"

    compile_template("games/two_player_booklet.typ", booklet_data(theme), pages_pdf, theme=theme)
    impose_booklet(pages_pdf, print_pdf, theme=theme, fold_guide=False)
    notes = check_outputs(pages_pdf, print_pdf)

    result: dict[str, Any] = {"pages": pages_pdf, "booklet": print_pdf, "notes": notes}
    if previews:
        shots = render_previews(
            pages_pdf,
            Path(preview_dir) if preview_dir else root / "output" / "preview" / "hry-pro-dva",
        )
        for shot in shots:
            result[shot.stem] = shot
    return result
