"""Beds on the garden plan: where things grow, how big, which cells hold what and when (SPEC §7.1, §7.2)."""

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .. import catalog as cat
from ..deps import EditorDep, MemberDep, SessionDep
from ..engine import layout, phenology
from ..models import Bed, Planting
from .catalog import CatalogDep, _overrides
from .today import refresh_tasks

router = APIRouter(prefix="/api/v1/beds", tags=["beds"])
MAX_M = 1000.0
MAX_CELLS = layout.MAX_CELLS


class BedIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    kind: Literal["bed", "container", "row"] = "bed"
    x: float = Field(0, ge=0, le=MAX_M)
    y: float = Field(0, ge=0, le=MAX_M)
    width: float = Field(gt=0, le=100)
    length: float = Field(gt=0, le=100)
    cell_cm: int | None = Field(None, ge=5, le=100)  # blank: whole cells that fit the bed exactly
    layout: str = Field("", max_length=60)


class BedPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=60)
    kind: Literal["bed", "container", "row"] | None = None
    x: float | None = Field(None, ge=0, le=MAX_M)
    y: float | None = Field(None, ge=0, le=MAX_M)
    width: float | None = Field(None, gt=0, le=100)
    length: float | None = Field(None, gt=0, le=100)
    cell_cm: int | None = Field(None, ge=5, le=100)
    layout: str | None = Field(None, max_length=60)


def _own(db: SessionDep, household_id: int, bed_id: int) -> Bed:
    row = db.get(Bed, bed_id)
    if not row or row.household_id != household_id:
        raise HTTPException(404, "No such bed")
    return row


def grid_of(bed: Bed) -> tuple[int, int]:
    return layout.grid(bed.width, bed.length, bed.cell_cm)


def crop_facts(db: Session, c: cat.Catalog, household_id: int, crop: str, cache: dict) -> dict:
    """What the layout and the year plan need to know about a crop: name, family, plant footprint, longest cycle,
    yield per m² and food group."""
    if crop not in cache:
        item = cat.effective(c, "crop", crop, _overrides(db, household_id, "crop", crop)) or {}
        profile = phenology.profile_from_item(item) if item else None
        cache[crop] = {
            "name": (item.get("names", {}).get("en") or [crop])[0],
            "family": item.get("family", ""),
            "footprint": layout.footprint_m2(item),
            "dims": layout.dims_cm(item),
            "cycle_days": profile.cycle_days[1] if profile and profile.usable else None,
            "yield_per_m2": layout.yield_per_m2(item),
            "food_group": item.get("food_group"),
        }
    return cache[crop]


def holds(p: Planting, facts: dict, today: date) -> tuple[date, date]:
    return layout.occupancy(p.start_date, p.set_out_date, p.ends_on, p.status, facts["cycle_days"], today)


def cm(bed: Bed) -> tuple[int, int]:
    return round(bed.width * 100), round(bed.length * 100)


def spots_of(p: Planting, bed: Bed, dims) -> list[list[int]]:
    """Where a planting's plants stand: as saved, else laid out over its cells (rows made before plants had places)."""
    if p.spots or not p.cells:
        return p.spots
    return [list(s) for s in layout.fill(p.cells, bed.cell_cm, *cm(bed), dims, limit=p.quantity)]


def ground_taken(
    db: Session, c: cat.Catalog, household_id: int, bed: Bed, first: date, last: date, skip: int | None = None
) -> list[layout.Spot]:
    """Plants of other plantings that stand in a bed at any time between two dates, so new ones go round them."""
    cache: dict = {}
    today = datetime.now(UTC).date()
    out: list[layout.Spot] = []
    for p in db.exec(select(Planting).where(Planting.bed_id == bed.id)):
        if p.id == skip or not p.cells or p.status in ("finished", "failed"):
            continue
        f = crop_facts(db, c, household_id, p.crop, cache)
        a, z = holds(p, f, today)
        if a <= last and first <= z:
            out += [tuple(s) for s in spots_of(p, bed, f["dims"])]  # type: ignore[misc]
    return out


