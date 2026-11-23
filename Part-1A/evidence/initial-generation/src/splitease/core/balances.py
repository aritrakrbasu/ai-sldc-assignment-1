"""Net balances (T020, T035). FR-012, FR-013. Positive = member is owed money."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from .model import Expense, Member, Settlement


def compute_balances(
    members: Sequence[Member], expenses: Iterable[Expense], settlements: Iterable[Settlement]
) -> dict[int, int]:
    ordered = sorted(members, key=lambda m: m.position)
    balances = {m.id: 0 for m in ordered}
    for e in expenses:
        balances[e.paid_by] += e.amount
        for member_id, share in e.shares.items():
            balances[member_id] -= share
    for s in settlements:
        balances[s.from_member] += s.amount
        balances[s.to_member] -= s.amount
    return balances
