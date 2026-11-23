"""Immutable domain value types (T008), mirroring data-model.md."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Member:
    id: int
    name: str
    position: int  # member order (0-based); tie-break key everywhere


@dataclass(frozen=True)
class SplitInput:
    member_id: int
    amount: int | None = None  # EXACT
    percent: str | None = None  # PERCENT, e.g. "33.33"
    weight: int | None = None  # SHARES


@dataclass(frozen=True)
class Expense:
    id: int
    description: str
    amount: int
    paid_by: int
    date: str
    split_mode: str
    shares: dict[int, int] = field(default_factory=dict)
    seq: int = 0


@dataclass(frozen=True)
class Settlement:
    id: int
    from_member: int
    to_member: int
    amount: int
    date: str
    seq: int = 0


@dataclass(frozen=True)
class Payment:
    from_member: int
    to_member: int
    amount: int
