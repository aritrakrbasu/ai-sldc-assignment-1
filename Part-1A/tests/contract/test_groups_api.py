"""T016 [US1] — contract C1, C2, C3. FR-001, FR-002, FR-018, FR-019."""

from fastapi.testclient import TestClient

from splitease.api.app import create_app


def test_us1_1_c1_create_group(client):
    r = client.post("/api/groups", json={"name": "Flat 4B", "members": ["Asha", "Bilal", "Chen"]})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Flat 4B"
    assert [m["name"] for m in body["members"]] == ["Asha", "Bilal", "Chen"]
    assert [m["position"] for m in body["members"]] == [0, 1, 2]
    assert all(isinstance(m["id"], int) for m in body["members"])


def test_us1_1_c3_new_group_balances_zero(client, make_group):
    gid, ids = make_group()
    r = client.get(f"/api/groups/{gid}")
    assert r.status_code == 200
    body = r.json()
    assert [b["balance"] for b in body["balances"]] == [0, 0, 0]
    assert body["expenses"] == [] and body["settlements"] == [] and body["settle_up"] == []


def test_c2_list_groups_ordered_by_id(client, make_group):
    g1, _ = make_group(name="One")
    g2, _ = make_group(name="Two", names=("X", "Y"))
    r = client.get("/api/groups")
    assert r.status_code == 200
    assert r.json() == [{"id": g1, "name": "One", "member_count": 3},
                        {"id": g2, "name": "Two", "member_count": 2}]


def test_c3_unknown_group_404(client):
    r = client.get("/api/groups/999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "GROUP_NOT_FOUND"


def test_fr001_c1_duplicate_members_400(client):
    r = client.post("/api/groups", json={"name": "G", "members": ["Asha", " asha "]})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_MEMBERS"


def test_fr001_c1_single_member_400(client):
    r = client.post("/api/groups", json={"name": "G", "members": ["Asha"]})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_MEMBERS"


def test_fr018_c1_bad_body_422(client):
    r = client.post("/api/groups", json={"name": "G"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert client.get("/api/groups").json() == []


def test_c1_invalid_group_name_400(client):
    r = client.post("/api/groups", json={"name": "   ", "members": ["A", "B"]})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "INVALID_GROUP_NAME"


def test_fr019_data_persists_across_restart(tmp_path):
    db = str(tmp_path / "persist.sqlite3")
    with TestClient(create_app(db_path=db)) as c1:
        gid = c1.post("/api/groups", json={"name": "Trip", "members": ["A", "B"]}).json()["id"]
    with TestClient(create_app(db_path=db)) as c2:
        assert c2.get(f"/api/groups/{gid}").json()["name"] == "Trip"
