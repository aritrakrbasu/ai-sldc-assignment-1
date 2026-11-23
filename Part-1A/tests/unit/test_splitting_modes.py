"""T023 [US2] — EXACT / PERCENT / SHARES. FR-005, FR-006, FR-007, FR-008, FR-009."""

import pytest

from splitease.core.errors import DomainError
from splitease.core.model import SplitInput as S
from splitease.core.splitting import compute_shares

A, B, C = 1, 2, 3


def test_us2_1_fr005_exact(abc_members):
    shares = compute_shares(abc_members, 50000, A, "EXACT",
                            [S(B, amount=20000), S(C, amount=30000)])
    assert shares == {B: 20000, C: 30000}


def test_us2_2_fr005_exact_sum_mismatch(abc_members):
    with pytest.raises(DomainError) as exc:
        compute_shares(abc_members, 50000, A, "EXACT", [S(B, amount=20000), S(C, amount=29999)])
    assert exc.value.code == "SPLIT_SUM_MISMATCH"


def test_fr005_exact_zero_amount_participant_allowed(abc_members):
    shares = compute_shares(abc_members, 100, A, "EXACT", [S(A, amount=0), S(B, amount=100)])
    assert shares == {A: 0, B: 100}


def test_edge_exact_negative_amount_rejected(abc_members):
    with pytest.raises(DomainError) as exc:
        compute_shares(abc_members, 100, A, "EXACT", [S(A, amount=-1), S(B, amount=101)])
    assert exc.value.code == "INVALID_AMOUNT"


def test_fr005_exact_missing_amount_rejected(abc_members):
    with pytest.raises(DomainError) as exc:
        compute_shares(abc_members, 100, A, "EXACT", [S(A), S(B, amount=100)])
    assert exc.value.code == "INVALID_AMOUNT"


def test_us2_3_fr006_percent_10000(abc_members):
    shares = compute_shares(abc_members, 10000, A, "PERCENT",
                            [S(A, percent="33.33"), S(B, percent="33.33"), S(C, percent="33.34")])
    assert shares == {A: 3333, B: 3333, C: 3334}


def test_us2_4_fr008_percent_100_largest_remainder(abc_members):
    shares = compute_shares(abc_members, 100, A, "PERCENT",
                            [S(A, percent="33.33"), S(B, percent="33.33"), S(C, percent="33.34")])
    assert shares == {A: 33, B: 33, C: 34}


def test_us2_5_fr006_percent_sum_not_100(abc_members):
    with pytest.raises(DomainError) as exc:
        compute_shares(abc_members, 10000, A, "PERCENT",
                       [S(A, percent="33.33"), S(B, percent="33.33"), S(C, percent="33.33")])
    assert exc.value.code == "PERCENT_SUM_INVALID"


def test_fr006_percent_over_two_decimals(abc_members):
    with pytest.raises(DomainError) as exc:
        compute_shares(abc_members, 10000, A, "PERCENT",
                       [S(A, percent="50.005"), S(B, percent="49.995")])
    assert exc.value.code == "INVALID_PERCENT"


def test_us2_6_fr007_shares_1_2_3(abc_members):
    shares = compute_shares(abc_members, 100000, A, "SHARES",
                            [S(A, weight=1), S(B, weight=2), S(C, weight=3)])
    assert shares == {A: 16667, B: 33333, C: 50000}


@pytest.mark.parametrize("weight", [0, -1, None])
def test_edge_fr007_invalid_weight(abc_members, weight):
    with pytest.raises(DomainError) as exc:
        compute_shares(abc_members, 100, A, "SHARES", [S(A, weight=weight), S(B, weight=1)])
    assert exc.value.code == "INVALID_WEIGHT"


def test_fr008_tie_broken_by_member_order(abc_members):
    # 100 paise, equal weights 1:1:1 -> floors 33,33,33; remainders all equal -> first in order.
    shares = compute_shares(abc_members, 100, A, "SHARES",
                            [S(C, weight=1), S(B, weight=1), S(A, weight=1)])
    assert shares == {A: 34, B: 33, C: 33}


def test_fr008_largest_remainder_not_first_member(abc_members):
    # 10 paise weights 1:1:2 -> exact 2.5, 2.5, 5 -> floors 2,2,5 (=9); remainders .5,.5,0
    # -> tie between A and B goes to A.
    shares = compute_shares(abc_members, 10, A, "SHARES",
                            [S(A, weight=1), S(B, weight=1), S(C, weight=2)])
    assert shares == {A: 3, B: 2, C: 5}


def test_fr008_percent_zero_participant(abc_members):
    shares = compute_shares(abc_members, 999, A, "PERCENT",
                            [S(A, percent="0"), S(B, percent="100")])
    assert shares == {A: 0, B: 999}
