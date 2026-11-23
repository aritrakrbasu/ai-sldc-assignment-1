"""Group and member validation (T018). FR-001; data-model.md Group.name, Group.members,
Member.name, Member.position."""

from __future__ import annotations

from .errors import DomainError

MIN_MEMBERS, MAX_MEMBERS = 2, 50
MAX_MEMBER_NAME, MAX_GROUP_NAME = 40, 60


def validate_group_name(name: str) -> str:
    cleaned = name.strip()
    if not 1 <= len(cleaned) <= MAX_GROUP_NAME:
        raise DomainError("INVALID_GROUP_NAME", "Group name must be 1-60 characters")
    return cleaned


def validate_members(names: list[str]) -> list[str]:
    """Return trimmed names in the given order (member order) or raise INVALID_MEMBERS."""
    if not MIN_MEMBERS <= len(names) <= MAX_MEMBERS:
        raise DomainError("INVALID_MEMBERS", "A group needs 2-50 members")
    cleaned = [n.strip() for n in names]
    for n in cleaned:
        if not 1 <= len(n) <= MAX_MEMBER_NAME:
            raise DomainError("INVALID_MEMBERS", "Member names must be 1-40 characters")
    if len({n.casefold() for n in cleaned}) != len(cleaned):
        raise DomainError("INVALID_MEMBERS", "Member names must be unique")
    return cleaned
