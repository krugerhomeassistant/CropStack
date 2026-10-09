from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import external
from app.db import get_engine
from app.main import app
from app.models import ClimateArchive
from app.routers import auth
from tests.test_climate import synthetic

GARDEN = {"name": "Back yard", "latitude": -33.92, "longitude": 18.42, "postal_code": "8001", "frost_probability": 30}


@pytest.fixture
def client(monkeypatch):
    # Tests share one DB, so keep registration open regardless of how many accounts exist.
    monkeypatch.setattr(auth, "registration_open", lambda db: True)
    auth.FAILS.clear()
    with TestClient(app) as c:
        yield c


def register(client: TestClient, username: str) -> None:
    resp = client.post("/api/v1/auth/register", json={"username": username, "password": "correct horse"})
    assert resp.status_code == 200, resp.text


def test_register_login_logout_flow(client):
    register(client, "Alice")
    me = client.get("/api/v1/auth/me").json()
    assert me["username"] == "alice"
    assert "password_hash" not in me

    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": "ALICE", "password": "wrong pass"}).status_code == 401
    assert client.post("/api/v1/auth/login", json={"username": "alice", "password": "correct horse"}).status_code == 200


def test_duplicate_username_rejected(client):
    register(client, "bob")
    resp = client.post("/api/v1/auth/register", json={"username": "BOB", "password": "another one"})
    assert resp.status_code == 409


def test_login_throttled_after_repeated_failures(client):
    for _ in range(auth.MAX_FAILS):
        client.post("/api/v1/auth/login", json={"username": "nobody", "password": "wrong pass"})
    assert client.post("/api/v1/auth/login", json={"username": "nobody", "password": "wrong pass"}).status_code == 429


def test_password_change(client):
    register(client, "carol")
    bad = client.post("/api/v1/auth/password", json={"current": "nope", "new": "brand new pw"})
    assert bad.status_code == 400
    assert (
        client.post("/api/v1/auth/password", json={"current": "correct horse", "new": "brand new pw"}).status_code
        == 200
    )
    client.post("/api/v1/auth/logout")
    assert client.post("/api/v1/auth/login", json={"username": "carol", "password": "brand new pw"}).status_code == 200


def test_registration_auto_closes_after_first_account():
    with TestClient(app) as c:
        c.post("/api/v1/auth/register", json={"username": "first", "password": "first pass"})
        assert c.get("/api/v1/auth/status").json()["registration_open"] is False
        assert c.post("/api/v1/auth/register", json={"username": "late", "password": "late pass"}).status_code == 403


def test_garden_requires_login(client):
    assert client.get("/api/v1/sites/current").status_code == 401


def test_garden_create_update_and_isolation(client):
    register(client, "dave")
    assert client.get("/api/v1/sites/current").status_code == 404

    created = client.put("/api/v1/sites/current", json=GARDEN).json()
    assert created["name"] == "Back yard" and created["frost_probability"] == 30
    updated = client.put("/api/v1/sites/current", json=GARDEN | {"name": "Allotment"}).json()
    assert updated["id"] == created["id"] and updated["name"] == "Allotment"

    client.post("/api/v1/auth/logout")
    register(client, "erin")
    assert client.get("/api/v1/sites/current").status_code == 404  # another user's garden is never visible


@pytest.mark.parametrize(
    "bad", [{"latitude": 91}, {"longitude": -181}, {"frost_probability": 5}, {"name": ""}, {"latitude": None}]
)
def test_garden_validation(client, bad):
    register(client, f"val{abs(hash(str(bad))) % 10_000}")
    assert client.put("/api/v1/sites/current", json=GARDEN | bad).status_code == 422


