from datetime import UTC, date, datetime, timedelta

from app.models import Planting
from app.tasks import crop_schedule
from tests.test_household import owner  # noqa: F401  (fixture)


def planting(**kw) -> Planting:
    base = {
        "id": 1,
        "household_id": 1,
        "crop": "tomato",
        "method": "direct",
        "status": "planned",
        "start_date": date(2026, 10, 1),
        "quantity": 6,
        "location": "Bed 1",
    }
    return Planting(**(base | kw))


def kinds(specs) -> dict[str, bool]:
    return {s.kind: s.done for s in specs}


def test_schedule_for_direct_sowing_and_transplants():
    maturity = {"p10": 80, "p50": 95, "p90": 115}
    specs = crop_schedule(planting(), "tomato", maturity, None)
    assert kinds(specs) == {"sow": False, "harvest": False}
    harvest = specs[-1]
    assert (harvest.earliest, harvest.ideal, harvest.latest) == (
        date(2026, 12, 20),
        date(2027, 1, 4),
        date(2027, 1, 24),
    )
    assert "95 days" in harvest.reason and "Bed 1" in harvest.title

    moved = planting(method="transplant", set_out_date=date(2026, 11, 12), status="germinated")
    assert kinds(crop_schedule(moved, "tomato", maturity, None)) == {"sow": True, "set_out": False, "harvest": False}
    assert kinds(crop_schedule(planting(status="finished"), "tomato", maturity, None)) == {"sow": True, "harvest": True}
    assert crop_schedule(planting(status="failed"), "tomato", maturity, None) == []


def test_schedule_without_climate_uses_catalogued_cycle():
    specs = crop_schedule(planting(), "tomato", None, (70, 100))
    assert specs[-1].ideal == date(2026, 10, 1) + timedelta(days=85)
    assert [s.kind for s in crop_schedule(planting(), "tomato", None, None)] == ["sow"]  # nothing to estimate from


def test_today_lists_jobs_and_completing_moves_the_planting(owner):  # noqa: F811
    today = datetime.now(UTC).date()
    made = owner.post("/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": str(today)})
    assert made.status_code == 201
    groups = owner.get("/api/v1/today").json()["groups"]
    assert [g["group"] for g in groups] == ["Plant"]  # harvest is months away
    job = groups[0]["tasks"][0]
    assert job["kind"] == "sow" and "test crop (1)" in job["title"].lower() and not job["overdue"]

    assert owner.patch(f"/api/v1/tasks/{job['id']}", json={"status": "done"}).status_code == 200
    assert owner.patch(f"/api/v1/tasks/{job['id']}", json={"status": "done"}).status_code == 409
    assert owner.get("/api/v1/plantings").json()[0]["status"] == "sown"
    assert owner.get("/api/v1/today").json()["groups"] == []
    soon = owner.get("/api/v1/today").json()["upcoming"]
    assert soon == []  # the harvest is more than two weeks out

    # failing the planting removes its remaining jobs; deleting it removes them for good
    pid = made.json()["id"]
    owner.patch(f"/api/v1/plantings/{pid}", json={"status": "failed"})
    owner.delete(f"/api/v1/plantings/{pid}")
    assert owner.get("/api/v1/today").json()["groups"] == []


def test_overdue_jobs_stay_on_today(owner):  # noqa: F811
    week_ago = datetime.now(UTC).date() - timedelta(days=30)
    owner.post("/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": str(week_ago)})
    job = owner.get("/api/v1/today").json()["groups"][0]["tasks"][0]
    assert job["overdue"]


def forecast(*lows_highs: tuple[float, float]) -> list[dict]:
    return [
        {"date": str(date(2026, 10, 9) + timedelta(days=i)), "tmin": lo, "tmax": hi}
        for i, (lo, hi) in enumerate(lows_highs)
    ]


