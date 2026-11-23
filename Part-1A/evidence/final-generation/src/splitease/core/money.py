"""Exact money helpers (T006). Constitution I: integers only, never floats."""

from __future__ import annotations

import re

from .errors import DomainError

MIN_AMOUNT = 1
MAX_AMOUNT = 1_000_000_000  # ₹1 crore in paise
FULL_PERCENT_BP = 10_000  # 100.00 % in basis points

_PERCENT_RE = re.compile(r"^\d{1,3}(?:\.\d{1,2})?$")


def check_amount(amount: object) -> int:
    """Validate an amount in paise (data-model.md Expense.amount / Settlement.amount)."""
    if type(amount) is not int:
        raise DomainError("INVALID_AMOUNT", "Amount must be a whole number of paise")
    if not MIN_AMOUNT <= amount <= MAX_AMOUNT:
        raise DomainError("INVALID_AMOUNT", "Amount must be between ₹0.01 and ₹1,00,00,000.00")
    return amount


def format_inr(paise: int) -> str:
    """Render paise as rupees with exactly two decimals, e.g. 100050 -> '1000.50'."""
    sign = "-" if paise < 0 else ""
    value = abs(paise)
    return f"{sign}{value // 100}.{value % 100:02d}"


def parse_percent(text: object) -> int:
    """Parse a percentage string with <= 2 decimals into integer basis points (100.00 -> 10000)."""
    if not isinstance(text, str) or not _PERCENT_RE.fullmatch(text):
        raise DomainError("INVALID_PERCENT", "Percent must be 0-100 with at most 2 decimals")
    whole, _, frac = text.partition(".")
    bp = int(whole) * 100 + int(frac.ljust(2, "0") or "0")
    if bp > FULL_PERCENT_BP:
        raise DomainError("INVALID_PERCENT", "Percent must be 0-100 with at most 2 decimals")
    return bp
