"""Pydantic request/response models (T021, T027). contracts/api.md; data-model.md
Expense.description, Expense.amount, Expense.date, Expense.split_mode, Settlement.date."""

from __future__ import annotations

import datetime as dt
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StrictInt

from splitease.core.money import MAX_AMOUNT

Paise = Annotated[StrictInt, Field(ge=1, le=MAX_AMOUNT)]


def _strip_non_empty(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("must not be blank")
    return value


Description = Annotated[str, Field(max_length=120), AfterValidator(_strip_non_empty)]


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GroupIn(_In):
    name: str
    members: list[str]


class MemberOut(BaseModel):
    id: int
    name: str
    position: int


class GroupOut(BaseModel):
    id: int
    name: str
    members: list[MemberOut]


class GroupSummary(BaseModel):
    id: int
    name: str
    member_count: int


class SplitIn(_In):
    member_id: StrictInt
    amount: StrictInt | None = None
    percent: str | None = None
    weight: StrictInt | None = None


class ExpenseIn(_In):
    description: Description
    amount: Paise
    paid_by: StrictInt
    date: dt.date
    split_mode: Literal["EQUAL", "EXACT", "PERCENT", "SHARES"]
    splits: list[SplitIn]


class ShareOut(BaseModel):
    member_id: int
    amount: int


class ExpenseOut(BaseModel):
    id: int
    description: str
    amount: int
    paid_by: int
    date: str
    split_mode: str
    splits: list[SplitIn]
    shares: list[ShareOut]


class SettlementIn(_In):
    from_member: StrictInt
    to_member: StrictInt
    amount: Paise
    date: dt.date


class SettlementOut(BaseModel):
    id: int
    from_member: int
    to_member: int
    amount: int
    date: str


class BalanceOut(BaseModel):
    member_id: int
    name: str
    balance: int


class PaymentOut(BaseModel):
    from_member: int
    to_member: int
    amount: int


class GroupDetail(GroupOut):
    expenses: list[ExpenseOut]
    settlements: list[SettlementOut]
    balances: list[BalanceOut]
    settle_up: list[PaymentOut]
