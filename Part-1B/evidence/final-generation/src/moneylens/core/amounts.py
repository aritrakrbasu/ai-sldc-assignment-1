"""Find every INR amount mentioned in a text, as integer paise (supports INV-3 grounding)."""

from __future__ import annotations

import re

_NUM = r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)"
_PREFIX = re.compile(r"(?:\brs\b\.?|\binr\b|₹)\s*" + _NUM, re.IGNORECASE)
_SUFFIX = re.compile(_NUM + r"\s*(?:\binr\b|\brs\b)", re.IGNORECASE)


def _to_paise(raw: str) -> int | None:
    whole, _, frac = raw.replace(",", "").partition(".")
    if not whole:
        return None
    return int(whole) * 100 + int((frac + "00")[:2])


def find_amounts(text: str) -> set[int]:
    found: set[int] = set()
    for pattern in (_PREFIX, _SUFFIX):
        for raw in pattern.findall(text):
            paise = _to_paise(raw)
            if paise:
                found.add(paise)
    return found
