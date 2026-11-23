"""T028 [US3], T030 [US4] — deterministic dashboard and query execution."""

import pytest

from moneylens.core.dashboard import summarize
from moneylens.core.query_exec import execute

TX = [
    {"id": 1, "txn_date": "2026-11-17", "direction": "DEBIT", "amount_paise": 25000,
     "merchant": "Swiggy", "category": "FOOD"},
    {"id": 2, "txn_date": "2026-11-19", "direction": "DEBIT", "amount_paise": 40000,
     "merchant": "Zomato", "category": "FOOD"},
    {"id": 3, "txn_date": "2026-11-20", "direction": "DEBIT", "amount_paise": 18000,
     "merchant": "Uber", "category": "TRANSPORT"},
    {"id": 4, "txn_date": "2026-11-01", "direction": "CREDIT", "amount_paise": 8500000,
     "merchant": "ACME", "category": "INCOME"},
    {"id": 5, "txn_date": "2026-10-15", "direction": "DEBIT", "amount_paise": 55000,
     "merchant": "Swiggy", "category": "FOOD"},
    {"id": 6, "txn_date": "2026-11-21", "direction": "DEBIT", "amount_paise": 7000,
     "merchant": None, "category": "CASH"},
]


def q(**kw):
    base = {"metric": "TOTAL", "direction": "DEBIT", "categories": [], "merchant_contains": None,
            "date_from": "2026-11-01", "date_to": "2026-11-23", "period_defaulted": False}
    return base | kw


def test_us3_1_dashboard_exact_and_sorted():
    d = summarize(TX, "2026-11-01", "2026-11-30")
    assert d["by_category"] == [
        {"category": "FOOD", "value_paise": 65000, "count": 2},
        {"category": "TRANSPORT", "value_paise": 18000, "count": 1},
        {"category": "CASH", "value_paise": 7000, "count": 1}]
    assert d["total_debit_paise"] == 90000 and d["total_credit_paise"] == 8500000
    assert [t["id"] for t in d["recent"]] == [6, 3, 2, 1, 4]


def test_dashboard_empty_range():
    d = summarize(TX, "2025-01-01", "2025-01-31")
    assert d["by_category"] == [] and d["total_debit_paise"] == 0 and d["recent"] == []


@pytest.mark.parametrize(
    ("query", "value", "count"),
    [(q(categories=["FOOD"], date_from="2026-11-16", date_to="2026-11-22"), 65000, 2),
     (q(metric="COUNT", merchant_contains="swig"), None, 1),
     (q(metric="AVERAGE", categories=["FOOD"]), 32500, 2),
     (q(metric="LARGEST"), 40000, 4),
     (q(direction="CREDIT"), 8500000, 1),
     (q(date_from="2025-01-01", date_to="2025-01-31"), 0, 0),
     (q(metric="AVERAGE", date_from="2025-01-01", date_to="2025-01-31"), 0, 0),
     (q(metric="LARGEST", date_from="2025-01-01", date_to="2025-01-31"), None, 0)],
)
def test_fr011_execute_metrics(query, value, count):
    ans = execute(query, TX)
    assert (ans["value_paise"], ans["count"]) == (value, count)


def test_list_and_top_merchants_items():
    ans = execute(q(metric="LIST"), TX)
    assert [i["id"] for i in ans["items"]] == [6, 3, 2, 1]
    top = execute(q(metric="TOP_MERCHANTS"), TX)["items"]
    assert top[0] == {"merchant": "Zomato", "value_paise": 40000, "count": 1}
    assert top[-1]["merchant"] == "(unknown)"
