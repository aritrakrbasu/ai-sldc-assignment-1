"""Deterministic execution of a validated query (FR-011, INV-8, constitution II).

Every figure shown to the user is computed here. See data-model.md "Query" table.
"""

from __future__ import annotations

from collections.abc import Iterable


def _matches(t: dict, q: dict) -> bool:
    merchant = q.get("merchant_contains")
    return (q["date_from"] <= t["txn_date"] <= q["date_to"]
            and t["direction"] == q["direction"]
            and (not q["categories"] or t["category"] in q["categories"])
            and (not merchant or merchant.lower() in (t.get("merchant") or "").lower()))


def _recent_first(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda t: (t["txn_date"], t.get("id", 0)), reverse=True)


def execute(query: dict, transactions: Iterable[dict]) -> dict:
    rows = [t for t in transactions if t.get("txn_date") and _matches(t, query)]
    total = sum(t["amount_paise"] for t in rows)
    n = len(rows)
    metric = query["metric"]
    items: list[dict] = []
    if metric == "TOTAL":
        value: int | None = total
    elif metric == "COUNT":
        value = None
    elif metric == "AVERAGE":
        value = total // n if n else 0
    elif metric == "LARGEST":
        top = max(rows, key=lambda t: (t["amount_paise"], t["txn_date"]), default=None)
        value = top["amount_paise"] if top else None
        items = [top] if top else []
    elif metric == "LIST":
        value = total
        items = _recent_first(rows)[:20]
    else:  # TOP_MERCHANTS
        value = total
        groups: dict[str, list[int]] = {}
        for t in rows:
            groups.setdefault(t.get("merchant") or "(unknown)", []).append(t["amount_paise"])
        ranked = sorted(groups.items(), key=lambda kv: (-sum(kv[1]), kv[0]))[:5]
        items = [{"merchant": m, "value_paise": sum(v), "count": len(v)} for m, v in ranked]
    return {"value_paise": value, "count": n, "items": items}
