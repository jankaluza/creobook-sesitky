"""Calendar data and Czech holiday tests."""

from __future__ import annotations

from datetime import date

import pytest

from creobook.calendar import (
    MONTH_NAMES_CS,
    build_calendar_data,
    build_month,
    easter_sunday,
    holidays_for_year,
    is_leap_year,
)


def test_leap_years():
    assert is_leap_year(2024)
    assert is_leap_year(2000)
    assert not is_leap_year(1900)
    assert not is_leap_year(2026)
    assert is_leap_year(2028)


def test_february_days_leap_vs_common():
    leap = build_calendar_data(2024)
    common = build_calendar_data(2026)
    feb_leap = leap["months"][1]
    feb_common = common["months"][1]
    leap_days = [
        d for w in feb_leap["weeks"] for d in w["days"] if d["in_month"]
    ]
    common_days = [
        d for w in feb_common["weeks"] for d in w["days"] if d["in_month"]
    ]
    assert len(leap_days) == 29
    assert len(common_days) == 28


def test_twelve_months_exactly_once():
    data = build_calendar_data(2026)
    assert len(data["months"]) == 12
    names = [m["name"] for m in data["months"]]
    assert names == MONTH_NAMES_CS
    assert len(set(names)) == 12


def test_six_week_rows():
    for year in (2026, 2027):
        data = build_calendar_data(year)
        for month in data["months"]:
            assert len(month["weeks"]) == 6
            for week in month["weeks"]:
                assert len(week["days"]) == 7


def test_monday_first():
    data = build_calendar_data(2026)
    assert data["weekday_names"][0] == "po"
    assert data["weekday_names"][-1] == "ne"
    for month in data["months"]:
        for week in month["weeks"]:
            monday = week["days"][0]
            assert date.fromisoformat(monday["iso"]).weekday() == 0


def test_iso_week_around_new_year():
    """ISO week numbers near New Year follow ISO 8601."""
    # 2026-01-01 is Thursday → ISO week 1
    jan = build_month(2026, 1, {})
    first_week = jan["weeks"][0]
    # First week of Jan 2026 calendar may start in Dec 2025
    days = first_week["days"]
    jan1 = next(d for d in days if d["iso"] == "2026-01-01")
    assert jan1["weekday"] == 3  # Thursday
    assert first_week["iso_week"] == date(2026, 1, 1).isocalendar().week

    # 2027-01-01 is Friday — still ISO week 53 of 2026 for days before Monday?
    # 28 Dec 2026 is Monday of ISO week 53
    assert date(2026, 12, 28).isocalendar() == (2026, 53, 1)
    assert date(2027, 1, 1).isocalendar().week == 53
    dec = build_month(2026, 12, {})
    # Find week containing 2026-12-28
    week53 = next(
        w for w in dec["weeks"] if any(d["iso"] == "2026-12-28" for d in w["days"])
    )
    assert week53["iso_week"] == 53


def test_czech_holidays_2026():
    holidays = holidays_for_year(2026)
    assert holidays[date(2026, 1, 1)]
    assert holidays[date(2026, 5, 1)]
    assert holidays[date(2026, 5, 8)]
    assert holidays[date(2026, 7, 5)]
    assert holidays[date(2026, 7, 6)]
    assert holidays[date(2026, 9, 28)]
    assert holidays[date(2026, 10, 28)]
    assert holidays[date(2026, 11, 17)]
    assert holidays[date(2026, 12, 24)]
    assert holidays[date(2026, 12, 25)]
    assert holidays[date(2026, 12, 26)]
    # Easter 2026-04-05 → Good Friday 04-03, Easter Monday 04-06
    assert easter_sunday(2026) == date(2026, 4, 5)
    assert date(2026, 4, 3) in holidays
    assert date(2026, 4, 6) in holidays
    assert "Velký pátek" in holidays[date(2026, 4, 3)]
    assert "Velikonoční pondělí" in holidays[date(2026, 4, 6)]


def test_easter_known_dates():
    assert easter_sunday(2025) == date(2025, 4, 20)
    assert easter_sunday(2027) == date(2027, 3, 28)
    assert easter_sunday(2028) == date(2028, 4, 16)


def test_adjacent_month_days_marked():
    jan = build_month(2026, 1, {})
    # First cell should be Dec 2025 if month doesn't start on Monday
    first = jan["weeks"][0]["days"][0]
    if first["iso"] != "2026-01-01":
        assert first["in_month"] is False
        assert first["month"] == 12
