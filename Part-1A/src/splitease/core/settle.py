"""Greedy settle-up plan (T031). FR-014, research R4.

Repeatedly match the largest debtor with the largest creditor, paying the smaller absolute
value; ties broken by member order. Produces at most k-1 payments.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .model import Member, Payment


def settle_up(members: Sequence[Member], balances: Mapping[int, int]) -> list[Payment]:
    position = {m.id: m.position for m in members}
    remaining = {mid: bal for mid, bal in balances.items() if bal != 0}
    plan: list[Payment] = []
    while remaining:
        debtor = min((m for m in remaining if remaining[m] < 0),
                     key=lambda m: (remaining[m], position[m]))
        creditor = max((m for m in remaining if remaining[m] > 0),
                       key=lambda m: (remaining[m], -position[m]))
        amount = min(-remaining[debtor], remaining[creditor])
        plan.append(Payment(from_member=debtor, to_member=creditor, amount=amount))
        for mid, delta in ((debtor, amount), (creditor, -amount)):
            remaining[mid] += delta
            if remaining[mid] == 0:
                del remaining[mid]
    return plan
