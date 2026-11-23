"""T033 [US4] — settlement validation. FR-015."""

import pytest

from splitease.core.errors import DomainError
from splitease.core.settlements import validate_settlement

A, B, C = 1, 2, 3


def test_fr015_valid_settlement(abc_members):
    validate_settlement(abc_members, B, A, 33333)


def test_us4_2_same_member_rejected(abc_members):
    with pytest.raises(DomainError) as exc:
        validate_settlement(abc_members, A, A, 100)
    assert exc.value.code == "SAME_MEMBER"


@pytest.mark.parametrize("amount", [0, -5])
def test_us4_3_non_positive_amount_rejected(abc_members, amount):
    with pytest.raises(DomainError) as exc:
        validate_settlement(abc_members, B, A, amount)
    assert exc.value.code == "INVALID_AMOUNT"


@pytest.mark.parametrize(("frm", "to"), [(99, A), (A, 99)])
def test_fr015_unknown_member_rejected(abc_members, frm, to):
    with pytest.raises(DomainError) as exc:
        validate_settlement(abc_members, frm, to, 100)
    assert exc.value.code == "UNKNOWN_MEMBER"
