"""Deterministic masking before any text leaves the process (FR-002, GR-1, research R4).

(a) OTP-like codes: 4-8 digits within 40 characters of an OTP keyword -> "[OTP]".
    Numbers directly preceded by a currency marker (Rs, INR, ₹) are amounts, not codes.
(b) Long numbers: a continuous run of >= 9 digits, or 3-4 groups of exactly 4 digits separated by
    a single space or dash (card format) -> "XXXX" + last 4 digits. Dates/times are not matched.
"""

from __future__ import annotations

import re

OTP_TOKEN = "[OTP]"  # noqa: S105 - placeholder text, not a credential
_LONG = re.compile(r"(?<![0-9])(?:[0-9]{9,}|[0-9]{4}(?:[ -][0-9]{4}){2,3})(?![0-9])")
_KEYWORD = re.compile(
    r"\b(?:otp|one[ -]?time[ -]?password|verification[ -]?code|passcode|pin|code)\b",
    re.IGNORECASE,
)
_CODE = re.compile(r"(?<![0-9.,])(?<!rs)(?<!rs\.)(?<!inr)(?<!₹)(?<!rs )(?<!rs\. )(?<!inr )"
                   r"(?<!₹ )\b[0-9]{4,8}\b(?![0-9.,]*[0-9])", re.IGNORECASE)
_WINDOW = 40


def _mask_long(text: str) -> str:
    return _LONG.sub(lambda m: "XXXX" + re.sub(r"[^0-9]", "", m.group())[-4:], text)


def _mask_otps(text: str) -> str:
    spans = [(max(0, k.start() - _WINDOW), k.end() + _WINDOW) for k in _KEYWORD.finditer(text)]
    if not spans:
        return text

    def near_keyword(m: re.Match) -> bool:
        return any(lo <= m.start() and m.end() <= hi for lo, hi in spans)

    return _CODE.sub(lambda m: OTP_TOKEN if near_keyword(m) else m.group(), text)


def mask(text: str) -> str:
    """Return the masked form of an SMS. Idempotent."""
    return _mask_otps(_mask_long(text))


def find_long_numbers(text: str) -> list[str]:
    """Long numbers per FR-002(b) still present in ``text`` (used for leak re-checks)."""
    return _LONG.findall(text)
