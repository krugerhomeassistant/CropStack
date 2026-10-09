from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import environment as env
from app import external, scheduler, weather
from app.db import get_engine
from app.main import app
from app.models import Forecast, now
from app.routers import auth
from app.routers import weather as weather_router
from tests.test_auth_garden import GARDEN
from tests.test_climate import synthetic
from tests.test_environment import make


def forecast_raw(today: date, tmin=12.0, tmax=24.0, precip=1.0) -> dict:
    days = [today - timedelta(days=92) + timedelta(days=i) for i in range(92 + 16)]
    n = len(days)
    return {
        "timezone": "Africa/Johannesburg",
        "utc_offset_seconds": 0,
        "daily": {
            "time": [d.isoformat() for d in days],
            "temperature_2m_min": [tmin] * n,
            "temperature_2m_max": [tmax] * n,
            "precipitation_sum": [precip] * n,
            "precipitation_probability_max": [30] * n,
            "et0_fao_evapotranspiration": [4.0] * n,
            "relative_humidity_2m_mean": [65.0] * n,
            "wind_speed_10m_max": [12.0] * n,
            "soil_temperature_0_to_7cm_mean": [18.0] * n,
            "weather_code": [2] * n,
        },
    }


# ---------------------------------------------------------------- pure functions


def test_forecast_is_written_into_every_year_and_wraps_into_the_next():
    c = make(tmin_of=lambda d: 5.0)
    f = env.with_forecast(c, date(2026, 12, 30), {"tmin": [-4.0, -3.0, -2.0], "unknown": [1.0]})
    assert all(year[363] == -4.0 and year[364] == -3.0 for year in f.series["tmin"])  # 30-31 Dec, every year
    assert f.series["tmin"][1][0] == -2.0  # 1 Jan continues in the following year's slots
    assert c.series["tmin"][0][363] == 5.0  # the original is untouched
    assert env.prob_any(f, "tmin", "le", 0, 364, 2) == pytest.approx(1.0)


def test_recent_weather_against_normal():
    c = make(tmin_of=lambda d: 10.0, tmax_of=lambda d: 20.0, precip_of=lambda d: 1.0)
    today = date(2026, 3, 1)
    past = [
        {"date": (today - timedelta(days=k)).isoformat(), "tmin": 12.0, "tmax": 22.0, "precip": 3.0}
        for k in range(1, 31)
    ]
    a = weather.anomaly(c, past, today)
    assert a["temp_diff_c"] == 2.0
    assert a["rain_mm"] == 90 and a["rain_normal_mm"] == 30 and a["rain_percentile"] == 100
    assert weather.anomaly(c, past[:10], today) is None  # too few observed days


def test_daily_rows_and_split():
    rows = weather.daily_rows(forecast_raw(date(2026, 5, 10)))
    past, future = weather.split(rows, date(2026, 5, 10))
    assert len(past) == 92 and len(future) == 16
    assert future[0]["date"] == "2026-05-10" and future[0]["precip_prob"] == 30 and future[0]["soil_t"] == 18.0


def test_scheduler_runs_due_jobs_and_survives_failures(monkeypatch):
    monkeypatch.setattr(scheduler, "JOBS", {})
    ran = []

    @scheduler.job("ok", every=timedelta(minutes=30))
    def ok():
        ran.append("ok")

    @scheduler.job("boom", every=timedelta(minutes=30))
    def boom():
        raise RuntimeError("no network")

    start = datetime(2026, 1, 1, tzinfo=UTC)
    assert scheduler.run_due(start) == []  # first run waits for start-up
    assert scheduler.run_due(start + scheduler.FIRST_RUN_DELAY) == ["ok", "boom"]
    assert scheduler.status()["boom"]["last_error"] == "RuntimeError: no network"
    assert scheduler.run_due(start + scheduler.FIRST_RUN_DELAY + timedelta(minutes=10)) == []  # not due yet
    assert ran == ["ok"]


# ---------------------------------------------------------------- API


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(auth, "registration_open", lambda db: True)
    monkeypatch.setattr(external, "fetch_climate_archive", lambda lat, lon: synthetic(5, 10, date(2001, 7, 15)))
    auth.FAILS.clear()
    with TestClient(app) as c:
        yield c


def owner_with_garden(client: TestClient, name: str) -> None:
    client.post("/api/v1/auth/register", json={"username": name, "password": "weather pass"})
    client.put("/api/v1/sites/current", json=GARDEN)


def test_weather_today_next_days_and_recent(client, monkeypatch):
    calls = []
    today = datetime.now(UTC).date()
    monkeypatch.setattr(external, "fetch_forecast", lambda lat, lon: calls.append(1) or forecast_raw(today))
    owner_with_garden(client, "sunny")
    w = client.get("/api/v1/sites/current/weather").json()
    assert w["today"]["date"] == today.isoformat() and len(w["days"]) == 16
    assert w["recent"]["days"] == 30 and not w["stale"]
    client.get("/api/v1/sites/current/weather")
    assert len(calls) == 1  # fresh for 3 hours


def test_old_forecast_is_refreshed_and_kept_if_refresh_fails(client, monkeypatch):
    today = datetime.now(UTC).date()
    monkeypatch.setattr(external, "fetch_forecast", lambda lat, lon: forecast_raw(today))
    owner_with_garden(client, "cloudy")
    client.get("/api/v1/sites/current/weather")
    site_id = client.get("/api/v1/sites/current").json()["id"]
    with Session(get_engine()) as db:
        fc = db.get(Forecast, site_id)
        fc.fetched_at = now() - timedelta(hours=4)
        db.add(fc)
        db.commit()

    def down(lat, lon):
        raise external.ExternalError("api.open-meteo.com answered 503: busy")

    monkeypatch.setattr(external, "fetch_forecast", down)
    w = client.get("/api/v1/sites/current/weather").json()
    assert w["stale"] is True and w["today"] is not None


def test_switching_sources_off(client, monkeypatch):
    monkeypatch.setattr(external, "fetch_forecast", lambda lat, lon: forecast_raw(date.today()))
    monkeypatch.setattr(external, "search_places", lambda q: [])
    owner_with_garden(client, "private")
    sources = {s["id"]: s for s in client.get("/api/v1/household/data-sources").json()}
    assert sources["forecast"]["enabled"] and sources["climate"]["switch"] is None

    assert client.put("/api/v1/household/settings", json={"forecast": False, "place_search": False}).status_code == 200
    assert client.get("/api/v1/sites/current/weather").status_code == 409
    assert client.get("/api/v1/places", params={"q": "Paarl"}).status_code == 409
    weather_router.refresh_all()  # the background job skips this household too (other test households may refresh)
    site_id = client.get("/api/v1/sites/current").json()["id"]
    with Session(get_engine()) as db:
        assert db.get(Forecast, site_id) is None
    assert client.get("/api/v1/household/data-sources").json()[1]["enabled"] is False


def test_only_owners_change_household_settings(client, monkeypatch):
    owner_with_garden(client, "boss")
    token = client.post("/api/v1/household/invites", json={"role": "member"}).json()["token"]
    member = TestClient(app)
    monkeypatch.setattr(auth, "registration_open", lambda db: False)
    member.post("/api/v1/auth/register", json={"username": "boss-member", "password": "member pass", "invite": token})
    assert member.get("/api/v1/household/settings").json() == {"forecast": True, "place_search": True}
    assert member.put("/api/v1/household/settings", json={"forecast": False}).status_code == 403