@router.get("")
def list_beds(me: MemberDep, db: SessionDep, c: CatalogDep) -> list[dict]:
    """Every bed with its cells, what sits in them and when, clashes, and whether the plants fit."""
    today = datetime.now(UTC).date()
    cache: dict = {}
    beds = db.exec(select(Bed).where(Bed.household_id == me.household_id).order_by(Bed.id)).all()
    plantings = db.exec(select(Planting).where(Planting.household_id == me.household_id)).all()
    from .plantings import outlook

    ahead = outlook(db, me.household_id)
    out = []
    for bed in beds:
        cols, rows = grid_of(bed)
        inside = [p for p in plantings if p.bed_id == bed.id]
        placements, held, over, legacy = [], [], [], []
        for p in inside:
            f = crop_facts(db, c, me.household_id, p.crop, cache)
            first, last = holds(p, f, today)
            live = p.status not in ("finished", "failed")
            cells = [tuple(x) for x in p.cells]
            spots = spots_of(p, bed, f["dims"])
            capacity = len(spots)
            if cells:
                held += [(p.id, tuple(s), first, last) for s in spots]
                if live and p.quantity > capacity:
                    over.append(p.id)
            elif live:
                legacy.append((p.quantity, f["footprint"]))
            placements.append(
                {
                    "planting_id": p.id,
                    "crop": p.crop,
                    "purpose": cat.effective(c, "crop", p.crop, _overrides(db, me.household_id, "crop", p.crop)).get(
                        "purpose", "food"
                    ),
                    "name": f["name"],
                    "cells": p.cells,
                    "spots": spots,
                    "from": first,
                    "until": last,
                    "quantity": p.quantity,
                    "method": p.method,
                    "start_date": p.start_date,
                    "set_out_date": p.set_out_date,
                    "capacity": capacity,
                    "harvest_from": ahead.get(p.id, {}).get("harvest_from"),
                    "harvest_to": ahead.get(p.id, {}).get("harvest_to"),
                    "next_job": ahead.get(p.id, {}).get("next_job"),
                    "status": p.status,
                }
            )
        clash = layout.spot_clashes(held, bed.cell_cm)
        use = layout.bed_use(bed.width * bed.length, legacy)
        out.append(
            bed.model_dump()
            | {
                "cols": cols,
                "rows": rows,
                "plantings": [
                    p.id for p in inside if p.status in ("planned", "sown", "germinated", "transplanted", "harvesting")
                ],
                "placements": placements,
                "clashes": [{"cell": list(cell), "plantings": [a, b]} for cell, a, b in clash],
                "over_capacity": over,
                "area_m2": round(use.area_m2, 2),
                "needed_m2": round(use.needed_m2, 2),
                "unknown_footprint": use.unknown,
                "crowded": bool(clash or over or use.crowded),
                "outside": sum(1 for p in inside for x in p.cells if x[0] >= cols or x[1] >= rows),
            }
        )
    return out


class ArrangeCrop(BaseModel):
    crop: str
    amount: int | None = Field(None, ge=1, le=MAX_CELLS)  # blank: as many as fit


class ArrangeIn(BaseModel):
    crops: list[ArrangeCrop] = Field(min_length=1, max_length=12)
    area: list[int] | None = Field(
        None, min_length=4, max_length=4
    )  # a section: first col, first row, last col, last row
    how: Literal["mixed", "rows", "columns"] = "mixed"
    start_date: date


