"""T010 — the evaluation harness checks themselves are tested: each check must reject a
hand-made violating output and accept a valid one. No application code is imported."""

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / ".harness"))

from checks import properties, semantic, structural  # noqa: E402

META = {"model": "m", "model_version": None, "temperature": 0.2, "prompt_version": "parse.v1"}
TXN = {"amount_paise": 25000, "direction": "DEBIT", "merchant": "swiggy", "account_last4": "4821",
       "txn_date": "2026-11-18", "channel": "UPI", "category": "FOOD"}
GOOD = {"index": 0, "status": "ok", "error_code": None,
        "masked_text": "Rs.250.00 debited from A/c XX4821 on 18-11-26 to VPA swiggy@icici "
                       "(UPI Ref XXXX5012)", "kind": "TRANSACTION", "transaction": TXN,
        "bill": None, "phishing": None, "meta": META}
WEIGHTS = {"parse_transaction": {"kind": 0.30, "amount": 0.20, "direction": 0.15, "category": 0.15,
                                 "merchant": 0.10, "date": 0.05, "account": 0.05},
           "parse_other": {"kind": 0.60, "detail": 0.40},
           "ask": {"intent": 0.40, "answer": 0.40, "filters": 0.20}}
EXPECTED = {"kind": ["TRANSACTION"], "transaction": {
    "amount_paise": 25000, "direction": "DEBIT", "categories": ["FOOD"],
    "merchant_aliases": ["swiggy"], "account_last4": "4821", "txn_date": "2026-11-18"}}
CASE = {"id": "T", "reference_date": "2026-11-23", "expected": [EXPECTED],
        "checks": ["INV-3", "INV-4", "INV-5", "INV-6", "INV-7", "PROP-3", "PROP-4",
                   "AMOUNT_EXACT"], "secrets": ["432198765012"]}


def mutate(**changes):
    r = copy.deepcopy(GOOD)
    for key, value in changes.items():
        if key in TXN:
            r["transaction"][key] = value
        else:
            r[key] = value
    return r


def test_valid_output_passes_all_layers():
    body = {"results": [GOOD]}
    assert structural.check_parse_response(body, 1) == []
    assert properties.check_parse_case(CASE, body, ["prompt with XXXX5012"]) == []
    score, _ = semantic.score_parse_case(CASE, body, WEIGHTS)
    assert score == 1.0


def test_layer1_rejects_schema_violation_and_count_mismatch():
    assert structural.check_parse_response({"results": [mutate(category="SALARY")]}, 1)
    assert structural.check_parse_response({"results": [GOOD]}, 2)
    assert structural.check_parse_response({"results": [mutate(kind="OTP")]}, 1)  # INV-2


def test_inv3_ungrounded_amount():
    assert properties.inv3_amount_grounded(mutate(amount_paise=5000000))


def test_inv4_inv5_ungrounded_account_and_merchant():
    assert properties.inv4_account_grounded(mutate(account_last4="9999"))
    assert properties.inv5_merchant_grounded(mutate(merchant="Zomato"))


def test_inv6_detects_secret_and_long_numbers_but_not_dates():
    assert properties.inv6_no_leak({"t": "ref 432198765012"}, [])
    assert properties.inv6_no_leak({"t": "card 4111 1111 1111 1111"}, [])
    assert properties.inv6_no_leak({"t": "otp 482913"}, ["482913"])
    assert properties.inv6_no_leak({"t": "on 2026-11-20 14:32:11, XXXX5012"}, []) == []


def test_inv7_future_and_invalid_dates():
    assert properties.inv7_dates(mutate(txn_date="2026-11-24"), "2026-11-23")
    assert properties.inv7_dates(mutate(txn_date="2026-02-30"), "2026-11-23")


def test_prop1_prop2_prop3_prop4():
    assert properties.prop1_otp_not_transaction(GOOD, {"kind": ["OTP"]})
    assert properties.prop2_phishing(GOOD, {"kind": ["PHISHING_SUSPECT"]})
    phish_no_reason = mutate(kind="PHISHING_SUSPECT", transaction=None,
                             phishing={"reasons": []})
    assert properties.prop2_phishing(phish_no_reason, {"kind": ["PHISHING_SUSPECT"]})
    assert properties.prop3_kind_in_expected(GOOD, {"kind": ["OTHER"]})
    assert properties.prop4_direction(mutate(direction="CREDIT"), EXPECTED)


def test_money_in_text_formats():
    assert properties.money_in_text("Rs.1,250.00 INR 1,250.5 ₹1,250 Rs 1250 INR 1,02,345.60") == {
        125000, 125050, 10234560}


def test_semantic_partial_scores():
    s, d = semantic.score_parse_case(CASE, {"results": [mutate(category="SHOPPING")]}, WEIGHTS)
    assert s == 0.85 and d[0]["fields"]["category"] == 0.0
    s, _ = semantic.score_parse_case(CASE, {"results": [mutate(kind="OTHER", transaction=None)]},
                                     WEIGHTS)
    assert s == 0.0


def test_ask_recompute_and_checks():
    fx = [{"txn_date": "2026-11-17", "direction": "DEBIT", "amount_paise": 25000,
           "category": "FOOD", "merchant": "Swiggy"},
          {"txn_date": "2026-11-19", "direction": "DEBIT", "amount_paise": 40000,
           "category": "FOOD", "merchant": "Zomato"}]
    q = {"metric": "TOTAL", "direction": "DEBIT", "categories": ["FOOD"], "merchant_contains": None,
         "date_from": "2026-11-16", "date_to": "2026-11-22", "period_defaulted": False}
    assert properties.recompute_answer(q, fx) == {"value_paise": 65000, "count": 2}
    case = {"reference_date": "2026-11-23"}
    good = {"intent": "SPEND_QUERY", "query": q, "answer": {"value_paise": 65000, "count": 2}}
    assert properties.check_ask_case(case, good, fx) == []
    wrong = {**good, "answer": {"value_paise": 99999, "count": 2}}
    assert properties.check_ask_case(case, wrong, fx)
    future = {**good, "query": {**q, "date_to": "2026-11-30"}}
    assert properties.check_ask_case(case, future, fx)
    oos = {"intent": "OUT_OF_SCOPE", "query": None, "answer": {"value_paise": 1, "count": 1}}
    assert properties.check_ask_case(case, oos, fx)
