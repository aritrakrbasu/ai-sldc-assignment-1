"""Load and validate the spec's JSON Schema contracts (constitution I).

The schemas live in specs/001-sms-finance-inbox/contracts/ and are the single source of truth for
both the application and the evaluation harness. Reading them is file I/O at import time only.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator

CONTRACTS = Path(__file__).resolve().parents[3] / "specs" / "001-sms-finance-inbox" / "contracts"


@cache
def schema(name: str) -> dict:
    return json.loads((CONTRACTS / f"{name}.schema.json").read_text(encoding="utf-8"))


@cache
def _validator(name: str) -> Draft202012Validator:
    return Draft202012Validator(schema(name))


def validate(name: str, obj: object) -> list[str]:
    """Return human-readable violations (empty list = valid)."""
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in _validator(name).iter_errors(obj)]
