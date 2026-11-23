"""Question answering (T034): question -> LLM structured query -> validate -> deterministic answer.

The model never supplies figures (constitution II); ``core.query_exec.execute`` computes them.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from moneylens.core.contracts import schema, validate
from moneylens.core.query_exec import execute

from .llm import LLMClient, ServiceError

PROMPT_VERSION = "query.v1"
PROMPT = (Path(__file__).resolve().parents[3] / "prompts" / "query.v1.md").read_text(
    encoding="utf-8")


def _base(question: str, reference_date: str, llm: LLMClient | None) -> dict:
    return {"status": "ok", "error_code": None, "question": question,
            "reference_date": reference_date, "intent": None, "query": None,
            "clarification": None, "answer": None,
            "meta": {"model": getattr(llm, "model", None),
                     "model_version": getattr(llm, "model_version", None),
                     "temperature": getattr(llm, "temperature", None),
                     "prompt_version": PROMPT_VERSION}}


def _error(result: dict, code: str) -> dict:
    return {**result, "status": "error", "error_code": code, "intent": None, "query": None,
            "clarification": None, "answer": None}


def answer_question(question: str, reference_date: str, llm: LLMClient | None,
                    transactions: list[dict]) -> dict:
    result = _base(question, reference_date, llm)
    if llm is None:
        return _error(result, "MODEL_UNAVAILABLE")
    ref = dt.date.fromisoformat(reference_date)
    user = json.dumps({"reference_date": reference_date, "reference_weekday": ref.strftime("%A"),
                       "question": question}, ensure_ascii=False)
    try:
        raw = llm.generate_json(PROMPT, user, schema("model_query_output"))
        output = json.loads(raw)
    except ServiceError:
        return _error(result, "MODEL_UNAVAILABLE")
    except (json.JSONDecodeError, TypeError):
        return _error(result, "MODEL_OUTPUT_INVALID")
    if validate("model_query_output", output):
        return _error(result, "MODEL_OUTPUT_INVALID")
    query = output["query"]
    if query is not None and not (query["date_from"] <= query["date_to"] <= reference_date):
        return _error(result, "MODEL_OUTPUT_INVALID")  # INV-8
    result.update(intent=output["intent"], query=query, clarification=output["clarification"])
    if output["intent"] == "SPEND_QUERY":
        result["answer"] = execute(query, transactions)
    return result
