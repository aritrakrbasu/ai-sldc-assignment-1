"""Deterministic post-validator (FR-007, INV-3..INV-5, INV-7, GR-6, research R5).

Rejects outputs whose amounts are not present in the SMS, and nulls ungrounded account suffixes,
merchants and impossible dates. It never invents or "fixes" a value.
"""

from __future__ import annotations

import copy
import datetime as dt
import re

from .amounts import find_amounts
from .dates import parse_iso

_TOKEN = re.compile(r"[a-z0-9]{3,}")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def ground(output: dict, masked_text: str, reference_date: str) -> tuple[dict | None, str | None]:
    """Return (grounded_output, None) or (None, reason_code)."""
    out = copy.deepcopy(output)
    amounts = find_amounts(masked_text)
    ref = dt.date.fromisoformat(reference_date)
    text_tokens = _tokens(masked_text)

    txn = out.get("transaction")
    if txn:
        if txn["amount_paise"] not in amounts:
            return None, "AMOUNT_NOT_GROUNDED"
        if txn.get("account_last4") and txn["account_last4"] not in masked_text:
            txn["account_last4"] = None
        if txn.get("merchant") and not (_tokens(txn["merchant"]) & text_tokens):
            txn["merchant"] = None
        date = parse_iso(txn.get("txn_date"))
        if txn.get("txn_date") and (date is None or date > ref):
            txn["txn_date"] = None

    bill = out.get("bill")
    if bill:
        if bill.get("amount_due_paise") is not None and bill["amount_due_paise"] not in amounts:
            return None, "AMOUNT_NOT_GROUNDED"
        if bill.get("due_date") and parse_iso(bill["due_date"]) is None:
            bill["due_date"] = None
        if bill.get("biller") and not (_tokens(bill["biller"]) & text_tokens):
            bill["biller"] = None
    return out, None
