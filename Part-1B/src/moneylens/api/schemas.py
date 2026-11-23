"""Request models (contracts/api.md). Responses follow the JSON Schema contracts."""

from __future__ import annotations

import datetime as dt
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ParseIn(_In):
    messages: list[str]
    reference_date: dt.date | None = None
    save: StrictBool = True


class AskIn(_In):
    question: Annotated[str, Field(min_length=1, max_length=300)]
    reference_date: dt.date | None = None


class SplitIn(_In):
    group_id: StrictInt
    paid_by: StrictInt
    participants: Annotated[list[StrictInt], Field(min_length=1)]
    confirm: StrictBool = False
