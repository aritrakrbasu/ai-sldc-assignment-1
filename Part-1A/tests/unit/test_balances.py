"""T014 [US1] — balances. FR-012, FR-013 (+ FR-015 settlement effect, US4)."""

from splitease.core.balances import compute_balances
from splitease.core.model import Expense, Settlement

A, B, C = 1, 2, 3


def exp(amount, paid_by, shares, seq=1):
    return Expense(id=seq, description="x", amount=amount, paid_by=paid_by, date="2026-11-01",
                   split_mode="EQUAL", shares=shares, seq=seq)


def test_fr012_no_activity_all_zero(abc_members):
    assert compute_balances(abc_members, [], []) == {A: 0, B: 0, C: 0}


def test_us1_2_fr012_equal_three_way(abc_members):
    e = exp(100000, A, {A: 33334, B: 33333, C: 33333})
    assert compute_balances(abc_members, [e], []) == {A: 66666, B: -33333, C: -33333}


def test_us1_3_fr012_payer_not_participant(abc_members):
    e = exp(90000, A, {B: 45000, C: 45000})
    assert compute_balances(abc_members, [e], []) == {A: 90000, B: -45000, C: -45000}


def test_fr012_balances_ordered_by_member_order(abc_members):
    e = exp(90000, A, {B: 45000, C: 45000})
    assert list(compute_balances(abc_members, [e], []).keys()) == [A, B, C]


def test_us4_1_fr015_settlement_reduces_debt(abc_members):
    e = exp(100000, A, {A: 33334, B: 33333, C: 33333})
    s = Settlement(id=1, from_member=B, to_member=A, amount=33333, date="2026-11-02", seq=2)
    assert compute_balances(abc_members, [e], [s]) == {A: 33333, B: 0, C: -33333}


def test_us4_4_overpayment_flips_sign(abc_members):
    e = exp(66666, A, {B: 33333, C: 33333})
    s1 = Settlement(id=1, from_member=C, to_member=A, amount=33333, date="2026-11-02", seq=2)
    s2 = Settlement(id=2, from_member=B, to_member=A, amount=50000, date="2026-11-02", seq=3)
    bal = compute_balances(abc_members, [e], [s1, s2])
    assert bal == {A: -16667, B: 16667, C: 0}


def test_fr013_sum_zero_multiple_expenses(abc_members):
    es = [exp(100000, A, {A: 33334, B: 33333, C: 33333}, 1),
          exp(5000, B, {C: 5000}, 2), exp(7, C, {A: 3, B: 2, C: 2}, 3)]
    assert sum(compute_balances(abc_members, es, []).values()) == 0
