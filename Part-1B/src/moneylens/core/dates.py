"""Period resolution relative to a reference date (FR-012). Pure; the date is passed in."""

from __future__ import annotations

import datetime as dt

Range = tuple[dt.date, dt.date]


def month_to_date(ref: dt.date) -> Range:
    return ref.replace(day=1), ref


def week_to_date(ref: dt.date) -> Range:
    return ref - dt.timedelta(days=ref.weekday()), ref


def previous_week(ref: dt.date) -> Range:
    start = ref - dt.timedelta(days=ref.weekday() + 7)
    return start, start + dt.timedelta(days=6)


def previous_month(ref: dt.date) -> Range:
    end = ref.replace(day=1) - dt.timedelta(days=1)
    return end.replace(day=1), end


def last_n_days(ref: dt.date, n: int) -> Range:
    return ref - dt.timedelta(days=n - 1), ref


def parse_iso(value: str | None) -> dt.date | None:
    if not value:
        return None
    try:
        return dt.date.fromisoformat(value)
    except ValueError:
        return None
