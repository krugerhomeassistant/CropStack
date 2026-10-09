from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import get_engine
from app.main import app
from app.models import Invite
from app.routers import auth
from tests.test_auth_garden import GARDEN


@pytest.fixture
def owner(monkeypatch):
    monkeypatch.setattr(auth, "registration_open", lambda db: True)
    auth.FAILS.clear()
    with TestClient(app) as c:
        resp = c.post(
            "/api/v1/auth/register", json={"username": f"own{id(c)}", "password": "owner pass", "display_name": "Jan"}
        )
        assert resp.status_code == 200
        yield c


def join(token: str, username: str, monkeypatch) -> TestClient:
    monkeypatch.setattr(auth, "registration_open", lambda db: False)  # invites work even when sign-up is closed
    client = TestClient(app)
    resp = client.post("/api/v1/auth/register", json={"username": username, "password": "joiner pass", "invite": token})
    assert resp.status_code == 200, resp.text
    return client


def test_new_account_owns_a_new_household(owner):
    me = owner.get("/api/v1/auth/me").json()
    assert me["role"] == "owner"
    assert me["household"]["name"] == "Jan's homestead"
    household = owner.get("/api/v1/household").json()
    assert household["my_role"] == "owner" and len(household["members"]) == 1


def test_invited_member_shares_the_garden_but_cannot_move_it(owner, monkeypatch):
    owner.put("/api/v1/sites/current", json=GARDEN)
    invite = owner.post("/api/v1/household/invites", json={"role": "member"}).json()
    assert invite["path"] == f"/invite/{invite['token']}"

    public = TestClient(app).get(f"/api/v1/invites/{invite['token']}").json()
    assert public == {"household": "Jan's homestead", "role": "member", "expires_at": public["expires_at"]}

    wife = join(invite["token"], f"wife{id(owner)}", monkeypatch)
    me = wife.get("/api/v1/auth/me").json()
    assert me["role"] == "member" and me["household"]["name"] == "Jan's homestead"
    assert wife.get("/api/v1/sites/current").json()["name"] == GARDEN["name"]
    assert wife.put("/api/v1/sites/current", json=GARDEN).status_code == 403
    assert wife.post("/api/v1/household/invites", json={"role": "member"}).status_code == 403
    assert len(owner.get("/api/v1/household").json()["members"]) == 2


def test_invite_is_single_use_and_stored_hashed(owner, monkeypatch):
    token = owner.post("/api/v1/household/invites", json={"role": "viewer"}).json()["token"]
    with Session(get_engine()) as db:
        assert db.get(Invite, token) is None  # only the hash is stored
    join(token, f"once{id(owner)}", monkeypatch)
    again = TestClient(app).post(
        "/api/v1/auth/register", json={"username": f"twice{id(owner)}", "password": "joiner pass", "invite": token}
    )
    assert again.status_code == 410
    assert TestClient(app).get(f"/api/v1/invites/{token}").status_code == 404


def test_expired_and_revoked_invites_are_refused(owner):
    first = owner.post("/api/v1/household/invites", json={}).json()
    with Session(get_engine()) as db:
        invite = db.get(Invite, first["id"])
        invite.expires_at = invite.created_at - timedelta(minutes=1)
        db.add(invite)
        db.commit()
    assert TestClient(app).get(f"/api/v1/invites/{first['token']}").status_code == 404

    second = owner.post("/api/v1/household/invites", json={}).json()
    assert [i["id"] for i in owner.get("/api/v1/household/invites").json()] == [second["id"]]
    assert owner.delete(f"/api/v1/household/invites/{second['id']}").status_code == 200
    assert TestClient(app).get(f"/api/v1/invites/{second['token']}").status_code == 404


def test_roles_and_removal(owner, monkeypatch):
    token = owner.post("/api/v1/household/invites", json={"role": "viewer"}).json()["token"]
    viewer = join(token, f"view{id(owner)}", monkeypatch)
    viewer_id = viewer.get("/api/v1/auth/me").json()["id"]
    owner_id = owner.get("/api/v1/auth/me").json()["id"]

    assert owner.put(f"/api/v1/household/members/{owner_id}", json={"role": "member"}).status_code == 409  # last owner
    assert owner.put(f"/api/v1/household/members/{viewer_id}", json={"role": "owner"}).json()["role"] == "owner"
    assert (
        owner.put(f"/api/v1/household/members/{owner_id}", json={"role": "member"}).status_code == 200
    )  # 2 owners now
    assert viewer.put("/api/v1/household", json={"name": "Kruger plot"}).status_code == 200

    assert viewer.delete(f"/api/v1/household/members/{viewer_id}").status_code == 409  # not yourself
    assert viewer.delete(f"/api/v1/household/members/{owner_id}").status_code == 200
    assert owner.get("/api/v1/auth/me").status_code == 401  # their login is gone


def test_members_of_other_households_are_invisible(owner, monkeypatch):
    monkeypatch.setattr(auth, "registration_open", lambda db: True)
    other = TestClient(app)
    other.post("/api/v1/auth/register", json={"username": f"other{id(owner)}", "password": "other pass"})
    other_id = other.get("/api/v1/auth/me").json()["id"]
    assert owner.put(f"/api/v1/household/members/{other_id}", json={"role": "viewer"}).status_code == 404
    assert owner.delete(f"/api/v1/household/members/{other_id}").status_code == 404
