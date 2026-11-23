"""Property tests for GR-1 / INV-6: masking never leaks a long number and is idempotent."""

from hypothesis import given, settings
from hypothesis import strategies as st

from moneylens.core.masking import find_long_numbers, mask

digits = st.text(alphabet="0123456789", min_size=9, max_size=19)
words = st.text(alphabet="abcdefghij RsINR.,:-", max_size=40)


@settings(max_examples=300, deadline=None)
@given(words, digits, words)
def test_long_number_never_survives(prefix, number, suffix):
    out = mask(f"{prefix} {number} {suffix}")
    assert number not in out
    assert find_long_numbers(out) == []


@settings(max_examples=300, deadline=None)
@given(st.integers(1000, 99999999), words)
def test_otp_never_survives(code, filler):
    out = mask(f"Your OTP is {code}. {filler}")
    assert f" {code}" not in out


@settings(max_examples=300, deadline=None)
@given(st.text(max_size=200))
def test_idempotent(text):
    assert mask(mask(text)) == mask(text)
