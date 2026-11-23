"""Settlement validation (T035). FR-015; data-model.md Settlement.from_member,
Settlement.to_member, Settlement.amount. Over-payment is allowed (clarification Q1)."""

from __future__ import annotations

from collections.abc import Sequence

from .errors import DomainError
from .model import Member
from .money import check_amount


def validate_settlement(
    members: Sequence[Member], from_member: int, to_member: int, amount: int
) -> None:
    ids = {m.id for m in members}
    if from_member not in ids or to_member not in ids:
        raise DomainError("UNKNOWN_MEMBER", "Both people must be members of this group")
    if from_member == to_member:
        raise DomainError("SAME_MEMBER", "Payer and receiver must be different people")
    check_amount(amount)
