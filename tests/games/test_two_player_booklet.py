"""Layout and print checks for the Hry pro dva booklet."""

from __future__ import annotations

from creobook.games.two_player_booklet import (
    EXPECTED_COUNTS,
    PAGE_COUNT,
    build_page_plan,
    check_outputs,
    compile_hry_pro_dva,
    expected_print_order,
    validate_layout,
)
from creobook.imposition import booklet_spreads


def test_page_plan_matches_the_brief():
    validate_layout()
    pages = build_page_plan()
    assert len(pages) == PAGE_COUNT
    counts: dict[str, int] = {}
    for page in pages:
        counts[page["kind"]] = counts.get(page["kind"], 0) + 1
    assert counts == EXPECTED_COUNTS
    assert pages[0]["title"] == "HRY PRO DVA"
    assert pages[1]["title"] == "Pravidla"

    lode = [page for page in pages if page["kind"] == "lode"]
    assert [page["heading"] for page in lode] == [
        "Partie 1 — Hráč 1",
        "Partie 1 — Hráč 2",
        "Partie 2 — Hráč 1",
        "Partie 2 — Hráč 2",
        "Partie 3 — Hráč 1",
        "Partie 3 — Hráč 2",
        "Partie 4 — Hráč 1",
        "Partie 4 — Hráč 2",
    ]
    assert [second["number"] - first["number"] for first, second in zip(lode[::2], lode[1::2])] == [1, 1, 1, 1]
    mesto = [page for page in pages if page["kind"] == "mesto"]
    assert len({page["match"] for page in mesto}) == 3
    assert [second["number"] - first["number"] for first, second in zip(mesto[::2], mesto[1::2])] == [1, 1, 1]


def test_print_order_starts_with_the_outer_sheet():
    order = expected_print_order()
    assert order == [(left, right) for left, right in booklet_spreads(32)]
    assert order[0] == (32, 1)
    assert order[1] == (2, 31)
    assert len(order) == 16
    assert None not in {side for pair in order for side in pair}


def test_booklet_pdfs(tmp_path):
    result = compile_hry_pro_dva(
        output_dir=tmp_path / "booklet",
        preview_dir=tmp_path / "preview",
        previews=True,
    )
    notes = check_outputs(result["pages"], result["booklet"])
    assert any("booklet order" in note for note in notes)
    assert (tmp_path / "preview" / "hry-pro-dva-cover.png").is_file()
    assert (tmp_path / "preview" / "hry-pro-dva-lode.png").is_file()
    assert (tmp_path / "preview" / "hry-pro-dva-mesto.png").is_file()
