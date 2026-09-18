"""Quarterly planner: date model, localized JSON, and spread planning."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from creobook.calendar import (
    MONTH_NAMES_CS,
    WEEKDAY_NAMES_CS,
    build_month,
    holidays_for_year,
    load_holiday_config,
)
from creobook.theme import Theme, load_theme

# Full Czech weekday names for planner day headers (Monday-first).
WEEKDAY_NAMES_FULL_CS = [
    "pondělí",
    "úterý",
    "středa",
    "čtvrtek",
    "pátek",
    "sobota",
    "neděle",
]

QUARTER_MONTHS = {
    1: (1, 2, 3),
    2: (4, 5, 6),
    3: (7, 8, 9),
    4: (10, 11, 12),
}

PLANNER_A5_PAGES = 28
PLANNER_PHYSICAL_SHEETS = 7
# 7 physical duplex sheets → 14 printed A4 sides → 28 A5 pages
PLANNER_A4_SIDES = PLANNER_PHYSICAL_SHEETS * 2
WEEKLY_SPREADS = 13


class PlannerError(ValueError):
    """Raised when a quarter cannot be packed into thirteen weekly spreads."""


class QuarterSpec(BaseModel):
    """Validated quarter selection."""

    year: int = Field(..., ge=1970, le=2100)
    quarter: int

    @field_validator("quarter")
    @classmethod
    def _quarter_range(cls, value: int) -> int:
        if value not in (1, 2, 3, 4):
            raise ValueError("quarter must be an integer from 1 to 4")
        return value


def validate_quarter(quarter: int) -> int:
    """Return quarter if valid; raise ValueError with a clear message otherwise."""
    try:
        return QuarterSpec(year=2000, quarter=quarter).quarter
    except Exception as exc:  # noqa: BLE001 — surface pydantic / value errors
        raise ValueError("quarter must be an integer from 1 to 4") from exc


def quarter_date_range(year: int, quarter: int) -> tuple[date, date]:
    """Inclusive start/end dates for a calendar quarter."""
    validate_quarter(quarter)
    starts = {1: (1, 1), 2: (4, 1), 3: (7, 1), 4: (10, 1)}
    ends = {1: (3, 31), 2: (6, 30), 3: (9, 30), 4: (12, 31)}
    sm, sd = starts[quarter]
    em, ed = ends[quarter]
    return date(year, sm, sd), date(year, em, ed)


def next_quarter(year: int, quarter: int) -> tuple[int, int]:
    """Return (year, quarter) for the following quarter (Q4 → Q1 next year)."""
    validate_quarter(quarter)
    if quarter == 4:
        return year + 1, 1
    return year, quarter + 1


def quarter_label_cs(year: int, quarter: int) -> str:
    validate_quarter(quarter)
    return f"{quarter}. ČTVRTLETÍ {year}"


def format_date_cs(d: date, *, include_year: bool = True) -> str:
    """Czech date like ``1. ledna 2027``."""
    month = MONTH_NAMES_CS[d.month - 1]
    if include_year:
        return f"{d.day}. {month} {d.year}"
    return f"{d.day}. {month}"


def format_range_cs(start: date, end: date) -> str:
    if start.year == end.year and start.month == end.month:
        return f"{start.day}.–{end.day}. {MONTH_NAMES_CS[start.month - 1]} {start.year}"
    if start.year == end.year:
        return (
            f"{start.day}. {MONTH_NAMES_CS[start.month - 1]} – "
            f"{end.day}. {MONTH_NAMES_CS[end.month - 1]} {start.year}"
        )
    return f"{format_date_cs(start)} – {format_date_cs(end)}"


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _day_payload(
    d: date,
    *,
    quarter_start: date,
    quarter_end: date,
    holidays: dict[date, str],
    show_holidays: bool,
) -> dict[str, Any]:
    in_quarter = quarter_start <= d <= quarter_end
    holiday_name = holidays.get(d) if show_holidays else None
    return {
        "iso": d.isoformat(),
        "day": d.day,
        "month": d.month,
        "year": d.year,
        "weekday": d.weekday(),
        "weekday_name": WEEKDAY_NAMES_FULL_CS[d.weekday()],
        "weekday_short": WEEKDAY_NAMES_CS[d.weekday()],
        "month_name": MONTH_NAMES_CS[d.month - 1],
        "month_label": MONTH_NAMES_CS[d.month - 1][:3],
        "in_quarter": in_quarter,
        "weekend": d.weekday() >= 5,
        "holiday": holiday_name is not None,
        "holiday_name": holiday_name,
        "active": in_quarter,
    }


def intersecting_iso_weeks(
    quarter_start: date,
    quarter_end: date,
    *,
    holidays: dict[date, str],
    show_holidays: bool = True,
) -> list[dict[str, Any]]:
    """Return ISO weeks that intersect ``[quarter_start, quarter_end]``."""
    weeks: list[dict[str, Any]] = []
    seen: set[tuple[int, int]] = set()
    cursor = _monday_of(quarter_start)
    while cursor <= quarter_end:
        days = [cursor + timedelta(days=i) for i in range(7)]
        if any(quarter_start <= d <= quarter_end for d in days):
            thursday = cursor + timedelta(days=3)
            iso = thursday.isocalendar()
            key = (iso.year, iso.week)
            if key not in seen:
                seen.add(key)
                payloads = [
                    _day_payload(
                        d,
                        quarter_start=quarter_start,
                        quarter_end=quarter_end,
                        holidays=holidays,
                        show_holidays=show_holidays,
                    )
                    for d in days
                ]
                in_count = sum(1 for p in payloads if p["in_quarter"])
                weeks.append(
                    {
                        "iso_year": iso.year,
                        "iso_week": iso.week,
                        "label": f"Týden {iso.week}",
                        "range_label": format_range_cs(days[0], days[6]),
                        "start": days[0].isoformat(),
                        "end": days[6].isoformat(),
                        "complete": in_count == 7,
                        "partial": in_count < 7,
                        "in_quarter_count": in_count,
                        "days": payloads,
                    }
                )
        cursor += timedelta(days=7)
    return weeks


SpreadKind = Literal["standard", "boundary"]


def build_weekly_spreads(weeks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Pack intersecting ISO weeks into exactly 13 facing-page spreads.

    - 13 weeks → one standard spread each (out-of-quarter days marked inactive).
    - 14 weeks → boundary spread (opening | closing) + 12 complete middle weeks.

    Raises ``PlannerError`` when the week count is not 13 or 14, or when the
    twelve middle weeks of a 14-week quarter are not all complete.
    """
    n = len(weeks)
    if n == 13:
        return [
            {
                "kind": "standard",
                "index": i + 1,
                "week": week,
                "left_page": 2 + 2 * i,
                "right_page": 3 + 2 * i,
            }
            for i, week in enumerate(weeks)
        ]

    if n == 14:
        first, *middle, last = weeks
        if len(middle) != 12:
            raise PlannerError(
                f"Expected 12 complete weeks between boundary weeks, got {len(middle)}"
            )
        incomplete = [w for w in middle if not w["complete"]]
        if incomplete:
            labels = ", ".join(f"{w['iso_year']}-W{w['iso_week']}" for w in incomplete)
            raise PlannerError(
                f"14-week quarter has incomplete middle week(s): {labels}"
            )
        spreads: list[dict[str, Any]] = [
            {
                "kind": "boundary",
                "index": 1,
                "opening": first,
                "closing": last,
                "left_page": 2,
                "right_page": 3,
                "opening_range_label": format_range_cs(
                    date.fromisoformat(first["start"]),
                    date.fromisoformat(first["end"]),
                ),
                "closing_range_label": format_range_cs(
                    date.fromisoformat(last["start"]),
                    date.fromisoformat(last["end"]),
                ),
            }
        ]
        for i, week in enumerate(middle):
            spreads.append(
                {
                    "kind": "standard",
                    "index": i + 2,
                    "week": week,
                    "left_page": 4 + 2 * i,
                    "right_page": 5 + 2 * i,
                }
            )
        return spreads

    raise PlannerError(
        f"Quarter intersects {n} ISO weeks; only 13 or 14 are supported "
        f"for a 13-spread / 28-page planner"
    )


