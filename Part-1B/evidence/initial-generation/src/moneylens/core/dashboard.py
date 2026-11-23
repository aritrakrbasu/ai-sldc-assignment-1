"""Dashboard aggregation (FR-010). All totals exact, computed from stored transactions."""

from __future__ import annotations

from collections.abc import Iterable


def summarize(transactions: Iterable[dict], date_from: str, date_to: str) -> dict:
    rows = [t for t in transactions if t.get("txn_date") and date_from <= t["txn_date"] <= date_to]
    by_cat: dict[str, list[int]] = {}
    for t in rows:
        if t["direction"] == "DEBIT":
            by_cat.setdefault(t["category"], []).append(t["amount_paise"])
    categories = sorted(
        ({"category": c, "value_paise": sum(v), "count": len(v)} for c, v in by_cat.items()),
        key=lambda x: (-x["value_paise"], x["category"]),
    )
    recent = sorted(rows, key=lambda t: (t["txn_date"], t.get("id", 0)), reverse=True)[:20]
    return {
        "from": date_from,
        "to": date_to,
        "by_category": categories,
        "total_debit_paise": sum(t["amount_paise"] for t in rows if t["direction"] == "DEBIT"),
        "total_credit_paise": sum(t["amount_paise"] for t in rows if t["direction"] == "CREDIT"),
        "recent": recent,
    }
