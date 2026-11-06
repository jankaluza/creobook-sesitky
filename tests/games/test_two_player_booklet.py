"""Layout and print checks for the Hry pro dva booklet."""

from __future__ import annotations

from creobook.games.two_player_booklet import (
    EXPECTED_COUNTS,
    LODE_MATCHES,
    PAGE_COUNT,
    SHEET_COUNT,
    build_page_plan,
    check_outputs,
    compile_hry_pro_dva,
    expected_print_order,
    page_sheet_side,
    physical_sheets,
    sheet_overview,
    sheets_toward_center,
    validate_layout,
    validate_lode_sheet_layout,
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
    assert [(page["number"], page["heading"]) for page in lode] == [
        (4, "Partie 1 — Hráč 1"),
        (6, "Partie 2 — Hráč 1"),
        (8, "Partie 3 — Hráč 1"),
        (10, "Partie 4 — Hráč 1"),
        (23, "Partie 4 — Hráč 2"),
        (25, "Partie 3 — Hráč 2"),
        (27, "Partie 2 — Hráč 2"),
        (29, "Partie 1 — Hráč 2"),
    ]
    assert {page["sheet_hand"] for page in lode if page["player"] == 1} == {"left"}
    assert {page["sheet_hand"] for page in lode if page["player"] == 2} == {"right"}
    mesto = [page for page in pages if page["kind"] == "mesto"]
    assert len({page["match"] for page in mesto}) == 3
    assert [second["number"] - first["number"] for first, second in zip(mesto[::2], mesto[1::2])] == [
        1,
        1,
        1,
    ]


def test_lode_matches_share_one_a4_side_with_a_privacy_stack():
    pages = build_page_plan()
    notes = validate_lode_sheet_layout(pages)
    assert len(notes) == 4
    for item in LODE_MATCHES:
        sheet_a, side_a, hand_a = page_sheet_side(item["player1"])
        sheet_b, side_b, hand_b = page_sheet_side(item["player2"])
        assert sheet_a == sheet_b == item["sheet"]
        assert side_a == side_b == "back"
        assert hand_a == "left"
        assert hand_b == "right"
        privacy = sheets_toward_center(item["sheet"])
        assert privacy
        assert privacy[-1] == SHEET_COUNT
        assert item["sheet"] not in privacy

    overview = "\n".join(sheet_overview(pages))
    assert "List 2:" in overview
    assert "4 Lodě P1 H1" in overview
    assert "29 Lodě P1 H2" in overview
    assert "10 Lodě P4 H1" in overview
    assert "23 Lodě P4 H2" in overview


def test_physical_sheets_follow_booklet_imposition():
    sheets = physical_sheets()
    assert len(sheets) == SHEET_COUNT
    spreads = booklet_spreads(PAGE_COUNT)
    assert sheets[0]["front"] == {"left": spreads[0][0], "right": spreads[0][1]}
    assert sheets[0]["back"] == {"left": spreads[1][0], "right": spreads[1][1]}
    assert sheets[1]["back"] == {"left": 4, "right": 29}
    assert sheets[4]["back"] == {"left": 10, "right": 23}


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
    assert any(note.startswith("Partie 1:") for note in notes)
    assert any(note.startswith("Fyzické listy A4") for note in notes)
    assert (tmp_path / "preview" / "hry-pro-dva-cover.png").is_file()
    assert (tmp_path / "preview" / "hry-pro-dva-lode.png").is_file()
    assert (tmp_path / "preview" / "hry-pro-dva-mesto.png").is_file()
