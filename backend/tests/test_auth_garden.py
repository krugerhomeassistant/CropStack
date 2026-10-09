import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import auth

GARDEN = {"name": "Back yard", "latitude": -33.92, "longitude": 18.42, "postal_code": "8001", "frost_probability": 30}


@pytest.fixture
def client(monkeypatch):
    # Tests share one DB, so keep registration open regardless of how many accounts exist.
    monkeypatch.setattr(auth, "registration_open", lambda db: True)
    auth.FAILS.clear()
    with TestClient(app) as c:
        yield c


def register(client: TestClient, username: str) -> None:
    resp = client.post("/api/auth/register", json={"username": username, "password": "correct horse"})
    assert resp.status_code == 200, resp.text


def test_register_login_logout_flow(client):
    register(client, "Alice")
    me = client.get("/api/auth/me").json()
    assert me["username"] == "alice"
    assert "password_hash" not in me

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/login", json={"username": "ALICE", "password": "wrong pass"}).status_code == 401
    assert client.post("/api/auth/login", json={"username": "alice", "password": "correct horse"}).status_code == 200


def test_duplicate_username_rejected(client):
    register(client, "bob")
    resp = client.post("/api/auth/register", json={"username": "BOB", "password": "another one"})
    assert resp.status_code == 409


def test_login_throttled_after_repeated_failures(client):
    for _ in range(auth.MAX_FAILS):
        client.post("/api/auth/login", json={"username": "nobody", "password": "wrong pass"})
    assert client.post("/api/auth/login", json={"username": "nobody", "password": "wrong pass"}).status_code == 429


def test_password_change(client):
    register(client, "carol")
    bad = client.post("/api/auth/password", json={"current": "nope", "new": "brand new pw"})
    assert bad.status_code == 400
    assert (
        client.post("/api/auth/password", json={"current": "correct horse", "new": "brand new pw"}).status_code == 200
    )
    client.post("/api/auth/logout")
    assert client.post("/api/auth/login", json={"username": "carol", "password": "brand new pw"}).status_code == 200


def test_registration_auto_closes_after_first_account():
    with TestClient(app) as c:
        c.post("/api/auth/register", json={"username": "first", "password": "first pass"})
        assert c.get("/api/auth/status").json()["registration_open"] is False
        assert c.post("/api/auth/register", json={"username": "late", "password": "late pass"}).status_code == 403


def test_garden_requires_login(client):
    assert client.get("/api/garden").status_code == 401


def test_garden_create_update_and_isolation(client):
    register(client, "dave")
    assert client.get("/api/garden").status_code == 404

    created = client.put("/api/garden", json=GARDEN).json()
    assert created["name"] == "Back yard" and created["frost_probability"] == 30
    updated = client.put("/api/garden", json=GARDEN | {"name": "Allotment"}).json()
    assert updated["id"] == created["id"] and updated["name"] == "Allotment"

    client.post("/api/auth/logout")
    register(client, "erin")
    assert client.get("/api/garden").status_code == 404  # another user's garden is never visible


@pytest.mark.parametrize(
    "bad", [{"latitude": 91}, {"longitude": -181}, {"frost_probability": 5}, {"name": ""}, {"latitude": None}]
)
def test_garden_validation(client, bad):
    register(client, f"val{abs(hash(str(bad))) % 10_000}")
    assert client.put("/api/garden", json=GARDEN | bad).status_code == 422
