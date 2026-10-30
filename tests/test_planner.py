"""Quarterly planner calendar logic and PDF integration tests."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from creobook.calendar import easter_sunday, holidays_for_year
from creobook.imposition import booklet_spreads
from creobook.planner import (
    PLANNER_A4_SIDES,
    PLANNER_A5_PAGES,
    PLANNER_PHYSICAL_SHEETS,
    WEEKLY_SPREADS,
    PlannerError,
    active_dates_in_spreads,
    build_planner_data,
    build_weekly_spreads,
    next_quarter,
    planner_a5_filename,
    planner_booklet_filename,
    quarter_date_range,
    validate_quarter,
)


@pytest.mark.parametrize("bad", [0, 5, -1, 99])
def test_quarter_argument_rejects_invalid(bad):
    with pytest.raises(ValueError, match="1 to 4"):
        validate_quarter(bad)


@pytest.mark.parametrize("q", [1, 2, 3, 4])
def test_quarter_argument_accepts_1_to_4(q):
    assert validate_quarter(q) == q


@pytest.mark.parametrize(
    "year,quarter,start,end",
    [
        (2027, 1, date(2027, 1, 1), date(2027, 3, 31)),
        (2027, 2, date(2027, 4, 1), date(2027, 6, 30)),
        (2027, 3, date(2027, 7, 1), date(2027, 9, 30)),
        (2027, 4, date(2027, 10, 1), date(2027, 12, 31)),
        (2024, 1, date(2024, 1, 1), date(2024, 3, 31)),  # leap year
    ],
)
def test_quarter_start_end_dates(year, quarter, start, end):
    assert quarter_date_range(year, quarter) == (start, end)


def test_q4_points_to_q1_next_year():
    assert next_quarter(2027, 4) == (2028, 1)
    assert next_quarter(2027, 1) == (2027, 2)
    data = build_planner_data(2027, 4)
    assert data["next_quarter"]["year"] == 2028
    assert data["next_quarter"]["quarter"] == 1
    assert data["next_quarter"]["start"] == "2028-01-01"


def test_calendar_quarter_and_rolling():
    from datetime import date

    from creobook.planner import calendar_quarter, rolling_quarters

    assert calendar_quarter(date(2026, 9, 18)) == (2026, 3)
    assert calendar_quarter(date(2026, 1, 1)) == (2026, 1)
    assert calendar_quarter(date(2026, 12, 31)) == (2026, 4)
    assert rolling_quarters(date(2026, 9, 18), count=4) == [
        (2026, 3),
        (2026, 4),
        (2027, 1),
        (2027, 2),
    ]
    assert rolling_quarters(date(2026, 12, 1), count=2) == [(2026, 4), (2027, 1)]


def test_booklet_order_twenty_eight_pages():
    spreads = booklet_spreads(28)
    assert len(spreads) == PLANNER_A4_SIDES
    assert PLANNER_PHYSICAL_SHEETS * 2 == PLANNER_A4_SIDES
    assert spreads == [
        (28, 1),
        (2, 27),
        (26, 3),
        (4, 25),
        (24, 5),
        (6, 23),
        (22, 7),
        (8, 21),
        (20, 9),
        (10, 19),
        (18, 11),
        (12, 17),
        (16, 13),
        (14, 15),
    ]


def test_filenames():
    assert planner_a5_filename(2027, 1) == "creobook-quarterly-planner-2027-q1-a5.pdf"
    assert (
        planner_booklet_filename(2027, 1) == "creobook-quarterly-planner-2027-q1-a4.pdf"
    )


def _expected_dates(year: int, quarter: int) -> list[str]:
    start, end = quarter_date_range(year, quarter)
    return [
        (start + timedelta(days=i)).isoformat()
        for i in range((end - start).days + 1)
    ]


@pytest.mark.parametrize(
    "year,quarter,expect_boundary",
    [
        (2024, 1, False),  # 13 ISO weeks, leap-year Q1
        (2027, 1, True),  # 14 ISO weeks, crosses ISO week-year boundary
        (2029, 1, False),  # 13 weeks
        (2026, 1, True),  # 14 weeks
    ],
)
def test_spread_modes_and_date_coverage(year, quarter, expect_boundary):
    data = build_planner_data(year, quarter)
    assert data["boundary_mode"] is expect_boundary
    assert data["week_count"] in (13, 14)
    assert len(data["spreads"]) == WEEKLY_SPREADS

    active = active_dates_in_spreads(data["spreads"])
    expected = _expected_dates(year, quarter)
    assert sorted(active) == sorted(expected)
    assert len(active) == len(set(active))
    assert set(active) == set(expected)

    # Facing-page pairs: spread i uses pages (2+2i, 3+2i)
    for i, spread in enumerate(data["spreads"]):
        assert spread["left_page"] == 2 + 2 * i
        assert spread["right_page"] == 3 + 2 * i
        assert spread["left_page"] % 2 == 0
        assert spread["right_page"] == spread["left_page"] + 1


def test_iso_week_numbers_correct_for_2027_q1():
    data = build_planner_data(2027, 1)
    assert data["spreads"][0]["kind"] == "boundary"
    assert data["spreads"][0]["opening"]["iso_year"] == 2026
    assert data["spreads"][0]["opening"]["iso_week"] == 53
    assert data["spreads"][0]["closing"]["iso_week"] == 13
    assert data["spreads"][1]["week"]["iso_week"] == 1
    assert data["spreads"][1]["week"]["iso_year"] == 2027


def test_leap_year_february_in_q1_2024():
    data = build_planner_data(2024, 1)
    assert "2024-02-29" in active_dates_in_spreads(data["spreads"])
    assert data["week_count"] == 13
    assert data["boundary_mode"] is False


def test_czech_fixed_and_movable_holidays_in_planner():
    holidays = holidays_for_year(2027)
    assert holidays[date(2027, 1, 1)].startswith("Den obnovy")
    easter = easter_sunday(2027)
    assert easter == date(2027, 3, 28)
    assert holidays[easter + timedelta(days=-2)] == "Velký pátek"
    assert holidays[easter + timedelta(days=1)] == "Velikonoční pondělí"

    data = build_planner_data(2027, 1, show_holidays=True)
    found = False
    for spread in data["spreads"]:
        days = (
            spread["week"]["days"]
            if spread["kind"] == "standard"
            else spread["opening"]["days"] + spread["closing"]["days"]
        )
        for day in days:
            if day["iso"] == "2027-03-26":
                assert day["holiday"] is True
                assert day["holiday_name"] == "Velký pátek"
                found = True
    assert found


def test_show_holidays_false_clears_flags():
    data = build_planner_data(2027, 1, show_holidays=False)
    for spread in data["spreads"]:
        days = (
            spread["week"]["days"]
            if spread["kind"] == "standard"
            else spread["opening"]["days"] + spread["closing"]["days"]
        )
        for day in days:
            assert day["holiday"] is False
            assert day["holiday_name"] is None


def test_unsupported_week_count_fails_clearly():
    with pytest.raises(PlannerError, match="15 ISO weeks"):
        build_weekly_spreads(
            [{"iso_week": i, "complete": True, "days": []} for i in range(15)]
        )


def test_planner_pdf_dimensions_and_imposition(tmp_path):
    from creobook.compiler import compile_planner
    from creobook.imposition import impose_booklet
    from creobook.theme import load_theme
    from creobook.validation import (
        check_a4_landscape_sheets,
        check_a5_pages,
        check_content_within_media_box,
        check_page_count,
    )

    theme = load_theme()
    pages = tmp_path / "planner-a5.pdf"
    compile_planner(2027, 1, pages, theme=theme)
    assert check_page_count(pages, PLANNER_A5_PAGES).ok
    assert check_a5_pages(pages, theme=theme).ok
    assert check_content_within_media_box(pages).ok

    book = tmp_path / "planner-a4.pdf"
    impose_booklet(pages, book, theme=theme, fold_guide=True)
    assert check_page_count(book, PLANNER_A4_SIDES).ok
    assert check_a4_landscape_sheets(book, theme=theme).ok
    assert check_content_within_media_box(book).ok


def test_mirrored_margins_in_theme_data():
    data = build_planner_data(2027, 1)
    margins = data["theme"]["margins"]
    assert margins["inner_mm"] == 12.0
    assert margins["outer_mm"] == 11.0
    assert margins["top_mm"] == 18.0
    assert margins["bottom_mm"] == 16.0