def _assert_quarter_date_coverage(
    quarter_start: date,
    quarter_end: date,
    spreads: list[dict[str, Any]],
) -> None:
    """Every quarter date appears exactly once as an active day across spreads."""
    seen: list[str] = []

    def collect(days: list[dict[str, Any]]) -> None:
        for day in days:
            if day["in_quarter"]:
                seen.append(day["iso"])

    for spread in spreads:
        if spread["kind"] == "standard":
            collect(spread["week"]["days"])
        else:
            collect(spread["opening"]["days"])
            collect(spread["closing"]["days"])

    expected = [
        (quarter_start + timedelta(days=i)).isoformat()
        for i in range((quarter_end - quarter_start).days + 1)
    ]
    if len(seen) != len(set(seen)):
        dupes = sorted({d for d in seen if seen.count(d) > 1})
        raise PlannerError(f"Duplicate quarter dates in spreads: {dupes[:8]}")
    missing = sorted(set(expected) - set(seen))
    extra = sorted(set(seen) - set(expected))
    if missing or extra:
        raise PlannerError(
            f"Quarter date coverage failed "
            f"(missing={missing[:5]}, extra={extra[:5]})"
        )


def _mini_month(
    year: int,
    month: int,
    holidays: dict[date, str],
    *,
    quarter_start: date,
    quarter_end: date,
    show_holidays: bool,
) -> dict[str, Any]:
    raw = build_month(year, month, holidays if show_holidays else {})
    # Annotate in_quarter on each day for Typst highlighting.
    weeks = []
    for week in raw["weeks"]:
        days = []
        for day in week["days"]:
            d = date(day["year"], day["month"], day["day"])
            item = dict(day)
            item["in_quarter"] = quarter_start <= d <= quarter_end
            if not show_holidays:
                item["holiday"] = False
                item["holiday_name"] = None
            days.append(item)
        weeks.append({"iso_week": week["iso_week"], "days": days})
    return {
        "month": month,
        "year": year,
        "name": raw["name"],
        "weeks": weeks,
    }


