"""Today: the household's open jobs, made by the task engine from its plantings (SPEC §9.2, §11.2)."""

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from .. import catalog as cat
from .. import scheduler, weather
from ..db import get_engine
from ..deps import EditorDep, MemberDep, SessionDep
from ..engine import phenology, water, windows
from ..models import ClimateArchive, Forecast, Planting, Site, Task, now
from ..tasks import TaskSpec, crop_schedule, scout_checks, sync, water_alerts, weather_alerts
from .catalog import CatalogDep, _overrides, load_catalog
from .garden import _climatology
from .weather import local_today

router = APIRouter(prefix="/api/v1", tags=["today"])
GROUPS = ["Protect", "Plant", "Water", "Feed", "Harvest", "Animals", "Check", "Maintain"]  # SPEC §11.2 order
UPCOMING_DAYS = 14


def refresh_tasks(db: Session, household_id: int, c: cat.Catalog) -> None:
    """Regenerate the household's tasks from its plantings. Uses the climate record already stored (no network);
    without one, harvest dates fall back to the crop's catalogued cycle length."""
    site = db.exec(select(Site).where(Site.household_id == household_id)).first()
    archive = db.get(ClimateArchive, site.id) if site else None
    climate = _climatology(archive) if archive else None

    def specs(p: Planting) -> list[TaskSpec]:
        item = cat.effective(c, "crop", p.crop, _overrides(db, household_id, "crop", p.crop))
        if item is None:
            return []
        profile = phenology.profile_from_item(item)
        name = (item.get("names", {}).get("en") or [p.crop])[0]
        maturity = None
        if climate and profile.usable:
            age = (p.set_out_date - p.start_date).days if p.method == "transplant" and p.set_out_date else 0
            maturity = windows.maturity(
                climate, profile, p.set_out_date if age and p.set_out_date else p.start_date, age
            )
        cycle = (round(profile.cycle_days[0]), round(profile.cycle_days[1])) if profile.usable else None
        return crop_schedule(p, name.lower(), maturity, cycle)

    sync(db, household_id, specs, {"sow", "set_out", "harvest"})
    db.commit()
    refresh_protect(db, household_id, c)


def refresh_protect(db: Session, household_id: int, c: cat.Catalog) -> None:
    """Frost, heat and water jobs from the stored weather; cheap, so it also runs whenever Today is opened."""
    site = db.exec(select(Site).where(Site.household_id == household_id)).first()
    stored = db.get(Forecast, site.id) if site else None
    today = local_today(stored.raw) if stored else datetime.now(UTC).date()
    all_rows = weather.daily_rows(stored.raw) if stored else []
    ahead = weather.split(all_rows, today)[1]
    awc = water.SOIL_AWC_MM_PER_M[site.soil if site else ""]
    last_done: dict[tuple[str, int], date] = {}  # (job kind, planting) -> the last day a person said they did it
    for t in db.exec(
        select(Task).where(
            Task.household_id == household_id, Task.kind.in_(("water", "check")), Task.completed_by.is_not(None)
        )  # type: ignore[attr-defined]
    ):
        # a skipped look still starts the next week's check; a skipped watering does not count as watered
        if t.planting_id and t.completed_at and (t.status == "done" or t.kind == "check"):
            k = (t.kind, t.planting_id)
            last_done[k] = max(last_done.get(k, date.min), t.completed_at.date())

    def specs(p: Planting) -> list[TaskSpec]:
        item = cat.effective(c, "crop", p.crop, _overrides(db, household_id, "crop", p.crop))
        if item is None:
            return []
        profile = phenology.profile_from_item(item)
        name = (item.get("names", {}).get("en") or [p.crop])[0].lower()
        out = weather_alerts(p, name, profile.lethal_min, profile.stress_max, ahead)
        thirst = water.profile_from_item(item, profile.cycle_days if profile.usable else None)
        return (
            out
            + (
                water_alerts(p, name, thirst, last_done.get(("water", p.id)), all_rows, today, awc)
                if thirst and all_rows
                else []
            )
            + scout_checks(p, name, last_done.get(("check", p.id)))
        )

    sync(db, household_id, specs, {"frost", "heat", "water", "check"})
    db.commit()