def test_frost_and_heat_alerts_use_the_crops_own_limits():
    from app.tasks import weather_alerts

    out = planting(status="germinated")
    mild = forecast((8, 20), (7, 21), (-1, 18), (9, 40))
    specs = {s.kind: s for s in weather_alerts(out, "tomato", 0.0, 35.0, mild)}
    assert specs["frost"].ideal == date(2026, 10, 10) and specs["frost"].latest == date(2026, 10, 11)
    assert "-1 °C" in specs["frost"].reason and specs["frost"].group == "Protect"
    assert specs["heat"].latest == date(2026, 10, 12)
    # a hardier crop with the same forecast needs no frost cover; unknown limits raise no alert
    assert [s.kind for s in weather_alerts(out, "kale", -9.0, None, mild)] == []
    assert weather_alerts(out, "x", None, None, mild) == []
    # not yet sown, or still indoors as a seedling: nothing to protect
    assert weather_alerts(planting(), "tomato", 0.0, 35.0, mild) == []
    seedling = planting(method="transplant", set_out_date=date(2026, 11, 1), status="sown")
    assert weather_alerts(seedling, "tomato", 0.0, 35.0, mild) == []
    # beyond the 7-day horizon is ignored
    assert weather_alerts(out, "tomato", 0.0, None, forecast(*[(8, 20)] * 7, (-3, 10))) == []


def test_engine_skipped_alert_reopens_but_a_persons_skip_stays(owner):  # noqa: F811
    from dataclasses import replace

    from sqlmodel import Session, select

    from app.db import get_engine
    from app.models import Task
    from app.tasks import TaskSpec, sync

    spec = TaskSpec(
        "", "frost", "Protect", "Cover it", "cold", date(2026, 10, 8), date(2026, 10, 9), date(2026, 10, 10)
    )
    pid = owner.post(
        "/api/v1/plantings", json={"crop": "testcrop", "method": "direct", "start_date": "2026-10-01"}
    ).json()["id"]

    def generator(wanted: bool):
        return lambda p: [replace(spec, key=f"planting:{p.id}:frost")] if wanted else []

    with Session(get_engine()) as db:
        household = db.exec(select(Task.household_id).where(Task.planting_id == pid)).first()

        def run(wanted: bool) -> Task:
            sync(db, household, generator(wanted), {"frost"})
            db.commit()
            task = db.exec(select(Task).where(Task.kind == "frost", Task.planting_id == pid)).one()
            db.refresh(task)
            return task

        run(True)
        assert run(False).status == "skipped"  # the frost left the forecast
        task = run(True)
        assert task.status == "open"  # and came back
        task.status, task.completed_by = "skipped", 1  # a person said no
        db.add(task)
        db.commit()
        assert run(True).status == "skipped"


def test_water_alert_appears_when_the_soil_will_run_dry_and_restarts_after_watering():
    from app.engine.water import WaterProfile
    from app.tasks import water_alerts

    w = WaterProfile((0.5, 1.0, 0.8), (10, 10, 20, 10), 0.6, 0.5)
    start = date(2026, 10, 1)
    rows = [{"date": str(start + timedelta(days=i)), "et0": 10.0, "precip": 0.0} for i in range(1, 12)]
    sown = planting(status="sown", start_date=start)
    today = date(2026, 10, 2)

    (job,) = water_alerts(sown, "tomato", w, None, rows, today)
    assert job.kind == "water" and job.group == "Water" and job.ideal == date(2026, 10, 5)  # 20 mm >= 16.8 mm on day 4
    assert "20 mm" in job.reason and "since sowing on 1 October" in job.reason and job.key.endswith(":start")

    watered = date(2026, 10, 5)
    assert water_alerts(sown, "tomato", w, watered, rows, date(2026, 10, 6)) == []  # starts full again
    (again,) = water_alerts(sown, "tomato", w, watered, rows, date(2026, 10, 8))
    assert again.key.endswith(":2026-10-05") and "the last watering" in again.reason  # a new job, a new key
    rainy = [r | {"precip": 20.0} for r in rows]
    assert water_alerts(sown, "tomato", w, None, rainy, today) == []
    assert water_alerts(planting(), "tomato", w, None, rows, today) == []  # not sown yet
