"""A drafted year of plantings for the household's beds, accepted in one go (PLAN 8.4)."""

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from .. import catalog as cat
from ..deps import EditorDep, MemberDep, SessionDep
from ..engine import layout, phenology, recommend, windows, yearplan
from ..models import Bed, Forecast, Planting, Site
from .beds import crop_facts, grid_of, holds
from .catalog import CatalogDep, _overrides
from .garden import _archive, _climatology
from .plantings import PlantingIn, make_planting
from .today import refresh_tasks
from .weather import local_today

router = APIRouter(prefix="/api/v1/plan", tags=["plan"])
MIN_SUCCESS = 0.6  # a crop is drafted only where it works in at least this share of years


@router.get("/year")
def year_plan(me: MemberDep, db: SessionDep, c: CatalogDep) -> dict:
    """Plantings for the next 12 months that fit the beds, climate and what already grows there."""
    site = db.exec(select(Site).where(Site.household_id == me.household_id)).first()
    beds = db.exec(select(Bed).where(Bed.household_id == me.household_id).order_by(Bed.id)).all()
    if site is None or not beds:
        return {"garden": site is not None, "beds": bool(beds), "items": []}
    forecast = db.get(Forecast, site.id)
    today = local_today(forecast.raw) if forecast else datetime.now(UTC).date()
    climate = _climatology(_archive(site, db))
    threshold = windows.success_threshold(site.frost_probability)
    cache: dict = {}
    plantings = db.exec(select(Planting).where(Planting.household_id == me.household_id)).all()
    taken: dict[int, list] = {b.id: [] for b in beds}
    for p in plantings:
        if p.bed_id in taken and p.cells:  # finished ones too: they decide rotation
            f = crop_facts(db, c, me.household_id, p.crop, cache)
            a, z = holds(p, f, today)
            taken[p.bed_id] += [((x[0], x[1]), a, z, f["family"]) for x in p.cells]
    wants = []
    for slug, _ in c.list("crop"):
        item = cat.effective(c, "crop", slug, _overrides(db, me.household_id, "crop", slug))
        profile = phenology.profile_from_item(item) if item else None
        if not profile or not profile.usable:
            continue
        f = crop_facts(db, c, me.household_id, slug, cache)
        best: dict = {}  # per sowing window (month it opens): the likeliest way, direct first
        for o in recommend.options(windows.analyse(climate, profile, threshold), today, 365):
            if o["all_year"] or o["success"] < MIN_SUCCESS:
                continue
            key = (o["best_from"].year, o["best_from"].month)
            if key not in best or (o["success"], o["method"] == "direct") > (
                best[key]["success"],
                best[key]["method"] == "direct",
            ):
                best[key] = o
        for o in best.values():
            planted = o["best_from"]
            days = round(o["days_to_maturity"].get("p90") or f["cycle_days"] or layout.DEFAULT_CYCLE_DAYS)
            transplant = o["method"] == "transplant"
            start = planted - timedelta(days=o["age_days"]) if transplant else planted
            wants.append(
                yearplan.Want(
                    slug, f["name"], f["family"], o["method"], start, planted if transplant else None, planted, days,
                    o["success"], f["footprint"],
                    planted + timedelta(days=round(o["days_to_maturity"].get("p10") or days)),
                    planted + timedelta(days=days),
                )
            )  # fmt: skip
    grid = [yearplan.Bed(b.id, b.name, *grid_of(b), b.cell_cm) for b in beds]
    return {"garden": True, "beds": True, "today": today, "items": yearplan.draft(grid, taken, wants, today)}


@router.post("/year", status_code=201)
def accept_plan(items: list[PlantingIn], me: EditorDep, db: SessionDep, c: CatalogDep) -> dict:
    """Make plantings of the accepted items (the same bodies as POST /plantings), then plan their jobs once."""
    if not 0 < len(items) <= 300:
        raise HTTPException(422, "Send between 1 and 300 plantings")
    for body in items:
        db.add(make_planting(body, me, db, c))
    db.commit()
    refresh_tasks(db, me.household_id, c)
    return {"created": len(items)}
