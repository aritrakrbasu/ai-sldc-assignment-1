"""Exact expense splitting (T019, T026). FR-004 .. FR-010.

data-model.md Expense.splits, Expense.paid_by, Expense.shares, SplitInput.amount,
SplitInput.percent, SplitInput.weight.
"""

from __future__ import annotations

from collections.abc import Sequence

from .errors import DomainError
from .model import Member, SplitInput
from .money import FULL_PERCENT_BP, check_amount, parse_percent

MODES = ("EQUAL", "EXACT", "PERCENT", "SHARES")


def _ordered_participants(
    members: Sequence[Member], paid_by: int, splits: Sequence[SplitInput]
) -> list[SplitInput]:
    position = {m.id: m.position for m in members}
    if paid_by not in position:
        raise DomainError("UNKNOWN_MEMBER", "Payer is not a member of this group")
    if not splits:
        raise DomainError("EMPTY_SPLIT", "Select at least one participant")
    seen: set[int] = set()
    for s in splits:
        if s.member_id not in position:
            raise DomainError("UNKNOWN_MEMBER", "Participant is not a member of this group")
        if s.member_id in seen:
            raise DomainError("DUPLICATE_PARTICIPANT", "A participant appears twice")
        seen.add(s.member_id)
    return sorted(splits, key=lambda s: position[s.member_id])


def _largest_remainder(amount: int, weighted: list[tuple[int, int]]) -> dict[int, int]:
    """FR-008: floor of exact share, leftover paise to largest remainders, ties by order.

    ``weighted`` is a list of (member_id, weight) already in member order.
    """
    total = sum(w for _, w in weighted)
    shares: dict[int, int] = {}
    remainders: list[tuple[int, int, int]] = []  # (-remainder, order index, member id)
    for idx, (mid, weight) in enumerate(weighted):
        quotient, remainder = divmod(amount * weight, total)
        shares[mid] = quotient
        remainders.append((-remainder, idx, mid))
    leftover = amount - sum(shares.values())
    for _, _, mid in sorted(remainders)[:leftover]:
        shares[mid] += 1
    return shares


def compute_shares(
    members: Sequence[Member],
    amount: int,
    paid_by: int,
    split_mode: str,
    splits: Sequence[SplitInput],
) -> dict[int, int]:
    """Return {member_id: share_in_paise} for every participant; sum == amount (FR-009)."""
    check_amount(amount)
    if split_mode not in MODES:
        raise DomainError("INVALID_SPLIT_MODE", "Split mode must be EQUAL, EXACT, PERCENT or SHARES")
    parts = _ordered_participants(members, paid_by, splits)

    if split_mode == "EQUAL":
        base, rem = divmod(amount, len(parts))
        shares = {p.member_id: base + (1 if i < rem else 0) for i, p in enumerate(parts)}

    elif split_mode == "EXACT":
        shares = {}
        for p in parts:
            if type(p.amount) is not int or p.amount < 0:
                raise DomainError("INVALID_AMOUNT", "Each exact amount must be ≥ 0 paise")
            shares[p.member_id] = p.amount
        if sum(shares.values()) != amount:
            raise DomainError(
                "SPLIT_SUM_MISMATCH",
                f"Exact amounts add up to {sum(shares.values())} paise, expected {amount}",
            )

    elif split_mode == "PERCENT":
        weighted = [(p.member_id, parse_percent(p.percent)) for p in parts]
        if sum(w for _, w in weighted) != FULL_PERCENT_BP:
            raise DomainError("PERCENT_SUM_INVALID", "Percentages must add up to exactly 100")
        shares = _largest_remainder(amount, weighted)

    else:  # SHARES
        weighted = []
        for p in parts:
            if type(p.weight) is not int or p.weight < 1:
                raise DomainError("INVALID_WEIGHT", "Each weight must be a whole number ≥ 1")
            weighted.append((p.member_id, p.weight))
        shares = _largest_remainder(amount, weighted)

    return shares
