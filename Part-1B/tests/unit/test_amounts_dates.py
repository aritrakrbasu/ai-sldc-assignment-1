"""T012, T013 — amount mentions (spec edge cases) and period resolution (FR-012)."""

import datetime as dt

import pytest

from moneylens.core.amounts import find_amounts
from moneylens.core.dates import (
    last_n_days,
    month_to_date,
    previous_month,
    previous_week,
    week_to_date,
)

REF = dt.date(2026, 11, 23)  # Monday


@pytest.mark.parametrize(
    ("text", "expected"),
    [("Rs.1,250.00", {125000}), ("Rs 1250", {125000}), ("INR 1,250.5", {125050}),
     ("₹1,250", {125000}), ("₹ 99", {9900}), ("rs.312.40 paid", {31240}),
     ("INR 2,35,000.00 debited. Avl Bal INR 12,045.10", {23500000, 1204510}),
     ("1,200.00 INR debited", {120000}), ("No money here 4821", set()),
     ("@@## Rs. debited ???", set())],
)
def test_find_amounts(text, expected):
    assert find_amounts(text) == expected


def test_fr012_periods():
    assert month_to_date(REF) == (dt.date(2026, 11, 1), REF)
    assert previous_week(REF) == (dt.date(2026, 11, 16), dt.date(2026, 11, 22))
    assert week_to_date(REF) == (dt.date(2026, 11, 23), REF)
    assert previous_month(REF) == (dt.date(2026, 10, 1), dt.date(2026, 10, 31))
    assert last_n_days(REF, 30) == (dt.date(2026, 10, 25), REF)


def test_fr012_previous_month_january():
    assert previous_month(dt.date(2026, 1, 15)) == (dt.date(2025, 12, 1), dt.date(2025, 12, 31))


def test_fr012_previous_week_from_sunday():
    assert previous_week(dt.date(2026, 11, 29)) == (dt.date(2026, 11, 16), dt.date(2026, 11, 22))
