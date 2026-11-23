"""T031 [US4] — question answering with FakeLLM (INV-8, PROP-5, FR-013, FR-014)."""

import json

from moneylens.ai.llm import FakeLLM, ServiceError
from moneylens.ai.qa import answer_question
from moneylens.core.contracts import validate

TX = [{"id": 1, "txn_date": "2026-11-17", "direction": "DEBIT", "amount_paise": 25000,
       "merchant": "Swiggy", "category": "FOOD"},
      {"id": 2, "txn_date": "2026-11-19", "direction": "DEBIT", "amount_paise": 40000,
       "merchant": "Zomato", "category": "FOOD"}]
REF = "2026-11-23"


def spend(**kw):
    query = {"metric": "TOTAL", "direction": "DEBIT", "categories": ["FOOD"],
             "merchant_contains": None, "date_from": "2026-11-16", "date_to": "2026-11-22",
             "period_defaulted": False} | kw
    return json.dumps({"intent": "SPEND_QUERY", "query": query, "clarification": None})


def test_us4_1_answer_computed_by_app():
    r = answer_question("How much did I spend on food last week?", REF, FakeLLM([spend()]), TX)
    assert validate("query_result", r) == []
    assert r["answer"]["value_paise"] == 65000 and r["answer"]["count"] == 2
    assert r["query"]["categories"] == ["FOOD"]


def test_inv8_future_date_to_rejected():
    r = answer_question("food?", REF, FakeLLM([spend(date_to="2026-11-30")]), TX)
    assert (r["status"], r["error_code"], r["answer"]) == ("error", "MODEL_OUTPUT_INVALID", None)
    assert validate("query_result", r) == []


def test_inv8_reversed_dates_rejected():
    r = answer_question("food?", REF, FakeLLM([spend(date_from="2026-11-22",
                                                      date_to="2026-11-16")]), TX)
    assert r["error_code"] == "MODEL_OUTPUT_INVALID"


def test_prop5_out_of_scope_has_no_answer():
    oos = json.dumps({"intent": "OUT_OF_SCOPE", "query": None,
                      "clarification": "I can only answer questions about your transactions."})
    r = answer_question("Should I buy gold?", REF, FakeLLM([oos]), TX)
    assert r["intent"] == "OUT_OF_SCOPE" and r["answer"] is None
    assert validate("query_result", r) == []


def test_model_cannot_inject_numbers():
    extra = json.loads(spend())
    extra["answer"] = {"value_paise": 1, "count": 1}
    r = answer_question("food?", REF, FakeLLM([json.dumps(extra)]), TX)
    assert r["error_code"] == "MODEL_OUTPUT_INVALID"  # additionalProperties forbidden


def test_service_error():
    r = answer_question("food?", REF, FakeLLM([ServiceError("down")]), TX)
    assert (r["status"], r["error_code"]) == ("error", "MODEL_UNAVAILABLE")
    assert validate("query_result", r) == []


def test_prompt_includes_reference_date_and_weekday():
    llm = FakeLLM([spend()])
    answer_question("food last week?", REF, llm, TX)
    assert "2026-11-23" in llm.calls[0]["user"] and "Monday" in llm.calls[0]["user"]
