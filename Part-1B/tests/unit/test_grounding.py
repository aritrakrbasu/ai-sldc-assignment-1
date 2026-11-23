"""T018 [US1] / T027 [US2] — deterministic post-validator (INV-3..INV-5, INV-7, GR-6)."""

from moneylens.core.grounding import ground

TEXT = "Rs.250.00 debited from A/c XX4821 on 18-11-26 to VPA swiggy@icici. Avl Bal Rs 5,000.00"
REF = "2026-11-23"


def out(**txn):
    base = {"amount_paise": 25000, "direction": "DEBIT", "merchant": "Swiggy",
            "account_last4": "4821", "txn_date": "2026-11-18", "channel": "UPI",
            "category": "FOOD"}
    base.update(txn)
    return {"kind": "TRANSACTION", "transaction": base, "bill": None, "phishing": None}


def test_grounded_output_unchanged():
    result, reason = ground(out(), TEXT, REF)
    assert reason is None
    assert result == out()


def test_inv3_ungrounded_amount_rejected():
    result, reason = ground(out(amount_paise=5000000), TEXT, REF)
    assert result is None and reason == "AMOUNT_NOT_GROUNDED"


def test_inv3_balance_amount_is_grounded_text_amount():
    # Picking the balance is a semantic error (scored by the harness), not a grounding error.
    result, reason = ground(out(amount_paise=500000), TEXT, REF)
    assert reason is None


def test_inv4_ungrounded_last4_nulled():
    result, _ = ground(out(account_last4="9999"), TEXT, REF)
    assert result["transaction"]["account_last4"] is None


def test_inv5_ungrounded_merchant_nulled():
    result, _ = ground(out(merchant="Zomato"), TEXT, REF)
    assert result["transaction"]["merchant"] is None


def test_inv7_future_or_invalid_date_nulled():
    assert ground(out(txn_date="2026-11-30"), TEXT, REF)[0]["transaction"]["txn_date"] is None
    assert ground(out(txn_date="2026-02-30"), TEXT, REF)[0]["transaction"]["txn_date"] is None


def test_bill_amount_grounding_and_bad_date():
    bill_text = "BESCOM bill of Rs 1,846.00 is due on 28-11-2026"
    good = {"kind": "BILL_REMINDER", "transaction": None, "phishing": None,
            "bill": {"amount_due_paise": 184600, "due_date": "2026-11-28", "biller": "BESCOM"}}
    assert ground(good, bill_text, REF) == (good, None)
    bad = {**good, "bill": {**good["bill"], "amount_due_paise": 999}}
    assert ground(bad, bill_text, REF) == (None, "AMOUNT_NOT_GROUNDED")
    bad_date = {**good, "bill": {**good["bill"], "due_date": "2026-13-01"}}
    assert ground(bad_date, bill_text, REF)[0]["bill"]["due_date"] is None


def test_non_transaction_untouched():
    otp = {"kind": "OTP", "transaction": None, "bill": None, "phishing": None}
    assert ground(otp, "Your OTP is [OTP]", REF) == (otp, None)