def build_planner_data(
    year: int,
    quarter: int,
    *,
    locale: str = "cs-CZ",
    theme: Theme | None = None,
    accent: str | None = None,
    show_holidays: bool = True,
    holiday_path: Any = None,
) -> dict[str, Any]:
    """
    Build structured JSON for the 28-page quarterly planner.

    Physical format (documented for printers and tests):
    - 7 physical A4 sheets, duplex → 14 printed A4 sides → 28 logical A5 pages
    - one folded booklet under one CreoBook elastic
    """
    spec = QuarterSpec(year=year, quarter=quarter)
    if locale not in ("cs-CZ", "cs", "cs_CZ"):
        raise ValueError(f"Unsupported locale {locale!r}; only cs-CZ is implemented")

    base_theme = (theme or load_theme()).with_accent(accent)
    holidays = holidays_for_year(spec.year, load_holiday_config(holiday_path))
    # Holidays may fall in adjacent years for boundary weeks.
    holidays = {
        **holidays_for_year(spec.year - 1, load_holiday_config(holiday_path)),
        **holidays,
        **holidays_for_year(spec.year + 1, load_holiday_config(holiday_path)),
    }

    q_start, q_end = quarter_date_range(spec.year, spec.quarter)
    ny, nq = next_quarter(spec.year, spec.quarter)
    n_start, n_end = quarter_date_range(ny, nq)

    weeks = intersecting_iso_weeks(
        q_start, q_end, holidays=holidays, show_holidays=show_holidays
    )
    spreads = build_weekly_spreads(weeks)
    if len(spreads) != WEEKLY_SPREADS:
        raise PlannerError(f"Expected {WEEKLY_SPREADS} spreads, got {len(spreads)}")
    _assert_quarter_date_coverage(q_start, q_end, spreads)

    months = QUARTER_MONTHS[spec.quarter]
    mini_calendars = [
        _mini_month(
            spec.year,
            m,
            holidays,
            quarter_start=q_start,
            quarter_end=q_end,
            show_holidays=show_holidays,
        )
        for m in months
    ]

    quarter_id = f"{spec.year} / Q{spec.quarter}"
    return {
        "page_type": "quarterly_planner",
        "locale": "cs-CZ",
        "year": spec.year,
        "quarter": spec.quarter,
        "quarter_name": quarter_label_cs(spec.year, spec.quarter),
        "quarter_id": quarter_id,
        "start": q_start.isoformat(),
        "end": q_end.isoformat(),
        "range_label": format_range_cs(q_start, q_end),
        "show_holidays": show_holidays,
        "weekday_names": WEEKDAY_NAMES_CS,
        "weekday_names_full": WEEKDAY_NAMES_FULL_CS,
        "line_spacing_mm": 6.5,
        "physical": {
            "a5_pages": PLANNER_A5_PAGES,
            "physical_sheets": PLANNER_PHYSICAL_SHEETS,
            "a4_sides": PLANNER_A4_SIDES,
            "notes": (
                "One physical A4 sheet has two printed sides; each side holds two A5 "
                "pages. Seven duplex sheets ⇒ 14 A4 PDF pages ⇒ 28 A5 pages."
            ),
        },
        "next_quarter": {
            "year": ny,
            "quarter": nq,
            "quarter_name": quarter_label_cs(ny, nq),
            "start": n_start.isoformat(),
            "end": n_end.isoformat(),
            "range_label": format_range_cs(n_start, n_end),
        },
        "months": mini_calendars,
        "weeks": weeks,
        "week_count": len(weeks),
        "boundary_mode": len(weeks) == 14,
        "spreads": spreads,
        "theme": base_theme.to_typst_dict(),
        "labels": {
            "main_goal_quarter": "HLAVNÍ CÍL ČTVRTLETÍ",
            "personal_goals": "OSOBNÍ CÍLE",
            "work_projects": "PRÁCE A PROJEKTY",
            "milestones": "DŮLEŽITÁ DATA A MILNÍKY",
            "notes": "POZNÁMKY",
            "main_goal_week": "HLAVNÍ CÍL TÝDNE",
            "tasks_notes": "ÚKOLY A POZNÁMKY",
            "transfer": "PŘENOS DO DALŠÍHO ČTVRTLETÍ",
            "unfinished": "NEDOKONČENÉ ÚKOLY",
            "keep": "CO CHCI ZACHOVAT",
            "change": "CO CHCI ZMĚNIT",
            "first_steps": "PRVNÍ KROKY DALŠÍHO ČTVRTLETÍ",
            "opening_period": "ZAČÁTEK ČTVRTLETÍ",
            "closing_period": "KONEC ČTVRTLETÍ",
            "shared_notes": "POZNÁMKY",
        },
    }


def planner_a5_filename(year: int, quarter: int) -> str:
    validate_quarter(quarter)
    return f"creobook-quarterly-planner-{year}-q{quarter}-a5.pdf"


def planner_booklet_filename(year: int, quarter: int) -> str:
    validate_quarter(quarter)
    return f"creobook-quarterly-planner-{year}-q{quarter}-a4.pdf"


def active_dates_in_spreads(spreads: list[dict[str, Any]]) -> list[str]:
    """Helper for tests: ordered unique? list of in-quarter ISO dates."""
    out: list[str] = []
    for spread in spreads:
        if spread["kind"] == "standard":
            days = spread["week"]["days"]
        else:
            days = spread["opening"]["days"] + spread["closing"]["days"]
        for day in days:
            if day["in_quarter"]:
                out.append(day["iso"])
    return out
