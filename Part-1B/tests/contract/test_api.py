"""T020, T032, T035 — HTTP contracts M1-M8 (FakeLLM; fake SplitEase via httpx.MockTransport)."""

import json

import httpx
import pytest

from moneylens.ai.llm import FakeLLM
from moneylens.core.contracts import validate
from moneylens.splitease_client import SplitEaseClient
from tests.conftest import REF, SWIGGY_SMS, kind_out, txn_out


def parse(client, messages, save=True):
    return client.post("/api/parse", json={"messages": messages, "reference_date": REF,
                                           "save": save})


# ---- M1 -------------------------------------------------------------------------------
def test_m1_parse_ok_schema_valid(client_factory):
    with client_factory(FakeLLM([txn_out()])) as c:
        r = parse(c, [SWIGGY_SMS])
    assert r.status_code == 200
    [res] = r.json()["results"]
    assert validate("parse_result", res) == []


@pytest.mark.parametrize("messages", [[], ["x"] * 51])
def test_m1_invalid_batch(client_factory, messages):
    with client_factory(FakeLLM([])) as c:
        r = parse(c, messages)
    assert r.status_code == 400 and r.json()["error"]["code"] == "INVALID_BATCH"


def test_fr008_duplicate_detected(client_factory):
    with client_factory(FakeLLM([txn_out(), txn_out()])) as c:
        first = parse(c, [SWIGGY_SMS]).json()["results"][0]
        second = parse(c, [SWIGGY_SMS]).json()["results"][0]
        txns = c.get("/api/transactions").json()
    assert first["status"] == "ok"
    assert (second["status"], second["error_code"]) == ("error", "DUPLICATE")
    assert validate("parse_result", second) == []
    assert len(txns) == 1


def test_save_false_stores_nothing(client_factory):
    with client_factory(FakeLLM([txn_out()])) as c:
        parse(c, [SWIGGY_SMS], save=False)
        assert c.get("/api/transactions").json() == []


def test_otp_never_stored_raw(client_factory, tmp_path):
    with client_factory(FakeLLM([kind_out("OTP")])) as c:
        parse(c, ["482913 is your OTP"])
    raw = (tmp_path / "t.sqlite3").read_bytes()
    assert b"482913" not in raw


# ---- M2, M3 ---------------------------------------------------------------------------
def test_m2_dashboard(client_factory):
    with client_factory(FakeLLM([txn_out()])) as c:
        parse(c, [SWIGGY_SMS])
        d = c.get("/api/dashboard", params={"from": "2026-11-01", "to": "2026-11-30"}).json()
    assert d["by_category"] == [{"category": "FOOD", "value_paise": 25000, "count": 1}]
    assert d["recent"][0]["merchant"] == "Swiggy"


# ---- M4 -------------------------------------------------------------------------------
def test_m4_ask(client_factory):
    query = {"metric": "TOTAL", "direction": "DEBIT", "categories": ["FOOD"],
             "merchant_contains": None, "date_from": "2026-11-01", "date_to": "2026-11-23",
             "period_defaulted": False}
    ask = json.dumps({"intent": "SPEND_QUERY", "query": query, "clarification": None})
    with client_factory(FakeLLM([txn_out(), ask])) as c:
        parse(c, [SWIGGY_SMS])
        r = c.post("/api/ask", json={"question": "Food this month?", "reference_date": REF})
    body = r.json()
    assert r.status_code == 200 and validate("query_result", body) == []
    assert body["answer"]["value_paise"] == 25000


@pytest.mark.parametrize("question", ["", "q" * 301])
def test_m4_invalid_question_422(client_factory, question):
    with client_factory(FakeLLM([])) as c:
        r = c.post("/api/ask", json={"question": question})
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR"


# ---- M8 -------------------------------------------------------------------------------
def test_m8_health_never_exposes_key(client_factory, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "super-secret-test-key")
    with client_factory(FakeLLM([])) as c:
        body = c.get("/api/health").text
    assert "super-secret-test-key" not in body


