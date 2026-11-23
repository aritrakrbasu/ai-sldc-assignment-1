"""CSV ledger export (T041). FR-016, FR-017, SC-006; format in contracts/api.md (C9)."""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence

from .model import Expense, Member, Settlement
from .money import format_inr

HEADER = ["date", "type", "description", "paid_by", "amount_inr", "split_mode", "participants"]
_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _safe(cell: str) -> str:
    """FR-017: neutralise spreadsheet formula injection."""
    return "'" + cell if cell.startswith(_FORMULA_PREFIXES) else cell


def build_csv(
    members: Sequence[Member], expenses: Sequence[Expense], settlements: Sequence[Settlement]
) -> str:
    ordered = sorted(members, key=lambda m: m.position)
    name = {m.id: m.name for m in ordered}
    rows: list[tuple[tuple[str, int], list[str]]] = []
    for e in expenses:
        participants = ";".join(
            f"{m.name}:{format_inr(e.shares[m.id])}" for m in ordered if m.id in e.shares
        )
        rows.append(((e.date, e.seq), [e.date, "expense", e.description, name[e.paid_by],
                                       format_inr(e.amount), e.split_mode, participants]))
    for s in settlements:
        rows.append(((s.date, s.seq), [s.date, "settlement", f"Settlement to {name[s.to_member]}",
                                       name[s.from_member], format_inr(s.amount), "",
                                       name[s.to_member]]))
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(HEADER)
    for _, row in sorted(rows, key=lambda r: r[0]):
        writer.writerow([_safe(c) for c in row])
    return buf.getvalue()
