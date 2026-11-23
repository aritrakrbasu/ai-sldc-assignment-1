"""T030 [US3], T034 [US4], T037 [US5], T040 [US6] — contracts C5, C6, C8, C9."""

import pytest


def equal_all(client, gid, m, amount=100000, payer="Asha", desc="Groceries", date="2026-11-20"):
    r = client.post(f"/api/groups/{gid}/expenses", json={
        "description": desc, "amount": amount, "paid_by": m[payer], "date": date,
        "split_mode": "EQUAL", "splits": [{"member_id": v} for v in m.values()]})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def settle(client, gid, frm, to, amount, date="2026-11-21"):
    return client.post(f"/api/groups/{gid}/settlements",
                       json={"from_member": frm, "to_member": to, "amount": amount, "date": date})


def bal(client, gid):
    return {b["name"]: b["balance"] for b in client.get(f"/api/groups/{gid}/balances").json()}


# ---- C8 settle-up (US3) ----
def test_us3_1_c8_plan(client, make_group):
    gid, m = make_group()
    equal_all(client, gid, m)
    r = client.get(f"/api/groups/{gid}/settle-up")
    assert r.status_code == 200
    assert r.json() == [
        {"from_member": m["Bilal"], "to_member": m["Asha"], "amount": 33333},
        {"from_member": m["Chen"], "to_member": m["Asha"], "amount": 33333},
    ]


def test_us3_3_c8_empty(client, make_group):
    gid, _ = make_group()
    assert client.get(f"/api/groups/{gid}/settle-up").json() == []


def test_c8_unknown_group(client):
    assert client.get("/api/groups/77/settle-up").status_code == 404


# ---- C6 settlements (US4) ----
def test_us4_1_c6_record_settlement(client, make_group):
    gid, m = make_group()
    equal_all(client, gid, m)
    r = settle(client, gid, m["Bilal"], m["Asha"], 33333)
    assert r.status_code == 201
    assert r.json()["amount"] == 33333
    assert bal(client, gid) == {"Asha": 33333, "Bilal": 0, "Chen": -33333}


def test_us4_4_c6_overpayment_flips(client, make_group):
    gid, m = make_group(names=("A", "B"))
    client.post(f"/api/groups/{gid}/expenses", json={
        "description": "x", "amount": 33333, "paid_by": m["A"], "date": "2026-11-20",
        "split_mode": "EQUAL", "splits": [{"member_id": m["B"]}]})
    assert settle(client, gid, m["B"], m["A"], 50000).status_code == 201
    assert bal(client, gid) == {"A": -16667, "B": 16667}


def test_us4_2_c6_same_member(client, make_group):
    gid, m = make_group()
    r = settle(client, gid, m["Asha"], m["Asha"], 100)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "SAME_MEMBER"


@pytest.mark.parametrize("amount", [0, -100, 1.5])
def test_us4_3_c6_invalid_amount_422(client, make_group, amount):
    gid, m = make_group()
    r = settle(client, gid, m["Bilal"], m["Asha"], amount)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_c6_unknown_member(client, make_group):
    gid, m = make_group()
    r = settle(client, gid, 9999, m["Asha"], 100)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "UNKNOWN_MEMBER"


def test_us4_5_c6_settlement_cannot_be_deleted(client, make_group):
    gid, m = make_group()
    sid = settle(client, gid, m["Bilal"], m["Asha"], 100).json()["id"]
    r = client.delete(f"/api/groups/{gid}/settlements/{sid}")
    assert r.status_code == 405
    assert len(client.get(f"/api/groups/{gid}").json()["settlements"]) == 1


def test_us4_5_reverse_settlement_undoes(client, make_group):
    gid, m = make_group()
    settle(client, gid, m["Bilal"], m["Asha"], 500)
    settle(client, gid, m["Asha"], m["Bilal"], 500)
    assert bal(client, gid) == {"Asha": 0, "Bilal": 0, "Chen": 0}


# ---- C5 delete expense (US5) ----
def test_us5_1_c5_delete_restores_balances(client, make_group):
    gid, m = make_group()
    equal_all(client, gid, m, amount=3000, payer="Chen")
    before = bal(client, gid)
    eid = equal_all(client, gid, m)
    assert bal(client, gid) != before
    r = client.delete(f"/api/groups/{gid}/expenses/{eid}")
    assert r.status_code == 204
    assert bal(client, gid) == before
    assert eid not in [e["id"] for e in client.get(f"/api/groups/{gid}").json()["expenses"]]


def test_us5_2_c5_unknown_expense(client, make_group):
    gid, _ = make_group()
    r = client.delete(f"/api/groups/{gid}/expenses/12345")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "EXPENSE_NOT_FOUND"


def test_c5_expense_of_other_group_not_found(client, make_group):
    gid, m = make_group()
    gid2, _ = make_group(name="Other", names=("X", "Y"))
    eid = equal_all(client, gid, m)
    r = client.delete(f"/api/groups/{gid2}/expenses/{eid}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "EXPENSE_NOT_FOUND"


# ---- C9 export (US6) ----
def test_us6_1_c9_csv_export(client, make_group):
    gid, m = make_group()
    equal_all(client, gid, m, desc="=SUM(A1)")
    settle(client, gid, m["Bilal"], m["Asha"], 33333)
    r = client.get(f"/api/groups/{gid}/export.csv")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/csv")
    assert "attachment" in r.headers["content-disposition"]
    assert r.text == (
        "date,type,description,paid_by,amount_inr,split_mode,participants\r\n"
        "2026-11-20,expense,'=SUM(A1),Asha,1000.00,EQUAL,Asha:333.34;Bilal:333.33;Chen:333.33\r\n"
        "2026-11-21,settlement,Settlement to Asha,Bilal,333.33,,Asha\r\n"
    )


def test_sc006_c9_export_byte_identical_for_identical_operations(client, make_group):
    outs = []
    for name in ("Run1", "Run2"):
        gid, m = make_group(name=name)
        equal_all(client, gid, m)
        settle(client, gid, m["Chen"], m["Asha"], 100)
        outs.append(client.get(f"/api/groups/{gid}/export.csv").content)
    assert outs[0] == outs[1]
