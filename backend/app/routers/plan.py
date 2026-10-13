"""A drafted year of plantings for the household's beds, accepted in one go (PLAN 8.4)."""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from .. import catalog as cat
from ..deps import EditorDep, MemberDep, SessionDep
from ..engine import layout, needs, phenology, recommend, windows, yearplan
from ..models import Bed, Forecast, Household, Planting, Site
from .beds import crop_facts, grid_of, holds
from .catalog import CatalogDep, _overrides
from .garden import _archive, _climatology
from .household import household_settings
from .plantings import PlantingIn, make_planting
from .today import refresh_tasks
from .weather import local_today

router = APIRouter(prefix="/api/v1/plan", tags=["plan"])
MIN_SUCCESS = 0.6  # a crop is drafted only where it works in at least this share of years
EXTRA_BED = yearplan.Bed(-1, "Extra bed", 7, 7, 30)  # 7 x 7 cells of 30 cm, about 4 m²
EXTRA_M2 = 4
ENOUGH = 0.95  # coverage at which no further change is suggested


def replaceable(p: Planting) -> bool:
    """Made by the year plan and still only a plan: nothing is in the ground yet, so no work is lost by replacing it."""
    return p.source == "plan" and p.status == "planned"


def existing_supply(plantings, facts_of, beds_by_id, window_of, today: date) -> list[tuple[str, float, date, date]]:
    """Food that plantings already in the ground will give: (group, kg, harvest from, harvest to).
    ponytail: the harvest is taken as the last 30% of the days a planting holds its cells; a real per-planting
    outlook (`plantings.outlook`) could replace it."""
    out = []
    for p in plantings:
        f, bed = facts_of(p.crop), beds_by_id.get(p.bed_id)
        if (
            bed is None
            or not p.cells
            or p.status in ("finished", "failed")
            or not f["yield_per_m2"]
            or not f["food_group"]
        ):
            continue
        first, last = window_of(p)
        if last < today:
            continue
        kg = f["yield_per_m2"] * (bed.cell_cm / 100) ** 2 * len(p.cells)
        out.append((f["food_group"], kg, max(first, first + (last - first) * 0.7), last))
    return out


def with_coverage(grid, taken, wants, today: date, target, existing, companions=None) -> tuple[list[dict], dict]:
    """The draft, its coverage of the weekly target, and the one change that would lift coverage most: a 4 m² bed
    when it adds at least 1 point (none once coverage reaches ENOUGH)."""
    items, supply = yearplan.draft(grid, taken, wants, today, target, existing, companions)
    cov = needs.coverage(target, supply, today)
    cov["best_change"] = None
    if cov["overall"] < ENOUGH:
        _, more = yearplan.draft([*grid, EXTRA_BED], taken, wants, today, target, existing, companions)
        gain = needs.coverage(target, more, today)["overall"] - cov["overall"]
        if gain >= 0.01:
            cov["best_change"] = {"kind": "add_bed_area", "m2": EXTRA_M2, "gain": round(gain, 3)}
    return items, cov


def _plan_key(item) -> tuple:
    return (
        item.crop,
        item.method,
        item.start_date,
        item.set_out_date,
        item.bed_id,
        tuple(sorted(tuple(cell) for cell in (item.cells or []))),
    )


def _preview_diff(existing: list[Planting], proposed: list[PlantingIn]) -> dict[str, int]:
    old = [_plan_key(p) for p in existing]
    new = [_plan_key(p) for p in proposed]
    unchanged = 0
    remaining_old = old.copy()
    remaining_new = new.copy()
    for key in old:
        if key in remaining_new:
            unchanged += 1
            remaining_old.remove(key)
            remaining_new.remove(key)
    moved = 0
    for old_key in remaining_old.copy():
        match = next((key for key in remaining_new if key[:2] == old_key[:2]), None)
        if match is not None:
            moved += 1
            remaining_old.remove(old_key)
            remaining_new.remove(match)
    return {"added": len(remaining_new), "removed": len(remaining_old), "moved": moved, "unchanged": unchanged}


def _scheduled(db: SessionDep, household_id: int) -> int:
    return sum(replaceable(p) for p in db.exec(select(Planting).where(Planting.household_id == household_id)))


def _plan_count(db: SessionDep, household_id: int) -> int:
    return sum(p.source == "plan" for p in db.exec(select(Planting).where(Planting.household_id == household_id)))


def _clear(db: SessionDep, household_id: int) -> int:
    rows = list(db.exec(select(Planting).where(Planting.household_id == household_id, Planting.source == "plan")))
    for p in rows:
        db.delete(p)  # its jobs go with it
    return len(rows)


