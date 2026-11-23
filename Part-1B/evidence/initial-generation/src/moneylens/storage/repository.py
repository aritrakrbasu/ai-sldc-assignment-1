"""SQLite persistence (T015) — data-model.md. Only masked text is ever stored (FR-002)."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT NOT NULL UNIQUE,
    masked_text TEXT NOT NULL,
    kind TEXT NOT NULL,
    reference_date TEXT NOT NULL,
    phishing_reasons TEXT,
    model TEXT, model_version TEXT, temperature REAL, prompt_version TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL UNIQUE REFERENCES messages(id) ON DELETE CASCADE,
    amount_paise INTEGER NOT NULL CHECK (amount_paise BETWEEN 1 AND 10000000000),
    direction TEXT NOT NULL CHECK (direction IN ('DEBIT','CREDIT')),
    merchant TEXT, account_last4 TEXT, txn_date TEXT,
    channel TEXT NOT NULL, category TEXT NOT NULL,
    shared_expense_id INTEGER
);
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL UNIQUE REFERENCES messages(id) ON DELETE CASCADE,
    amount_due_paise INTEGER, due_date TEXT, biller TEXT
);
"""

TXN_COLUMNS = ("t.id, t.amount_paise, t.direction, t.merchant, t.account_last4, t.txn_date, "
               "t.channel, t.category, t.shared_expense_id, m.masked_text, m.reference_date")


def content_hash(masked_text: str) -> str:
    return hashlib.sha256(masked_text.strip().encode("utf-8")).hexdigest()


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

    def save_result(self, result: dict, reference_date: str) -> bool:
        """Persist an ok ParseResult. Returns False if it is a duplicate (FR-008)."""
        now = dt.datetime.now(dt.UTC).isoformat(timespec="seconds")
        meta = result["meta"]
        reasons = (result.get("phishing") or {}).get("reasons")
        with self._tx() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO messages (content_hash, masked_text, kind, reference_date, "
                    "phishing_reasons, model, model_version, temperature, prompt_version, "
                    "created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (content_hash(result["masked_text"]), result["masked_text"], result["kind"],
                     reference_date, json.dumps(reasons) if reasons else None, meta["model"],
                     meta.get("model_version"), meta["temperature"], meta["prompt_version"], now))
            except sqlite3.IntegrityError:
                return False
            mid = cur.lastrowid
            t = result.get("transaction")
            if t:
                conn.execute(
                    "INSERT INTO transactions (message_id, amount_paise, direction, merchant, "
                    "account_last4, txn_date, channel, category) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (mid, t["amount_paise"], t["direction"], t["merchant"], t["account_last4"],
                     t["txn_date"], t["channel"], t["category"]))
            b = result.get("bill")
            if b:
                conn.execute("INSERT INTO bills (message_id, amount_due_paise, due_date, biller) "
                             "VALUES (?, ?, ?, ?)",
                             (mid, b["amount_due_paise"], b["due_date"], b["biller"]))
        return True

    def add_transaction_record(self, txn: dict, reference_date: str) -> int:
        """Insert a known transaction (used to seed fixtures for evaluation of questions)."""
        text = f"[fixture {txn.get('id')}] {txn['direction']} {txn['amount_paise']} " \
               f"{txn.get('merchant') or ''} {txn.get('txn_date') or ''}"
        result = {"masked_text": text, "kind": "TRANSACTION", "phishing": None, "bill": None,
                  "meta": {"model": None, "model_version": None, "temperature": None,
                           "prompt_version": "fixture"},
                  "transaction": {k: txn.get(k) for k in
                                  ("amount_paise", "direction", "merchant", "account_last4",
                                   "txn_date", "channel", "category")}}
        self.save_result(result, reference_date)
        with self._lock:
            return int(self._conn.execute("SELECT MAX(id) FROM transactions").fetchone()[0])

    def list_transactions(self, limit: int | None = None) -> list[dict]:
        sql = (f"SELECT {TXN_COLUMNS} FROM transactions t JOIN messages m ON m.id = t.message_id "  # noqa: S608
               "ORDER BY COALESCE(t.txn_date, m.reference_date) DESC, t.id DESC")
        params: tuple = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def transactions_for_query(self) -> list[dict]:
        """Transactions with null txn_date fall back to the message reference date
        (data-model.md Query)."""
        return [t | {"txn_date": t["txn_date"] or t["reference_date"]}
                for t in self.list_transactions()]

    def get_transaction(self, tid: int) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                f"SELECT {TXN_COLUMNS} FROM transactions t JOIN messages m "  # noqa: S608
                "ON m.id = t.message_id WHERE t.id = ?", (tid,)).fetchone()
        return dict(row) if row else None

    def mark_shared(self, tid: int, expense_id: int) -> None:
        with self._tx() as conn:
            conn.execute("UPDATE transactions SET shared_expense_id = ? WHERE id = ?",
                         (expense_id, tid))
