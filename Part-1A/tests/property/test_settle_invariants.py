"""T029 [US3] — settle-up properties. SC-004, FR-014, FR-021."""

from hypothesis import given, settings
from hypothesis import strategies as st

from splitease.core.model import Member
from splitease.core.settle import settle_up


@st.composite
def zero_sum_balances(draw):
    n = draw(st.integers(2, 50))
    members = [Member(id=500 + i, name=f"M{i}", position=i) for i in range(n)]
    values = draw(st.lists(st.integers(-10**9, 10**9), min_size=n - 1, max_size=n - 1))
    values.append(-sum(values))
    return members, {m.id: v for m, v in zip(members, values, strict=True)}


@settings(max_examples=500, deadline=None)
@given(zero_sum_balances())
def test_sc004_plan_zeroes_every_balance(case):
    members, balances = case
    plan = settle_up(members, balances)
    after = dict(balances)
    for p in plan:
        assert p.amount > 0
        assert p.from_member != p.to_member
        after[p.from_member] += p.amount
        after[p.to_member] -= p.amount
    assert all(v == 0 for v in after.values())
    k = sum(1 for v in balances.values() if v != 0)
    assert len(plan) <= max(k - 1, 0)


@settings(max_examples=200, deadline=None)
@given(zero_sum_balances())
def test_fr021_plan_deterministic(case):
    members, balances = case
    assert settle_up(members, balances) == settle_up(members, dict(reversed(balances.items())))