@router.get("/year")
def year_plan(me: MemberDep, db: SessionDep, c: CatalogDep) -> dict:
    """Plantings for the next 12 months that fit the beds, climate and what already grows there."""
    site = db.exec(select(Site).where(Site.household_id == me.household_id)).first()
    beds = db.exec(select(Bed).where(Bed.household_id == me.household_id).order_by(Bed.id)).all()
    people = household_settings(db.get(Household, me.household_id)).people
    if site is None or not beds:
        return {
            "garden": site is not None,
            "beds": bool(beds),
            "people": people,
            "items": [],
            "scheduled": _scheduled(db, me.household_id),
        }
    forecast = db.get(Forecast, site.id)
    today = local_today(forecast.raw) if forecast else datetime.now(UTC).date()
    climate = _climatology(_archive(site, db))
    threshold = windows.success_threshold(site.frost_probability)
    cache: dict = {}
    plantings = db.exec(select(Planting).where(Planting.household_id == me.household_id)).all()
    taken: dict[int, list] = {b.id: [] for b in beds}
    for p in plantings:
        if replaceable(p):  # an earlier plan not yet started is replaced by this one, not added to
            continue
        if p.bed_id in taken and p.cells:  # finished ones too: they decide rotation
            f = crop_facts(db, c, me.household_id, p.crop, cache)
            a, z = holds(p, f, today)
            taken[p.bed_id] += [((x[0], x[1]), a, z, f["family"], p.crop) for x in p.cells]
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
                    o["success"], f["dims"],
                    planted + timedelta(days=round(o["days_to_maturity"].get("p10") or days)),
                    planted + timedelta(days=days),
                    f["yield_per_m2"],
                    f["food_group"],
                )
            )  # fmt: skip
    flower_slugs = {f for fl in c.companions["flowers"].values() for f in fl}  # grown for the garden, not for food
    skipped = sorted(
        {w.crop for w in wants if w.crop not in flower_slugs and not (w.kg_per_m2 and w.food_group in needs.GROUPS)}
    )
    target = needs.weekly_target(people)
    beds_by_id = {b.id: b for b in beds}
    existing = existing_supply(
        [p for p in plantings if not replaceable(p)],
        lambda crop: crop_facts(db, c, me.household_id, crop, cache),
        beds_by_id,
        lambda p: holds(p, crop_facts(db, c, me.household_id, p.crop, cache), today),
        today,
    )
    grid = [yearplan.Bed(b.id, b.name, *grid_of(b), b.cell_cm) for b in beds]
    items, cov = with_coverage(grid, taken, wants, today, target, existing, c.companions)
    return {
        "garden": True,
        "beds": True,
        "today": today,
        "scheduled": sum(replaceable(p) for p in plantings),
        "people": people,
        "items": items,
        "coverage": cov,
        "skipped_no_yield": skipped,
    }


@router.post("/year/preview")
def preview_plan(items: list[PlantingIn], me: MemberDep, db: SessionDep) -> dict[str, int]:
    """Describe how a proposed plan differs from the replaceable plan without changing data."""
    if not 0 < len(items) <= 300:
        raise HTTPException(422, "Send between 1 and 300 plantings")
    existing = [p for p in db.exec(select(Planting).where(Planting.household_id == me.household_id)) if replaceable(p)]
    return _preview_diff(existing, items)


def _validate_plan(items: list[PlantingIn], db: SessionDep, household_id: int, c: CatalogDep) -> None:
    """Reject any plan that cannot physically fit, before replacing existing plan rows."""
    occupancy: dict[int, set[tuple[int, int]]] = {}
    existing = db.exec(select(Planting).where(Planting.household_id == household_id)).all()
    for row in existing:
        if replaceable(row) or row.bed_id is None:
            continue
        occupancy.setdefault(row.bed_id, set()).update(tuple(cell) for cell in row.cells)
    for item in items:
        if item.bed_id is None:
            continue
        bed = db.get(Bed, item.bed_id)
        if not bed or bed.household_id != household_id:
            raise HTTPException(422, "Every planned bed must belong to this household")
        cols, rows = grid_of(bed)
        cells = {tuple(cell) for cell in item.cells}
        if any(c < 0 or r < 0 or c >= cols or r >= rows for c, r in cells):
            raise HTTPException(422, f"Plan for {bed.name} uses cells outside the bed")
        prior = occupancy.setdefault(bed.id, set())
        if prior & cells:
            raise HTTPException(422, f"Year plan overlaps existing plants in {bed.name}")
        occupancy[bed.id] = prior | cells
        facts = crop_facts(db, c, household_id, item.crop, {})
        capacity = layout.plants_in(bed.cell_cm, facts["dims"], len(cells))
        if item.quantity is not None and item.quantity > capacity:
            raise HTTPException(422, f"Plan for {bed.name} exceeds the spacing capacity")


@router.post("/year", status_code=201)
def accept_plan(items: list[PlantingIn], me: EditorDep, db: SessionDep, c: CatalogDep) -> dict:
    """Make plantings of the accepted items (the same bodies as POST /plantings), then plan their jobs once.
    An earlier plan that has not started is replaced; anything sown or planted by hand stays."""
    if not 0 < len(items) <= 300:
        raise HTTPException(422, "Send between 1 and 300 plantings")
    _validate_plan(items, db, me.household_id, c)
    replaced = _clear(db, me.household_id)
    for body in items:
        row = make_planting(body, me, db, c)
        row.source = "plan"
        db.add(row)
    db.commit()
    refresh_tasks(db, me.household_id, c)
    return {"created": len(items), "replaced": replaced}


@router.delete("/year")
def clear_plan(me: EditorDep, db: SessionDep, c: CatalogDep) -> dict:
    """Remove every planting created by the year plan; hand-made plantings stay."""
    removed = _clear(db, me.household_id)
    db.commit()
    refresh_tasks(db, me.household_id, c)
    return {"removed": removed}
