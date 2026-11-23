"""T017 [US1] + T025 [US2] — contract C4, C7. FR-003..FR-010, FR-018, SC-005 (edge-case codes)."""

import pytest


def add(client, gid, **kw):
    body = {"description": "Groceries", "amount": 100000, "date": "2026-11-20",
            "split_mode": "EQUAL"} | kw
    return client.post(f"/api/groups/{gid}/expenses", json=body)


def balances(client, gid):
    r = client.get(f"/api/groups/{gid}/balances")
    assert r.status_code == 200
    return {b["name"]: b["balance"] for b in r.json()}


def test_us1_2_c4_equal_expense_and_c7_balances(client, make_group):
    gid, m = make_group()
    r = add(client, gid, paid_by=m["Asha"],
            splits=[{"member_id": m[n]} for n in ("Asha", "Bilal", "Chen")])
    assert r.status_code == 201
    body = r.json()
    assert {s["member_id"]: s["amount"] for s in body["shares"]} == {
        m["Asha"]: 33334, m["Bilal"]: 33333, m["Chen"]: 33333}
    assert balances(client, gid) == {"Asha": 66666, "Bilal": -33333, "Chen": -33333}


def test_c7_balances_in_member_order(client, make_group):
    gid, m = make_group()
    r = client.get(f"/api/groups/{gid}/balances")
    assert [b["name"] for b in r.json()] == ["Asha", "Bilal", "Chen"]


def test_us1_3_c4_payer_not_participant(client, make_group):
    gid, m = make_group()
    r = add(client, gid, amount=90000, paid_by=m["Asha"],
            splits=[{"member_id": m["Bilal"]}, {"member_id": m["Chen"]}])
    assert r.status_code == 201
    assert balances(client, gid) == {"Asha": 90000, "Bilal": -45000, "Chen": -45000}


def test_us2_1_c4_exact(client, make_group):
    gid, m = make_group()
    r = add(client, gid, amount=50000, paid_by=m["Asha"], split_mode="EXACT",
            splits=[{"member_id": m["Bilal"], "amount": 20000},
                    {"member_id": m["Chen"], "amount": 30000}])
    assert r.status_code == 201
    assert balances(client, gid) == {"Asha": 50000, "Bilal": -20000, "Chen": -30000}


def test_us2_3_c4_percent(client, make_group):
    gid, m = make_group()
    r = add(client, gid, amount=10000, paid_by=m["Asha"], split_mode="PERCENT",
            splits=[{"member_id": m["Asha"], "percent": "33.33"},
                    {"member_id": m["Bilal"], "percent": "33.33"},
                    {"member_id": m["Chen"], "percent": "33.34"}])
    assert r.status_code == 201
    assert [s["amount"] for s in r.json()["shares"]] == [3333, 3333, 3334]


def test_us2_6_c4_shares(client, make_group):
    gid, m = make_group()
    r = add(client, gid, amount=100000, paid_by=m["Asha"], split_mode="SHARES",
            splits=[{"member_id": m["Asha"], "weight": 1}, {"member_id": m["Bilal"], "weight": 2},
                    {"member_id": m["Chen"], "weight": 3}])
    assert r.status_code == 201
    assert [s["amount"] for s in r.json()["shares"]] == [16667, 33333, 50000]


@pytest.mark.parametrize(
    ("mode", "splits_fn", "code"),
    [
        ("EXACT", lambda m: [{"member_id": m["Bilal"], "amount": 49999}], "SPLIT_SUM_MISMATCH"),
        ("PERCENT", lambda m: [{"member_id": m["Bilal"], "percent": "99.99"}],
         "PERCENT_SUM_INVALID"),
        ("SHARES", lambda m: [{"member_id": m["Bilal"], "weight": 0}], "INVALID_WEIGHT"),
        ("EQUAL", lambda m: [{"member_id": 9999}], "UNKNOWN_MEMBER"),
        ("EQUAL", lambda m: [{"member_id": m["Bilal"]}, {"member_id": m["Bilal"]}],
         "DUPLICATE_PARTICIPANT"),
        ("EQUAL", lambda m: [], "EMPTY_SPLIT"),
        ("PERCENT", lambda m: [{"member_id": m["Bilal"], "percent": "99.999"}],
         "INVALID_PERCENT"),
    ],
)
def test_us2_c4_domain_errors_400_and_nothing_saved(client, make_group, mode, splits_fn, code):
    gid, m = make_group()
    r = add(client, gid, amount=50000, paid_by=m["Asha"], split_mode=mode, splits=splits_fn(m))
    assert r.status_code == 400, r.text
    assert r.json()["error"]["code"] == code
    assert client.get(f"/api/groups/{gid}").json()["expenses"] == []


def test_c4_unknown_payer_400(client, make_group):
    gid, m = make_group()
    r = add(client, gid, paid_by=12345, splits=[{"member_id": m["Asha"]}])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "UNKNOWN_MEMBER"


def test_c4_member_of_other_group_rejected(client, make_group):
    gid, m = make_group()
    _, other = make_group(name="Other", names=("X", "Y"))
    r = add(client, gid, paid_by=m["Asha"], splits=[{"member_id": other["X"]}])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "UNKNOWN_MEMBER"


@pytest.mark.parametrize(
    "override",
    [{"amount": 0}, {"amount": 1_000_000_001}, {"amount": 10.5}, {"amount": "100"},
     {"description": ""}, {"description": "   "}, {"description": "d" * 121},
     {"date": "2026-13-01"}, {"date": "yesterday"}, {"split_mode": "HALF"}],
)
def test_fr003_c4_schema_violations_422(client, make_group, override):
    gid, m = make_group()
    r = add(client, gid, paid_by=m["Asha"], splits=[{"member_id": m["Asha"]}], **override)
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get(f"/api/groups/{gid}").json()["expenses"] == []


def test_fr003_c4_boundary_amounts_ok(client, make_group):
    gid, m = make_group()
    for amount in (1, 1_000_000_000):
        r = add(client, gid, amount=amount, paid_by=m["Asha"], splits=[{"member_id": m["Asha"]}])
        assert r.status_code == 201
    assert add(client, gid, description="d" * 120, paid_by=m["Asha"],
               splits=[{"member_id": m["Asha"]}]).status_code == 201


def test_c4_unknown_group_404(client):
    r = add(client, 4242, paid_by=1, splits=[{"member_id": 1}])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "GROUP_NOT_FOUND"


def test_c3_detail_contains_expense(client, make_group):
    gid, m = make_group()
    add(client, gid, paid_by=m["Asha"], splits=[{"member_id": m["Bilal"]}])
    detail = client.get(f"/api/groups/{gid}").json()
    assert len(detail["expenses"]) == 1
    e = detail["expenses"][0]
    assert e["description"] == "Groceries" and e["amount"] == 100000 and e["date"] == "2026-11-20"
    assert e["split_mode"] == "EQUAL" and e["paid_by"] == m["Asha"]
