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


def test_climate_is_fetched_once_per_location(client, monkeypatch):
    from app import external
    from tests.test_climate import synthetic

    calls = []

    def fake_fetch(lat, lon):
        calls.append((lat, lon))
        return synthetic(mean=5, amplitude=10, coldest=__import__("datetime").date(2001, 7, 15))

    monkeypatch.setattr(external, "fetch_climate_archive", fake_fetch)
    register(client, "fiona")
    assert client.get("/api/garden/climate").status_code == 404  # no garden yet

    client.put("/api/garden", json=GARDEN)
    first = client.get("/api/garden/climate").json()
    assert first["zone"] and first["source"].startswith("Open-Meteo")
    client.put("/api/garden", json=GARDEN | {"frost_probability": 10})
    cautious = client.get("/api/garden/climate").json()
    assert len(calls) == 1  # risk change is computed from the cache
    assert cautious["frost_probability"] == 10

    client.put("/api/garden", json=GARDEN | {"latitude": -26.2})
    client.get("/api/garden/climate")
    assert calls == [(GARDEN["latitude"], GARDEN["longitude"]), (-26.2, GARDEN["longitude"])]


def test_climate_service_failure_is_reported(client, monkeypatch):
    from app import external

    def failing(lat, lon):
        raise external.ExternalError("archive-api.open-meteo.com answered 429: Daily API request limit exceeded")

    monkeypatch.setattr(external, "fetch_climate_archive", failing)
    register(client, "gina")
    client.put("/api/garden", json=GARDEN)
    resp = client.get("/api/garden/climate")
    assert resp.status_code == 502 and "limit exceeded" in resp.json()["detail"]


def test_place_search(client, monkeypatch):
    from app import external

    monkeypatch.setattr(external, "search_places", lambda q: [{"label": q, "latitude": 1.0, "longitude": 2.0}])
    assert client.get("/api/places", params={"q": "0081"}).status_code == 401
    register(client, "hank")
    assert client.get("/api/places", params={"q": "0081"}).json()[0]["label"] == "0081"
    assert client.get("/api/places", params={"q": "x"}).status_code == 422
