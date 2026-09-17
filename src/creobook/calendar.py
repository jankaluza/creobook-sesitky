"""Czech calendar data generation for Typst monthly calendars."""

from __future__ import annotations

from calendar import Calendar
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from creobook.theme import Theme, config_dir, load_theme

MONTH_NAMES_CS = [
    "leden",
    "únor",
    "březen",
    "duben",
    "květen",
    "červen",
    "červenec",
    "srpen",
    "září",
    "říjen",
    "listopad",
    "prosinec",
]

WEEKDAY_NAMES_CS = ["po", "út", "st", "čt", "pá", "so", "ne"]


class FixedHoliday(BaseModel):
    month: int
    day: int
    name: str


class EasterRelativeHoliday(BaseModel):
    offset: int
    name: str


class HolidayConfig(BaseModel):
    locale: str = "cs"
    fixed: list[FixedHoliday] = Field(default_factory=list)
    easter_relative: list[EasterRelativeHoliday] = Field(default_factory=list)


def easter_sunday(year: int) -> date:
    """Anonymous Gregorian algorithm for Western Easter Sunday."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    el = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * el) // 451
    month = (h + el - 7 * m + 114) // 31
    day = ((h + el - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def load_holiday_config(path: Path | None = None) -> HolidayConfig:
    holiday_path = path or (config_dir() / "holidays-cz.yaml")
    with holiday_path.open(encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return HolidayConfig.model_validate(raw)


def holidays_for_year(year: int, config: HolidayConfig | None = None) -> dict[date, str]:
    """Return mapping of holiday date -> name for a calendar year."""
    cfg = config or load_holiday_config()
    result: dict[date, str] = {}
    for item in cfg.fixed:
        result[date(year, item.month, item.day)] = item.name
    easter = easter_sunday(year)
    for item in cfg.easter_relative:
        result[easter + timedelta(days=item.offset)] = item.name
    return result


def build_month(
    year: int,
    month: int,
    holidays: dict[date, str],
) -> dict[str, Any]:
    """Build one month grid with exactly six Monday-first week rows."""
    cal = Calendar(firstweekday=0)  # Monday
    weeks_raw = cal.monthdatescalendar(year, month)
    # Always six rows for a stable printable layout
    while len(weeks_raw) < 6:
        last_sunday = weeks_raw[-1][-1]
        next_monday = last_sunday + timedelta(days=1)
        weeks_raw.append([next_monday + timedelta(days=i) for i in range(7)])
    weeks_raw = weeks_raw[:6]

    weeks: list[dict[str, Any]] = []
    for week_dates in weeks_raw:
        monday = week_dates[0]
        thursday = monday + timedelta(days=3)
        days = []
        for weekday_idx, d in enumerate(week_dates):
            holiday_name = holidays.get(d)
            days.append(
                {
                    "day": d.day,
                    "month": d.month,
                    "year": d.year,
                    "iso": d.isoformat(),
                    "in_month": d.month == month and d.year == year,
                    "weekend": d.weekday() >= 5,
                    "holiday": holiday_name is not None,
                    "holiday_name": holiday_name,
                    "weekday": weekday_idx,
                }
            )
        weeks.append(
            {
                "iso_week": thursday.isocalendar().week,
                "days": days,
            }
        )

    return {
        "month": month,
        "year": year,
        "name": MONTH_NAMES_CS[month - 1],
        "weeks": weeks,
    }


def build_calendar_data(
    year: int,
    theme: Theme | None = None,
    holiday_path: Path | None = None,
    accent: str | None = None,
) -> dict[str, Any]:
    """Generate structured JSON for twelve monthly A5 calendar pages."""
    base_theme = (theme or load_theme()).with_accent(accent)
    holidays = holidays_for_year(year, load_holiday_config(holiday_path))
    months = [build_month(year, m, holidays) for m in range(1, 13)]
    return {
        "page_type": "calendar",
        "year": year,
        "weekday_names": WEEKDAY_NAMES_CS,
        "months": months,
        "theme": base_theme.to_typst_dict(),
        "holidays": [
            {"date": d.isoformat(), "name": name}
            for d, name in sorted(holidays.items())
        ],
    }


def is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