@scheduler.job("tasks", every=timedelta(hours=12))
def refresh_all() -> None:
    """Keep every household's tasks current as the climate record and the catalog change."""
    c = load_catalog()
    with Session(get_engine()) as db:
        for household_id in db.exec(select(Planting.household_id).distinct()).all():
            refresh_tasks(db, household_id, c)


def _how(c: cat.Catalog) -> dict[str, list[str]]:
    """Plain steps for each kind of job, from the catalog's task templates."""
    return {data["task_kind"]: data["steps"] for _, data in c.list("task_template")}


VERDICTS = {"keep": "Keep", "remove": "Remove", "tolerate_below_threshold": "Leave unless numbers build"}


def _watch(c: cat.Catalog) -> list[dict]:
    """What to look for on a Check job: each organism with how to recognise it and whether to keep or remove it."""
    out = []
    for slug, data in c.list("organism"):
        p = data.get("params", {})
        out.append(
            {
                "slug": slug,
                "name": data["names"]["en"][0],
                "type": data["organism_type"],
                "identify": p.get("identify", {}).get("value", ""),
                "verdict": VERDICTS.get(p.get("verdict", {}).get("value", ""), ""),
                "action": p.get("first_action", {}).get("value", ""),
            }
        )
    return out


def _view(t: Task, today: date, how: dict[str, list[str]], watch: list[dict] | None = None) -> dict:
    return {
        "watch": watch if t.kind == "check" else [],
        "steps": how.get(t.kind, []),
        "id": t.id,
        "kind": t.kind,
        "group": t.group,
        "title": t.title,
        "reason": t.reason,
        "earliest": t.earliest,
        "ideal": t.ideal,
        "latest": t.latest,
        "overdue": t.latest < today,
        "planting_id": t.planting_id,
    }


def _today(db: Session, household_id: int) -> date:
    site = db.exec(select(Site).where(Site.household_id == household_id)).first()
    forecast = db.get(Forecast, site.id) if site else None
    return local_today(forecast.raw) if forecast else datetime.now(UTC).date()


@router.get("/today")
def get_today(me: MemberDep, db: SessionDep, c: CatalogDep) -> dict:
    refresh_protect(db, me.household_id, c)
    today = _today(db, me.household_id)
    open_tasks = db.exec(
        select(Task).where(Task.household_id == me.household_id, Task.status == "open").order_by(Task.ideal)
    ).all()
    due = [t for t in open_tasks if t.earliest <= today]
    soon = [t for t in open_tasks if today < t.earliest <= today + timedelta(days=UPCOMING_DAYS)]
    how, watch = _how(c), _watch(c)
    return {
        "date": today,
        "groups": [
            {"group": g, "tasks": [_view(t, today, how, watch) for t in due if t.group == g]}
            for g in GROUPS
            if any(t.group == g for t in due)
        ],
        "upcoming": [_view(t, today, how, watch) for t in soon],
    }


class TaskPatch(BaseModel):
    status: Literal["done", "skipped"]


# Completing a job moves its planting along; later states are never moved back.
_ORDER = ["planned", "sown", "germinated", "transplanted", "harvesting", "finished", "failed"]
_AFTER = {"sow": "sown", "set_out": "transplanted", "harvest": "harvesting"}  # frost, heat and water change nothing


@router.patch("/tasks/{task_id}")
def update_task(task_id: int, body: TaskPatch, me: EditorDep, db: SessionDep, c: CatalogDep) -> dict:
    task = db.get(Task, task_id)
    if not task or task.household_id != me.household_id:
        raise HTTPException(404, "No such task")
    if task.status != "open":
        raise HTTPException(409, f"This job is already {task.status}")
    task.status = body.status
    task.completed_at, task.completed_by = now(), me.user_id
    db.add(task)
    planting = db.get(Planting, task.planting_id) if task.planting_id else None
    target = _AFTER.get(task.kind)
    if body.status == "done" and planting and target and _ORDER.index(target) > _ORDER.index(planting.status):
        planting.status = target  # "failed" sorts last, so a failed planting is never revived
        db.add(planting)
    db.commit()
    refresh_tasks(db, me.household_id, c)
    return _view(task, _today(db, me.household_id), _how(c), _watch(c)) | {"status": task.status}
