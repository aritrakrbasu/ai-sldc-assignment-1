"""T028 [US3] — settle-up plan. FR-014, constitution performance constraint."""

import time

from splitease.core.model import Member, Payment
from splitease.core.settle import settle_up

A, B, C = 1, 2, 3


def apply(balances, plan):
    out = dict(balances)
    for p in plan:
        out[p.from_member] += p.amount
        out[p.to_member] -= p.amount
    return out


def test_us3_1_exact_plan(abc_members):
    plan = settle_up(abc_members, {A: 66666, B: -33333, C: -33333})
    assert plan == [Payment(B, A, 33333), Payment(C, A, 33333)]


def test_us3_3_all_zero_empty_plan(abc_members):
    assert settle_up(abc_members, {A: 0, B: 0, C: 0}) == []


def test_us3_2_plan_zeroes_balances(abc_members):
    bal = {A: -16667, B: 16667, C: 0}
    plan = settle_up(abc_members, bal)
    assert plan == [Payment(A, B, 16667)]
    assert set(apply(bal, plan).values()) == {0}


def test_fr014_largest_debtor_to_largest_creditor():
    members = [Member(i, f"M{i}", i - 1) for i in range(1, 5)]
    bal = {1: 500, 2: 300, 3: -600, 4: -200}
    plan = settle_up(members, bal)
    # step1: debtor 3 (600) -> creditor 1 (500): 500 ; step2: debtor 3 (100) vs 4 (200)
    # -> largest debtor now 4 (200) -> creditor 2 (300): 200 ; step3: 3 -> 2: 100
    assert plan == [Payment(3, 1, 500), Payment(4, 2, 200), Payment(3, 2, 100)]
    assert set(apply(bal, plan).values()) == {0}
    assert len(plan) <= 4 - 1


def test_fr014_ties_by_member_order():
    members = [Member(i, f"M{i}", i - 1) for i in range(1, 5)]
    bal = {1: -100, 2: -100, 3: 100, 4: 100}
    assert settle_up(members, bal) == [Payment(1, 3, 100), Payment(2, 4, 100)]


def test_fr014_member_order_uses_position_not_id():
    members = [Member(9, "Z", 0), Member(1, "Y", 1), Member(5, "X", 2)]
    bal = {9: -100, 1: -100, 5: 200}
    assert settle_up(members, bal) == [Payment(9, 5, 100), Payment(1, 5, 100)]


def test_constitution_perf_50_members_under_100ms():
    """SC-003 / constitution: settle-up for 50 members in < 100 ms."""
    members = [Member(i, f"M{i}", i) for i in range(50)]
    bal = {i: (i * 7919) % 100000 - 50000 for i in range(49)}
    bal[49] = -sum(bal.values())
    start = time.perf_counter()
    plan = settle_up(members, bal)
    elapsed = time.perf_counter() - start
    assert elapsed < 0.1
    assert set(apply(bal, plan).values()) == {0}
    assert len(plan) <= sum(1 for v in bal.values() if v) - 1
