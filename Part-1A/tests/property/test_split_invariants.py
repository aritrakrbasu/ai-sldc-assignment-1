"""T024 [US2] — property tests. SC-001, FR-009, FR-013, FR-021 (Hypothesis, >= 500 examples)."""

from hypothesis import given, settings
from hypothesis import strategies as st

from splitease.core.balances import compute_balances
from splitease.core.model import Expense, Member, Settlement, SplitInput
from splitease.core.money import MAX_AMOUNT
from splitease.core.splitting import compute_shares

members_st = st.integers(min_value=2, max_value=12).map(
    lambda n: [Member(id=100 + i, name=f"M{i}", position=i) for i in range(n)]
)


@st.composite
def expense_case(draw):
    members = draw(members_st)
    ids = [m.id for m in members]
    amount = draw(st.integers(min_value=1, max_value=MAX_AMOUNT))
    participants = draw(st.lists(st.sampled_from(ids), min_size=1, max_size=len(ids), unique=True))
    payer = draw(st.sampled_from(ids))
    mode = draw(st.sampled_from(["EQUAL", "EXACT", "PERCENT", "SHARES"]))
    if mode == "EQUAL":
        splits = [SplitInput(p) for p in participants]
    elif mode == "SHARES":
        splits = [SplitInput(p, weight=draw(st.integers(1, 1000))) for p in participants]
    elif mode == "EXACT":
        cuts = sorted(draw(st.lists(st.integers(0, amount), min_size=len(participants) - 1,
                                    max_size=len(participants) - 1)))
        bounds = [0, *cuts, amount]
        splits = [SplitInput(p, amount=bounds[i + 1] - bounds[i])
                  for i, p in enumerate(participants)]
    else:
        cuts = sorted(draw(st.lists(st.integers(0, 10000), min_size=len(participants) - 1,
                                    max_size=len(participants) - 1)))
        bounds = [0, *cuts, 10000]
        splits = []
        for i, p in enumerate(participants):
            bp = bounds[i + 1] - bounds[i]
            splits.append(SplitInput(p, percent=f"{bp // 100}.{bp % 100:02d}"))
    return members, amount, payer, mode, splits


@settings(max_examples=600, deadline=None)
@given(expense_case())
def test_sc001_fr009_shares_sum_to_amount_and_non_negative(case):
    members, amount, payer, mode, splits = case
    shares = compute_shares(members, amount, payer, mode, splits)
    assert sum(shares.values()) == amount
    assert all(isinstance(v, int) and v >= 0 for v in shares.values())
    assert set(shares) == {s.member_id for s in splits}


@settings(max_examples=500, deadline=None)
@given(expense_case())
def test_fr021_deterministic(case):
    members, amount, payer, mode, splits = case
    assert compute_shares(members, amount, payer, mode, splits) == compute_shares(
        members, amount, payer, mode, splits
    )


@settings(max_examples=500, deadline=None)
@given(st.data())
def test_sc001_fr013_balances_sum_zero_after_every_operation(data):
    members = data.draw(members_st)
    ids = [m.id for m in members]
    expenses, settlements = [], []
    n_ops = data.draw(st.integers(1, 15))
    for seq in range(n_ops):
        if data.draw(st.booleans()):
            amount = data.draw(st.integers(1, MAX_AMOUNT))
            payer = data.draw(st.sampled_from(ids))
            parts = data.draw(st.lists(st.sampled_from(ids), min_size=1, max_size=len(ids),
                                       unique=True))
            mode = data.draw(st.sampled_from(["EQUAL", "SHARES"]))
            splits = [SplitInput(p, weight=data.draw(st.integers(1, 50))) if mode == "SHARES"
                      else SplitInput(p) for p in parts]
            shares = compute_shares(members, amount, payer, mode, splits)
            expenses.append(Expense(seq, "e", amount, payer, "2026-01-01", mode, shares, seq))
        else:
            frm, to = data.draw(st.lists(st.sampled_from(ids), min_size=2, max_size=2,
                                         unique=True))
            amt = data.draw(st.integers(1, MAX_AMOUNT))
            settlements.append(Settlement(seq, frm, to, amt, "2026-01-01", seq))
        assert sum(compute_balances(members, expenses, settlements).values()) == 0