# ---- M5-M7 SplitEase (US5) ------------------------------------------------------------
class FakeSplitEase:
    def __init__(self, fail=None):
        self.posts = []
        self.fail = fail

    def handler(self, request: httpx.Request) -> httpx.Response:
        if self.fail == "down":
            raise httpx.ConnectError("refused")
        if request.method == "GET" and request.url.path == "/api/groups":
            return httpx.Response(200, json=[{"id": 1, "name": "Flat", "member_count": 2}])
        if request.method == "GET" and request.url.path == "/api/groups/1":
            return httpx.Response(200, json={"id": 1, "name": "Flat", "members": [
                {"id": 11, "name": "Riya", "position": 0}, {"id": 12, "name": "Sam",
                                                            "position": 1}]})
        if request.method == "POST" and request.url.path == "/api/groups/1/expenses":
            self.posts.append(json.loads(request.content))
            if self.fail == "400":
                return httpx.Response(400, json={"error": {"code": "UNKNOWN_MEMBER",
                                                           "message": "bad member"}})
            return httpx.Response(201, json={"id": 77})
        return httpx.Response(404, json={"error": {"code": "NOT_FOUND", "message": "x"}})


def split_env(client_factory, responses, fail=None):
    fake = FakeSplitEase(fail)
    se = SplitEaseClient("http://splitease.test", transport=httpx.MockTransport(fake.handler))
    return client_factory(FakeLLM(responses), splitease=se), fake


SPLIT = {"group_id": 1, "paid_by": 11, "participants": [11, 12]}


def tid(c):
    return c.get("/api/transactions").json()[0]["id"]


def test_us5_1_preview_sends_nothing(client_factory):
    client, fake = split_env(client_factory, [txn_out()])
    with client as c:
        parse(c, [SWIGGY_SMS])
        r = c.post(f"/api/transactions/{tid(c)}/split", json={**SPLIT, "confirm": False})
    assert r.status_code == 200
    assert r.json()["status"] == "preview" and r.json()["code"] == "CONFIRMATION_REQUIRED"
    assert fake.posts == []


def test_us5_2_confirm_sends_exactly_one_correct_expense(client_factory):
    client, fake = split_env(client_factory, [txn_out()])
    with client as c:
        parse(c, [SWIGGY_SMS])
        t = tid(c)
        r = c.post(f"/api/transactions/{t}/split", json={**SPLIT, "confirm": True})
        again = c.post(f"/api/transactions/{t}/split", json={**SPLIT, "confirm": True})
    assert r.status_code == 201 and r.json()["splitease_expense_id"] == 77
    assert fake.posts == [{"description": "Swiggy", "amount": 25000, "paid_by": 11,
                           "date": "2026-11-18", "split_mode": "EQUAL",
                           "splits": [{"member_id": 11}, {"member_id": 12}]}]
    assert again.status_code == 400 and again.json()["error"]["code"] == "ALREADY_SHARED"


def test_us5_3_credit_rejected(client_factory):
    client, fake = split_env(client_factory, [txn_out(direction="CREDIT", category="INCOME")])
    with client as c:
        parse(c, ["Rs.250.00 credited to A/c XX4821 on 18-11-26 from Swiggy refund"])
        r = c.post(f"/api/transactions/{tid(c)}/split", json={**SPLIT, "confirm": True})
    assert r.status_code == 400 and r.json()["error"]["code"] == "NOT_A_DEBIT"
    assert fake.posts == []


def test_us5_4_splitease_down(client_factory):
    client, _ = split_env(client_factory, [txn_out()], fail="down")
    with client as c:
        parse(c, [SWIGGY_SMS])
        t = tid(c)
        r = c.post(f"/api/transactions/{t}/split", json={**SPLIT, "confirm": True})
        shared = c.get("/api/transactions").json()[0]["shared_expense_id"]
    assert r.status_code == 502 and r.json()["error"]["code"] == "SPLITEASE_UNAVAILABLE"
    assert shared is None


def test_fr016_splitease_error_passthrough(client_factory):
    client, _ = split_env(client_factory, [txn_out()], fail="400")
    with client as c:
        parse(c, [SWIGGY_SMS])
        r = c.post(f"/api/transactions/{tid(c)}/split", json={**SPLIT, "confirm": True})
    assert r.status_code == 400 and r.json()["error"]["code"] == "UNKNOWN_MEMBER"


def test_m5_m6_groups_proxy(client_factory):
    client, _ = split_env(client_factory, [])
    with client as c:
        assert c.get("/api/splitease/groups").json()[0]["name"] == "Flat"
        assert len(c.get("/api/splitease/groups/1").json()["members"]) == 2


def test_split_unknown_transaction(client_factory):
    client, _ = split_env(client_factory, [])
    with client as c:
        r = c.post("/api/transactions/999/split", json={**SPLIT, "confirm": True})
    assert r.status_code == 404 and r.json()["error"]["code"] == "TRANSACTION_NOT_FOUND"
