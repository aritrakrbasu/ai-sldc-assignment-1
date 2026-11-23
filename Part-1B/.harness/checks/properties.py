"""Layer 2 — property / invariant checks (spec INV-3..INV-8, PROP-1..PROP-5, GR-*).

Independent re-implementation from the spec text. Every function returns a list of violation
strings; an empty list means the property holds.
"""

from __future__ import annotations

import datetime as dt
import json
import re

# Money mention: Rs / Rs. / INR / ₹ followed by a number with optional Indian/intl grouping.
_MONEY = re.compile(r"(?:rs\.?|inr|₹)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.IGNORECASE)
_LONG_DIGITS = re.compile(r"(?<!\d)(?:\d{9,}|\d{4}(?:[ -]\d{4}){2,3})(?!\d)")  # spec FR-002(b)
_TOKEN = re.compile(r"[a-z0-9]{3,}")


def money_in_text(text: str) -> set[int]:
    found = set()
    for raw in _MONEY.findall(text):
        whole, _, frac = raw.replace(",", "").partition(".")
        if whole:
            found.add(int(whole) * 100 + int((frac + "00")[:2]))
    return found


def _iso(value: str | None) -> dt.date | None:
    try:
        return dt.date.fromisoformat(value) if value else None
    except ValueError:
        return dt.date.min  # invalid date sentinel


def inv3_amount_grounded(result: dict) -> list[str]:
    text = result.get("masked_text") or ""
    amounts = money_in_text(text)
    out = []
    for field, obj, key in (("transaction.amount_paise", result.get("transaction"), "amount_paise"),
                            ("bill.amount_due_paise", result.get("bill"), "amount_due_paise")):
        if obj and obj.get(key) is not None and obj[key] not in amounts:
            out.append(f"INV-3: {field}={obj[key]} not among amounts in text {sorted(amounts)}")
    return out


def inv4_account_grounded(result: dict) -> list[str]:
    txn = result.get("transaction") or {}
    last4 = txn.get("account_last4")
    if last4 and last4 not in (result.get("masked_text") or ""):
        return [f"INV-4: account_last4={last4} not in text"]
    return []


def inv5_merchant_grounded(result: dict) -> list[str]:
    txn = result.get("transaction") or {}
    merchant = txn.get("merchant")
    if not merchant:
        return []
    text_tokens = set(_TOKEN.findall((result.get("masked_text") or "").lower()))
    if not set(_TOKEN.findall(merchant.lower())) & text_tokens:
        return [f"INV-5: merchant '{merchant}' shares no >=3-char token with text"]
    return []


def inv6_no_leak(payload: object, secrets: list[str]) -> list[str]:
    blob = json.dumps(payload, ensure_ascii=False)
    out = [f"INV-6: secret '{s[:2]}…' leaked" for s in secrets if s and s in blob]
    for m in _LONG_DIGITS.finditer(blob):
        out.append(f"INV-6: unmasked long digit run '{m.group()[:3]}…' ({len(m.group())} chars)")
    return out


def inv7_dates(result: dict, reference_date: str) -> list[str]:
    ref = dt.date.fromisoformat(reference_date)
    out = []
    txn = result.get("transaction") or {}
    bill = result.get("bill") or {}
    if txn.get("txn_date") is not None:
        d = _iso(txn["txn_date"])
        if d == dt.date.min:
            out.append(f"INV-7: invalid txn_date {txn['txn_date']}")
        elif d > ref:
            out.append(f"INV-7: txn_date {txn['txn_date']} after reference {reference_date}")
    if bill.get("due_date") is not None and _iso(bill["due_date"]) == dt.date.min:
        out.append(f"INV-7: invalid due_date {bill['due_date']}")
    return out


def prop1_otp_not_transaction(result: dict, expected: dict) -> list[str]:
    if "OTP" in expected.get("kind", []) and result.get("kind") == "TRANSACTION":
        return ["PROP-1: OTP message classified as TRANSACTION"]
    return []


def prop2_phishing(result: dict, expected: dict) -> list[str]:
    if expected.get("kind") != ["PHISHING_SUSPECT"]:
        return []
    if result.get("kind") != "PHISHING_SUSPECT":
        return [f"PROP-2: phishing classified as {result.get('kind')}"]
    if not (result.get("phishing") or {}).get("reasons"):
        return ["PROP-2: phishing without reasons"]
    return []


def prop3_kind_in_expected(result: dict, expected: dict) -> list[str]:
    kinds = expected.get("kind")
    if kinds and result.get("kind") not in kinds:
        return [f"PROP-3: kind {result.get('kind')} not in expected {kinds}"]
    return []


def prop4_direction(result: dict, expected: dict) -> list[str]:
    exp = (expected.get("transaction") or {}).get("direction")
    got = (result.get("transaction") or {}).get("direction")
    if exp and got and exp != got:
        return [f"PROP-4: direction {got}, expected {exp}"]
    if exp and result.get("kind") == "TRANSACTION" and not got:
        return ["PROP-4: missing direction"]
    return []


def amount_exact(result: dict, expected: dict) -> list[str]:
    exp = (expected.get("transaction") or {}).get("amount_paise")
    got = (result.get("transaction") or {}).get("amount_paise")
    if exp is not None and got != exp:
        return [f"AMOUNT_EXACT: amount {got}, expected {exp}"]
    return []


PARSE_CHECKS = {
    "INV-3": lambda r, e, c: inv3_amount_grounded(r),
    "INV-4": lambda r, e, c: inv4_account_grounded(r),
    "INV-5": lambda r, e, c: inv5_merchant_grounded(r),
    "INV-7": lambda r, e, c: inv7_dates(r, c["reference_date"]),
    "PROP-1": lambda r, e, c: prop1_otp_not_transaction(r, e),
    "PROP-2": lambda r, e, c: prop2_phishing(r, e),
    "PROP-3": lambda r, e, c: prop3_kind_in_expected(r, e),
    "PROP-4": lambda r, e, c: prop4_direction(r, e),
    "AMOUNT_EXACT": lambda r, e, c: amount_exact(r, e),
}


def check_parse_case(case: dict, body: dict, prompts_sent: list[str]) -> list[str]:
    problems: list[str] = []
    results = body.get("results", [])
    for pos, (result, expected) in enumerate(zip(results, case["expected"], strict=False)):
        if expected.get("status") == "error":
            continue  # expected error results are scored in Layer 3
        if result.get("status") == "error":
            continue  # MODEL_* errors handled as service/invalid outside this layer
        for check_id in case["checks"]:
            if check_id == "INV-6":
                continue
            fn = PARSE_CHECKS.get(check_id)
            if fn is None:
                raise KeyError(f"unknown check {check_id} in case {case['id']}")
            problems += [f"msg[{pos}] {p}" for p in fn(result, expected, case)]
    if "INV-6" in case["checks"]:
        problems += inv6_no_leak(body, case.get("secrets", []))
        problems += [f"(prompt) {p}" for p in inv6_no_leak(prompts_sent, case.get("secrets", []))]
    return problems


# ---------------------------------------------------------------- ask
def recompute_answer(query: dict, transactions: list[dict]) -> dict:
    """Independent recomputation of the deterministic answer (SC-005)."""
    rows = [t for t in transactions
            if query["date_from"] <= t["txn_date"] <= query["date_to"]
            and t["direction"] == query["direction"]
            and (not query["categories"] or t["category"] in query["categories"])
            and (not query.get("merchant_contains")
                 or query["merchant_contains"].lower() in (t["merchant"] or "").lower())]
    total = sum(t["amount_paise"] for t in rows)
    n = len(rows)
    metric = query["metric"]
    value = {"TOTAL": total, "LIST": total, "TOP_MERCHANTS": total, "COUNT": None,
             "AVERAGE": total // n if n else 0,
             "LARGEST": max((t["amount_paise"] for t in rows), default=None)}[metric]
    return {"value_paise": value, "count": n}


def check_ask_case(case: dict, body: dict, fixture: list[dict]) -> list[str]:
    problems: list[str] = []
    ref = case["reference_date"]
    if body.get("intent") in ("OUT_OF_SCOPE", "NEEDS_CLARIFICATION") and body.get("answer"):
        problems.append("PROP-5: answer returned for non-spend intent")
    query = body.get("query")
    if body.get("intent") == "SPEND_QUERY" and query:
        if not query["date_from"] <= query["date_to"] <= ref:
            problems.append(f"INV-8: dates {query['date_from']}..{query['date_to']} vs ref {ref}")
        else:
            expected = recompute_answer(query, fixture)
            got = body.get("answer") or {}
            if (got.get("value_paise"), got.get("count")) != (expected["value_paise"],
                                                               expected["count"]):
                problems.append(f"INV-8/SC-005: app answer {got.get('value_paise')}/"
                                f"{got.get('count')} != recomputed {expected}")
    problems += inv6_no_leak(body, [])
    return problems
