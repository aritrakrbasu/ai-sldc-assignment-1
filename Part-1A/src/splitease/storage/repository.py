"""SQLite persistence (T010). Parameterised SQL only (constitution V, Bandit B608). FR-019.

Balances and settle-up plans are never stored; they are recomputed by the core.
"""

from __future__ import annotations

import datetime as dt
import sqlite3
import threading
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Any

from splitease.core.model import Expense, Member, Settlement, SplitInput

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    next_seq INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    position INTEGER NOT NULL,
    UNIQUE (group_id, position)
);
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK (amount BETWEEN 1 AND 1000000000),
    paid_by INTEGER NOT NULL REFERENCES members(id),
    date TEXT NOT NULL,
    split_mode TEXT NOT NULL CHECK (split_mode IN ('EQUAL','EXACT','PERCENT','SHARES')),
    seq INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS expense_splits (
    expense_id INTEGER NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    member_id INTEGER NOT NULL REFERENCES members(id),
    amount INTEGER,
    percent TEXT,
    weight INTEGER,
    share INTEGER NOT NULL,
    PRIMARY KEY (expense_id, member_id)
);
CREATE TABLE IF NOT EXISTS settlements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    from_member INTEGER NOT NULL REFERENCES members(id),
    to_member INTEGER NOT NULL REFERENCES members(id),
    amount INTEGER NOT NULL CHECK (amount BETWEEN 1 AND 1000000000),
    date TEXT NOT NULL,
    seq INTEGER NOT NULL
);
"""


class Repository:
    def __init__(self, path: str) -> None:
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(SCHEMA)

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except BaseException:
                self._conn.rollback()
                raise

    def _next_seq(self, conn: sqlite3.Connection, group_id: int) -> int:
        seq = conn.execute("SELECT next_seq FROM groups WHERE id = ?", (group_id,)).fetchone()[0]
        conn.execute("UPDATE groups SET next_seq = next_seq + 1 WHERE id = ?", (group_id,))
        return int(seq)

    # ---- groups -------------------------------------------------------------------------
    def create_group(self, name: str, member_names: Sequence[str]) -> int:
        now = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
        with self._tx() as conn:
            cur = conn.execute("INSERT INTO groups (name, created_at) VALUES (?, ?)", (name, now))
            gid = int(cur.lastrowid or 0)
            conn.executemany(
                "INSERT INTO members (group_id, name, position) VALUES (?, ?, ?)",
                [(gid, n, i) for i, n in enumerate(member_names)],
            )
        return gid

    def list_groups(self) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT g.id, g.name, COUNT(m.id) AS member_count FROM groups g "
                "LEFT JOIN members m ON m.group_id = g.id GROUP BY g.id ORDER BY g.id"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_group(self, group_id: int) -> tuple[str, list[Member]] | None:
        with self._lock:
            row = self._conn.execute("SELECT name FROM groups WHERE id = ?", (group_id,)).fetchone()
            if row is None:
                return None
            members = self._conn.execute(
                "SELECT id, name, position FROM members WHERE group_id = ? ORDER BY position",
                (group_id,),
            ).fetchall()
        return row["name"], [Member(r["id"], r["name"], r["position"]) for r in members]

    # ---- expenses -----------------------------------------------------------------------
    def add_expense(
        self,
        group_id: int,
        description: str,
        amount: int,
        paid_by: int,
        date: str,
        split_mode: str,
        splits: Sequence[SplitInput],
        shares: dict[int, int],
    ) -> int:
        with self._tx() as conn:
            seq = self._next_seq(conn, group_id)
            cur = conn.execute(
                "INSERT INTO expenses (group_id, description, amount, paid_by, date, split_mode, "
                "seq) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (group_id, description, amount, paid_by, date, split_mode, seq),
            )
            eid = int(cur.lastrowid or 0)
            conn.executemany(
                "INSERT INTO expense_splits (expense_id, member_id, amount, percent, weight, share)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [(eid, s.member_id, s.amount, s.percent, s.weight, shares[s.member_id])
                 for s in splits],
            )
        return eid

    def list_expenses(self, group_id: int) -> list[tuple[Expense, list[SplitInput]]]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM expenses WHERE group_id = ? ORDER BY seq", (group_id,)
            ).fetchall()
            split_rows = self._conn.execute(
                "SELECT s.* FROM expense_splits s JOIN expenses e ON e.id = s.expense_id "
                "WHERE e.group_id = ?",
                (group_id,),
            ).fetchall()
        by_expense: dict[int, list[sqlite3.Row]] = {}
        for s in split_rows:
            by_expense.setdefault(s["expense_id"], []).append(s)
        out = []
        for r in rows:
            srows = by_expense.get(r["id"], [])
            expense = Expense(
                id=r["id"], description=r["description"], amount=r["amount"],
                paid_by=r["paid_by"], date=r["date"], split_mode=r["split_mode"],
                shares={s["member_id"]: s["share"] for s in srows}, seq=r["seq"],
            )
            inputs = [SplitInput(s["member_id"], s["amount"], s["percent"], s["weight"])
                      for s in srows]
            out.append((expense, inputs))
        return out

    def delete_expense(self, group_id: int, expense_id: int) -> bool:
        with self._tx() as conn:
            cur = conn.execute(
                "DELETE FROM expenses WHERE id = ? AND group_id = ?", (expense_id, group_id)
            )
        return cur.rowcount == 1

    # ---- settlements (immutable: no update/delete) --------------------------------------
    def add_settlement(
        self, group_id: int, from_member: int, to_member: int, amount: int, date: str
    ) -> int:
        with self._tx() as conn:
            seq = self._next_seq(conn, group_id)
            cur = conn.execute(
                "INSERT INTO settlements (group_id, from_member, to_member, amount, date, seq) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (group_id, from_member, to_member, amount, date, seq),
            )
        return int(cur.lastrowid or 0)

    def list_settlements(self, group_id: int) -> list[Settlement]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM settlements WHERE group_id = ? ORDER BY seq", (group_id,)
            ).fetchall()
        return [Settlement(r["id"], r["from_member"], r["to_member"], r["amount"], r["date"],
                           r["seq"]) for r in rows]
