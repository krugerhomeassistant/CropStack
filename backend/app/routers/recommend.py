"""What to plant now or soon, and where it would fit in the garden plan (SPEC §9.1)."""

from datetime import timedelta

from fastapi import APIRouter, Query
from sqlmodel import select

from .. import catalog as cat
from ..deps import MemberDep, SessionDep
from ..engine import layout, phenology, recommend, windows
from ..models import Bed, Planting, Site
from .beds import crop_facts, grid_of, holds
from .catalog import CatalogDep, _overrides
from .garden import _archive, _climatology
from .weather import local_today

router = APIRouter(prefix="/api/v1", tags=["recommendations"])
SUGGEST_CELLS = 4  # how many cells a suggestion starts with; the planting can be changed afterwards


def _where(beds, plantings, facts, f, first, last):
    """The bed with the most room for this crop between `first` and `last`, and the cells to use in it."""
    best = None
    for bed in beds:
        cols, rows = grid_of(bed)
        taken = []
        for p in plantings:
            if p.bed_id == bed.id and p.cells:
                a, b = holds(p, facts(p.crop), first)
                taken += [((x[0], x[1]), a, b) for x in p.cells]
        free = layout.free_cells(cols, rows, taken, first, last)
        # cells that last grew the same family come last (rotation), so a fresh cell is chosen when there is one
        if f["family"]:
            used = {
                (x[0], x[1])
                for p in plantings
                if p.bed_id == bed.id and facts(p.crop)["family"] == f["family"]
                for x in p.cells
            }
            free.sort(key=lambda cell: cell in used)
        else:
            used = set()
        if free and (best is None or len(free) > best[1]):
            best = (bed, len(free), free, used)
    if best is None:
        return None
    bed, n, free, used = best
    chosen = free[:SUGGEST_CELLS]
    return {
        "bed_id": bed.id,
        "bed": bed.name,
        "cells": [list(x) for x in chosen],
        "free_cells": n,
        "plants": layout.per_cell(bed.cell_cm, f["footprint"]) * len(chosen),
        "same_family_before": any(x in used for x in chosen),
    }


@router.get("/recommendations")
def recommendations(me: MemberDep, db: SessionDep, c: CatalogDep, horizon: int = Query(21, ge=1, le=120)) -> dict:
    """Crops that can go in the ground now or soon at this site, best first, each with where it fits."""
    site = db.exec(select(Site).where(Site.household_id == me.household_id)).first()
    if site is None:
        return {"garden": False, "now": [], "soon": []}
    from ..models import Forecast

    forecast = db.get(Forecast, site.id)
    from datetime import UTC, datetime

    today = local_today(forecast.raw) if forecast else datetime.now(UTC).date()
    climate = _climatology(_archive(site, db))
    threshold = windows.success_threshold(site.frost_probability)
    beds = db.exec(select(Bed).where(Bed.household_id == me.household_id).order_by(Bed.id)).all()
    plantings = db.exec(select(Planting).where(Planting.household_id == me.household_id)).all()
    cache: dict = {}

    def facts(crop: str) -> dict:
        return crop_facts(db, c, me.household_id, crop, cache)

    out = []
    for slug, _ in c.list("crop"):
        item = cat.effective(c, "crop", slug, _overrides(db, me.household_id, "crop", slug))
        profile = phenology.profile_from_item(item) if item else None
        if not profile or not profile.usable:
            continue
        pick = recommend.best_option(recommend.options(windows.analyse(climate, profile, threshold), today, horizon))
        if not pick:
            continue
        f = facts(slug)
        days = pick["days_to_maturity"].get("p90") or f["cycle_days"] or layout.DEFAULT_CYCLE_DAYS
        planted = pick["start"]  # sowing day, or set-out day for seedlings
        sow = planted - timedelta(days=pick["age_days"]) if pick["method"] == "transplant" else planted
        out.append(
            {
                "crop": slug,
                "name": f["name"],
                "method": pick["method"],
                "state": pick["state"],
                "start_date": sow,
                "set_out_date": planted if pick["method"] == "transplant" else None,
                "from": planted,
                "until": pick["until"],
                "best_from": pick["best_from"],
                "best_to": pick["best_to"],
                "all_year": pick["all_year"],
                "success": pick["success"],
                "age_days": pick["age_days"],
                # if it goes in on its first good day: when the harvest starts in most years
                "harvest_from": planted + timedelta(days=round(pick["days_to_maturity"].get("p10") or days)),
                "harvest_to": planted + timedelta(days=round(days)),
                "family": f["family"],
                "plants_per_cell": layout.per_cell(30, f["footprint"]),
                "where": _where(beds, plantings, facts, f, planted, planted + timedelta(days=round(days))),
            }
        )
    out.sort(
        key=lambda r: (
            r["state"] != "now",
            r["all_year"],
            r["from"] if r["state"] == "soon" else today,
            -r["success"],
            r["name"],
        )
    )
    return {
        "garden": True,
        "today": today,
        "has_beds": bool(beds),
        "now": [r for r in out if r["state"] == "now"],
        "soon": [r for r in out if r["state"] == "soon"],
    }
