"""Shared fixtures (T012). Tests are derived from specs/001-shared-expense-splitter."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from splitease.api.app import create_app
from splitease.core.model import Member


@pytest.fixture
def client(tmp_path):
    app = create_app(db_path=str(tmp_path / "test.sqlite3"))
    with TestClient(app) as c:
        yield c


@pytest.fixture
def make_group(client):
    def _make(names=("Asha", "Bilal", "Chen"), name="Flat 4B"):
        resp = client.post("/api/groups", json={"name": name, "members": list(names)})
        assert resp.status_code == 201, resp.text
        body = resp.json()
        ids = {m["name"]: m["id"] for m in body["members"]}
        return body["id"], ids

    return _make


@pytest.fixture
def abc_members():
    """Members A, B, C in member order with ids 1, 2, 3."""
    return [Member(id=1, name="A", position=0), Member(id=2, name="B", position=1),
            Member(id=3, name="C", position=2)]
