"""T017 [US1] — FR-002 / GR-1 masking before the model."""

import pytest

from moneylens.core.masking import find_long_numbers, mask


@pytest.mark.parametrize(
    ("text", "secret"),
    [("482913 is your OTP for login to SBI YONO.", "482913"),
     ("Your OTP is 551247 for Paytm login. Never share it.", "551247"),
     ("OTP 739201 for txn of Rs 4,999.00 at FLIPKART", "739201"),
     ("Use verification code 0045 to continue", "0045"),
     ("Your one time password: 12345678. Valid 10 min", "12345678"),
     ("Passcode for card activation is 9911", "9911")],
)
def test_fr002_otp_masked(text, secret):
    out = mask(text)
    assert secret not in out
    assert "[OTP]" in out


@pytest.mark.parametrize(
    ("text", "masked_part", "secret"),
    [("card 4111 1111 1111 1111 used", "XXXX1111", "4111 1111 1111 1111"),
     ("card 4111-1111-1111-1111 used", "XXXX1111", "4111-1111-1111-1111"),
     ("UPI Ref 432198765012).", "XXXX5012", "432198765012"),
     ("Call 18001234567", "XXXX4567", "18001234567")],
)
def test_fr002_long_numbers_masked_keep_last4(text, masked_part, secret):
    out = mask(text)
    assert secret not in out
    assert masked_part in out


@pytest.mark.parametrize(
    "text",
    ["Rs.250.00 debited from A/c XX4821 on 18-11-26",
     "Card ending 3344 for Rs 1,499.00 at AMAZON PAY INDIA on 2026-11-20 14:32:11.",
     "INR 2,35,000.00 debited, Avl Bal INR 1,02,345.60",
     "Rs.2000 withdrawn at ATM S1BW0123 from A/c X9902 on 21NOV26",
     "Get flat 50% off. Use code PIZZA50."],
)
def test_fr002_amounts_dates_and_last4_untouched(text):
    assert mask(text) == text


def test_mask_is_idempotent():
    once = mask("OTP 739201 card 4111 1111 1111 1111")
    assert mask(once) == once


def test_find_long_numbers_spec_definition():
    assert find_long_numbers("ref 432198765012 and 4111 1111 1111 1111")
    assert find_long_numbers("on 2026-11-20 14:32:11 XXXX5012 Rs 1,02,345.60") == []