@router.post("/{bed_id}/arrange")
def arrange_bed(bed_id: int, body: ArrangeIn, me: MemberDep, db: SessionDep, c: CatalogDep) -> dict:
    """Where chosen crops would stand in a bed (nothing is saved): the whole bed, a section, or a number of plants, any
    mix of them, with what else grows well beside them. A section too small for the amounts grows until they fit."""
    bed = _own(db, me.household_id, bed_id)
    cache: dict = {}
    for x in body.crops:
        if c.get("crop", x.crop) is None:
            raise HTTPException(422, f"No crop {x.crop!r} in the catalog")
    facts = [crop_facts(db, c, me.household_id, x.crop, cache) for x in body.crops]
    cols, rows = grid_of(bed)
    area = None
    if body.area:
        c0, r0, c1, r1 = body.area
        area = (max(0, min(c0, c1)), max(0, min(r0, r1)), min(cols - 1, max(c0, c1)), min(rows - 1, max(r0, r1)))
        if area[0] > area[2] or area[1] > area[3]:
            raise HTTPException(422, "That section is outside the bed")
    last = body.start_date + timedelta(days=round(max((f["cycle_days"] or layout.DEFAULT_CYCLE_DAYS) for f in facts)))
    used, laid = layout.arrange(
        cols, rows, bed.cell_cm, *cm(bed), [(f["dims"], x.amount) for f, x in zip(facts, body.crops, strict=True)],
        area, body.how, ground_taken(db, c, me.household_id, bed, body.start_date, last),
    )  # fmt: skip
    chosen = {x.crop for x in body.crops}
    score: dict[str, int] = {}
    for x in chosen:
        for friend in c.companions["good"].get(x, ()):
            score[friend] = score.get(friend, 0) + 1
    bad = {b for x in chosen for b in c.companions["avoid"].get(x, ())}
    friends = sorted((k for k in score if k not in chosen | bad), key=lambda k: (-score[k], k))[:8]
    return {
        "area": list(used),
        "full": used == (0, 0, cols - 1, rows - 1),
        "items": [
            {"crop": x.crop, "name": f["name"], "amount": len(s), "capacity": cap, "spots": [list(p) for p in s]}
            for x, f, (s, cap) in zip(body.crops, facts, laid, strict=True)
        ],
        "companions": [{"crop": k, "name": crop_facts(db, c, me.household_id, k, cache)["name"]} for k in friends],
    }


@router.post("", status_code=201)
def add_bed(body: BedIn, me: EditorDep, db: SessionDep) -> Bed:
    data = body.model_dump()
    data["cell_cm"] = body.cell_cm or layout.fit_cell(body.width, body.length)
    row = Bed(household_id=me.household_id, **data)
    cols, rows = grid_of(row)
    if cols * rows > MAX_CELLS:
        raise HTTPException(422, "That many cells is too many; use a bigger cell size")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{bed_id}")
def update_bed(bed_id: int, body: BedPatch, me: EditorDep, db: SessionDep, c: CatalogDep) -> Bed:
    row = _own(db, me.household_id, bed_id)
    changes = {k: v for k, v in body.model_dump(exclude_unset=True, exclude_none=True).items() if getattr(row, k) != v}
    renamed = "name" in changes
    old_cm = row.cell_cm
    width, length = changes.get("width", row.width), changes.get("length", row.length)
    fit = layout.fit_cell(width, length)
    if "cell_cm" not in changes and fit != old_cm and not layout.fits(width, length, old_cm):  # the cells no longer fit
        changes["cell_cm"] = fit
    for key, value in changes.items():
        setattr(row, key, value)
    cols, rows = grid_of(row)
    if cols * rows > MAX_CELLS:
        raise HTTPException(422, "That many cells is too many; use a bigger cell size")
    db.add(row)
    for p in db.exec(select(Planting).where(Planting.bed_id == bed_id)):
        if renamed:  # plantings and their jobs say "in <bed>", so they follow the new name
            p.location = row.name
        # Never drop where things grow: plants keep their place and size whatever the cells are, and plants left
        # outside a smaller bed are kept (and reported) so making it bigger again brings them back.
        if "cell_cm" in changes:
            p.cells = layout.cover(p.spots, row.cell_cm) if p.spots else layout.remap(p.cells, old_cm, row.cell_cm)
        db.add(p)
    db.commit()
    if renamed:
        refresh_tasks(db, me.household_id, c)
    db.refresh(row)
    return row


@router.delete("/{bed_id}", status_code=204)
def delete_bed(bed_id: int, me: EditorDep, db: SessionDep) -> None:
    for p in db.exec(select(Planting).where(Planting.bed_id == bed_id)):
        p.cells = []  # the plantings stay, unplaced
        db.add(p)
    db.delete(_own(db, me.household_id, bed_id))
    db.commit()
