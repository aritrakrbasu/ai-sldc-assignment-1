"""SMS parse pipeline (T024): mask -> prompt -> LLM -> JSON -> schema -> grounding -> ParseResult."""

from __future__ import annotations

import datetime as dt
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from moneylens.core.contracts import schema, validate
from moneylens.core.grounding import ground
from moneylens.core.masking import find_long_numbers, mask

from .llm import LLMClient, ServiceError

PROMPT_VERSION = "parse_sms.v1"
PROMPT = (Path(__file__).resolve().parents[3] / "prompts" / "parse_sms.v1.md").read_text(
    encoding="utf-8")
MAX_CHARS = 1000
MAX_WORKERS = 4


def _meta(llm: LLMClient | None) -> dict:
    return {"model": getattr(llm, "model", None), "model_version": getattr(llm, "model_version",
                                                                          None),
            "temperature": getattr(llm, "temperature", None), "prompt_version": PROMPT_VERSION}


def _result(index: int, masked: str, llm, *, kind=None, body=None, error=None) -> dict:
    body = body or {}
    return {"index": index, "status": "error" if error else "ok", "error_code": error,
            "masked_text": masked, "kind": kind,
            "transaction": body.get("transaction"), "bill": body.get("bill"),
            "phishing": body.get("phishing"), "meta": _meta(llm)}


def parse_one(index: int, text: str, reference_date: str, llm: LLMClient | None) -> dict:
    if len(text) > MAX_CHARS:
        return _result(index, mask(text[:MAX_CHARS]) + "…", llm, error="MESSAGE_TOO_LONG")
    masked = mask(text)
    if not masked.strip():
        return _result(index, masked, llm, kind="OTHER")
    if llm is None:
        return _result(index, masked, llm, error="MODEL_UNAVAILABLE")
    ref = dt.date.fromisoformat(reference_date)
    user = json.dumps({"reference_date": reference_date, "reference_weekday": ref.strftime("%A"),
                       "sms": masked}, ensure_ascii=False)
    if find_long_numbers(user):  # GR-1 re-check before anything leaves the process
        return _result(index, masked, llm, error="MODEL_OUTPUT_INVALID")
    try:
        raw = llm.generate_json(PROMPT, user, schema("model_parse_output"))
    except ServiceError:
        return _result(index, masked, llm, error="MODEL_UNAVAILABLE")
    try:
        output = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return _result(index, masked, llm, error="MODEL_OUTPUT_INVALID")
    if validate("model_parse_output", output):
        return _result(index, masked, llm, error="MODEL_OUTPUT_INVALID")
    grounded, reason = ground(output, masked, reference_date)
    if grounded is None or reason:
        return _result(index, masked, llm, error="MODEL_OUTPUT_INVALID")
    result = _result(index, masked, llm, kind=grounded["kind"], body=grounded)
    if find_long_numbers(json.dumps(result)):  # INV-6 output re-check
        return _result(index, masked, llm, error="MODEL_OUTPUT_INVALID")
    return result


def parse_batch(messages: list[str], reference_date: str, llm: LLMClient | None) -> list[dict]:
    """Parse messages concurrently; results keep input order (INV-9)."""
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(parse_one, i, m, reference_date, llm)
                   for i, m in enumerate(messages)]
        return [f.result() for f in futures]