def test_climate_is_fetched_once_per_location(client, monkeypatch):
    calls = []

    def fake_fetch(lat, lon):
        calls.append((lat, lon))
        return synthetic(mean=5, amplitude=10, coldest=date(2001, 7, 15))

    monkeypatch.setattr(external, "fetch_climate_archive", fake_fetch)
    register(client, "fiona")
    assert client.get("/api/v1/sites/current/climate").status_code == 404  # no garden yet

    client.put("/api/v1/sites/current", json=GARDEN)
    first = client.get("/api/v1/sites/current/climate").json()
    assert first["zone"] and first["source"].startswith("Open-Meteo")
    client.put("/api/v1/sites/current", json=GARDEN | {"frost_probability": 10})
    cautious = client.get("/api/v1/sites/current/climate").json()
    assert len(calls) == 1  # risk change is computed from the cache
    assert cautious["frost_probability"] == 10

    client.put("/api/v1/sites/current", json=GARDEN | {"latitude": -26.2})
    client.get("/api/v1/sites/current/climate")
    assert calls == [(GARDEN["latitude"], GARDEN["longitude"]), (-26.2, GARDEN["longitude"])]

    # The record is refetched when its format changes or a newer complete year exists...
    with Session(get_engine()) as db:
        archive = db.exec(select(ClimateArchive)).all()[-1]
        archive.version = 0
        db.add(archive)
        db.commit()
    assert "rain_season" in client.get("/api/v1/sites/current/climate").json()
    assert len(calls) == 3
    with Session(get_engine()) as db:
        archive = db.exec(select(ClimateArchive)).all()[-1]
        archive.last_year -= 1
        db.add(archive)
        db.commit()

    # ...but if that refresh fails, the existing record for the same place keeps answering.
    def failing(lat, lon):
        raise external.ExternalError("archive-api.open-meteo.com answered 429: Daily API request limit exceeded")

    monkeypatch.setattr(external, "fetch_climate_archive", failing)
    assert client.get("/api/v1/sites/current/climate").status_code == 200


def test_climate_service_failure_is_reported(client, monkeypatch):
    def failing(lat, lon):
        raise external.ExternalError("archive-api.open-meteo.com answered 429: Daily API request limit exceeded")

    monkeypatch.setattr(external, "fetch_climate_archive", failing)
    register(client, "gina")
    client.put("/api/v1/sites/current", json=GARDEN)
    resp = client.get("/api/v1/sites/current/climate")
    assert resp.status_code == 502 and "limit exceeded" in resp.json()["detail"]


def test_place_search(client, monkeypatch):
    monkeypatch.setattr(external, "search_places", lambda q: [{"label": q, "latitude": 1.0, "longitude": 2.0}])
    assert client.get("/api/v1/places", params={"q": "0081"}).status_code == 401
    register(client, "hank")
    assert client.get("/api/v1/places", params={"q": "0081"}).json()[0]["label"] == "0081"
    assert client.get("/api/v1/places", params={"q": "x"}).status_code == 422


def test_personal_prefs(client):
    register(client, "ivy")
    assert client.get("/api/v1/auth/me").json()["prefs"] == {"start": "today", "units": "metric"}
    assert client.put("/api/v1/auth/prefs", json={"start": "climate", "units": "imperial"}).status_code == 200
    assert client.get("/api/v1/auth/me").json()["prefs"] == {"start": "climate", "units": "imperial"}
    assert client.put("/api/v1/auth/prefs", json={"start": "nowhere"}).status_code == 422


def test_climate_probability_and_bands(client, monkeypatch):
    monkeypatch.setattr(
        external, "fetch_climate_archive", lambda lat, lon: synthetic(mean=5, amplitude=10, coldest=date(2001, 7, 15))
    )
    register(client, "jill")
    client.put("/api/v1/sites/current", json=GARDEN)
    frost = client.get("/api/v1/sites/current/climate/probability", params={"var": "tmin", "op": "le", "x": 0}).json()
    assert len(frost["days"]) == 365
    assert frost["days"][195] > 0.9 and frost["days"][14] == 0  # mid-July frosty, mid-January not
    bands = client.get("/api/v1/sites/current/climate/bands", params={"var": "tmax"}).json()
    assert all(lo <= mid <= hi for lo, mid, hi in zip(bands["p10"], bands["p50"], bands["p90"], strict=True))
    assert client.get("/api/v1/sites/current/climate/bands", params={"var": "nonsense"}).status_code == 422
