"""Layer 1 — structural validation (spec INV-1, INV-2, INV-9) against the JSON Schema contracts."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator

CONTRACTS = Path(__file__).resolve().parents[2] / "specs" / "001-sms-finance-inbox" / "contracts"


@cache
def _validator(name: str) -> Draft202012Validator:
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema)


def _errors(name: str, obj: object) -> list[str]:
    return [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
            for e in _validator(name).iter_errors(obj)]


def check_parse_response(body: object, n_messages: int) -> list[str]:
    """Return a list of Layer-1 violations for a /api/parse response body."""
    if not isinstance(body, dict) or not isinstance(body.get("results"), list):
        return ["INV-1: response is not {results: [...]}"]
    results = body["results"]
    problems: list[str] = []
    if len(results) != n_messages:
        problems.append(f"INV-9: expected {n_messages} results, got {len(results)}")
    for pos, result in enumerate(results):
        problems += [f"INV-1/2 result[{pos}] {e}" for e in _errors("parse_result", result)]
        if isinstance(result, dict) and result.get("index") != pos:
            problems.append(f"INV-9: result[{pos}].index = {result.get('index')}")
    return problems


def check_ask_response(body: object) -> list[str]:
    return [f"INV-1 {e}" for e in _errors("query_result", body)]
