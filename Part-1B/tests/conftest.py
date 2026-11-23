"""Shared fixtures. Unit/contract tests never call the real model (constitution: Technology)."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from moneylens.ai.llm import FakeLLM
from moneylens.api.app import create_app

REF = "2026-11-23"


def txn_out(amount=25000, direction="DEBIT", merchant="Swiggy", last4="4821",
            date="2026-11-18", channel="UPI", category="FOOD"):
    return json.dumps({"kind": "TRANSACTION", "transaction": {
        "amount_paise": amount, "direction": direction, "merchant": merchant,
        "account_last4": last4, "txn_date": date, "channel": channel, "category": category},
        "bill": None, "phishing": None})


def kind_out(kind, **extra):
    body = {"kind": kind, "transaction": None, "bill": None, "phishing": None}
    body.update(extra)
    return json.dumps(body)


SWIGGY_SMS = ("Rs.250.00 debited from A/c XX4821 on 18-11-26 to VPA swiggy@icici "
              "(UPI Ref 432198765012). Not you? Call 18001234567")


@pytest.fixture
def fake():
    return FakeLLM()


@pytest.fixture
def client_factory(tmp_path):
    def make(llm, splitease=None):
        app = create_app(db_path=str(tmp_path / "t.sqlite3"), llm=llm, splitease=splitease)
        return TestClient(app)
    return make
