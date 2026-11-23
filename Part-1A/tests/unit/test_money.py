"""T007 — money helpers. Constitution I, FR-006 (percent parsing), FR-016 (formatting)."""

import pytest

from splitease.core.errors import DomainError
from splitease.core.money import MAX_AMOUNT, check_amount, format_inr, parse_percent


@pytest.mark.parametrize(
    ("paise", "text"),
    [(0, "0.00"), (1, "0.01"), (10, "0.10"), (100000, "1000.00"), (33333, "333.33"),
     (1_000_000_000, "10000000.00"), (-16667, "-166.67")],
)
def test_fr016_format_inr_two_decimals(paise, text):
    assert format_inr(paise) == text


@pytest.mark.parametrize(
    ("text", "bp"),
    [("100", 10000), ("33.33", 3333), ("33.34", 3334), ("0", 0), ("0.5", 50), ("12.05", 1205),
     ("100.00", 10000)],
)
def test_fr006_parse_percent_to_basis_points(text, bp):
    assert parse_percent(text) == bp


@pytest.mark.parametrize("text", ["33.333", "-1", "abc", "", "1e2", "100.01", "101", " 5", "5."])
def test_fr006_parse_percent_rejects_invalid(text):
    with pytest.raises(DomainError) as exc:
        parse_percent(text)
    assert exc.value.code == "INVALID_PERCENT"


def test_fr006_parse_percent_rejects_float_type():
    with pytest.raises(DomainError):
        parse_percent(33.33)  # type: ignore[arg-type]


@pytest.mark.parametrize("amount", [1, 500, MAX_AMOUNT])
def test_fr003_amount_in_range_accepted(amount):
    check_amount(amount)


@pytest.mark.parametrize("amount", [0, -1, MAX_AMOUNT + 1])
def test_fr003_amount_out_of_range_rejected(amount):
    with pytest.raises(DomainError) as exc:
        check_amount(amount)
    assert exc.value.code == "INVALID_AMOUNT"


@pytest.mark.parametrize("amount", [1.0, "100", True])
def test_constitution_i_amount_must_be_int(amount):
    with pytest.raises(DomainError) as exc:
        check_amount(amount)
    assert exc.value.code == "INVALID_AMOUNT"


def test_max_amount_is_one_crore_rupees():
    assert MAX_AMOUNT == 1_000_000_000
