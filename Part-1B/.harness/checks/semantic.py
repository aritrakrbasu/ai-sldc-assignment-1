"""Layer 3 — semantic / quality scoring against ground truth (spec Evaluation Threshold)."""

from __future__ import annotations

import re

_WORD = re.compile(r"[a-z0-9]+")


def _norm(text: str | None) -> str:
    return " ".join(_WORD.findall((text or "").lower()))


def _alias_match(value: str | None, aliases: list[str] | None) -> float:
    if aliases is None:  # not scored for this case
        return 1.0
    if not value:
        return 0.0
    norm = _norm(value).replace(" ", "")
    return 1.0 if any(_norm(a).replace(" ", "") in norm for a in aliases) else 0.0


def score_message(result: dict, expected: dict, weights: dict) -> tuple[float, dict]:
    """Return (score in [0,1], per-field detail)."""
    if expected.get("status") == "error":
        ok = (result.get("status") == "error"
              and result.get("error_code") == expected.get("error_code"))
        return (1.0 if ok else 0.0), {"error_code": ok}

    kind_ok = 1.0 if result.get("kind") in expected["kind"] else 0.0
    if "transaction" in expected:
        w = weights["parse_transaction"]
        exp = expected["transaction"]
        got = result.get("transaction") or {}
        detail = {
            "kind": kind_ok,
            "amount": 1.0 if got.get("amount_paise") == exp["amount_paise"] else 0.0,
            "direction": 1.0 if got.get("direction") == exp["direction"] else 0.0,
            "category": 1.0 if got.get("category") in exp["categories"] else 0.0,
            "merchant": _alias_match(got.get("merchant"), exp.get("merchant_aliases")),
            "date": 1.0 if got.get("txn_date") == exp.get("txn_date") else 0.0,
            "account": 1.0 if got.get("account_last4") == exp.get("account_last4") else 0.0,
        }
        return round(sum(w[k] * v for k, v in detail.items()), 4), detail

    w = weights["parse_other"]
    detail_score = 1.0
    if "bill" in expected:
        exp, got = expected["bill"], result.get("bill") or {}
        parts = [got.get("amount_due_paise") == exp["amount_due_paise"],
                 got.get("due_date") == exp["due_date"],
                 _alias_match(got.get("biller"), exp.get("biller_aliases")) == 1.0]
        detail_score = sum(parts) / len(parts)
    elif "reasons_any" in expected:
        reasons = set((result.get("phishing") or {}).get("reasons") or [])
        detail_score = 1.0 if reasons & set(expected["reasons_any"]) else 0.0
    if not kind_ok:
        detail_score = 0.0
    detail = {"kind": kind_ok, "detail": detail_score}
    return round(w["kind"] * kind_ok + w["detail"] * detail_score, 4), detail


def score_parse_case(case: dict, body: dict, weights: dict) -> tuple[float, list[dict]]:
    results = body.get("results", [])
    scores, details = [], []
    for pos, expected in enumerate(case["expected"]):
        result = results[pos] if pos < len(results) else {}
        s, d = score_message(result, expected, weights)
        scores.append(s)
        details.append({"message": pos, "score": s, "fields": d})
    return round(sum(scores) / len(scores), 4), details


def score_ask_case(case: dict, body: dict, weights: dict) -> tuple[float, dict]:
    w = weights["ask"]
    exp = case["expected"]
    intent_ok = 1.0 if body.get("intent") in exp["intent"] else 0.0
    if exp["intent"] != ["SPEND_QUERY"]:
        answer_ok = filters_ok = 1.0 if (intent_ok and body.get("answer") is None) else 0.0
    else:
        got = body.get("answer") or {}
        answer_ok = 1.0 if intent_ok and all(got.get(k) == v for k, v in exp["answer"].items()) \
            else 0.0
        q = body.get("query") or {}
        f = exp["filters"]
        parts = [q.get("metric") in f["metric"],
                 sorted(q.get("categories") or []) in [sorted(c) for c in f["categories"]],
                 q.get("date_from") == f["date_from"], q.get("date_to") == f["date_to"],
                 q.get("direction") == f["direction"]]
        if f.get("period_defaulted") is not None:
            parts.append(q.get("period_defaulted") is f["period_defaulted"])
        filters_ok = sum(parts) / len(parts) if intent_ok else 0.0
    detail = {"intent": intent_ok, "answer": answer_ok, "filters": round(filters_ok, 4)}
    return round(sum(w[k] * v for k, v in detail.items()), 4), detail
