"""Beds on the garden plan: where things grow, how big, which cells hold what and when (SPEC §7.1, §7.2)."""

from datetime import UTC, date, datetime
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
MAX_CELLS = 2500  # per bed


class BedIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    kind: Literal["bed", "container", "row"] = "bed"
    x: float = Field(0, ge=0, le=MAX_M)
    y: float = Field(0, ge=0, le=MAX_M)
    width: float = Field(gt=0, le=100)
    length: float = Field(gt=0, le=100)
    cell_cm: int = Field(30, ge=5, le=100)
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
    """What the layout needs to know about a crop: name, family, plant footprint and longest cycle."""
    if crop not in cache:
        item = cat.effective(c, "crop", crop, _overrides(db, household_id, "crop", crop)) or {}
        profile = phenology.profile_from_item(item) if item else None
        cache[crop] = {
            "name": (item.get("names", {}).get("en") or [crop])[0],
            "family": item.get("family", ""),
            "footprint": layout.footprint_m2(item),
            "cycle_days": profile.cycle_days[1] if profile and profile.usable else None,
        }
    return cache[crop]


def holds(p: Planting, facts: dict, today: date) -> tuple[date, date]:
    return layout.occupancy(p.start_date, p.set_out_date, p.ends_on, p.status, facts["cycle_days"], today)


@router.get("")
def list_beds(me: MemberDep, db: SessionDep, c: CatalogDep) -> list[dict]:
    """Every bed with its cells, what sits in them and when, clashes, and whether the plants fit."""
    today = datetime.now(UTC).date()
    cache: dict = {}
    beds = db.exec(select(Bed).where(Bed.household_id == me.household_id).order_by(Bed.id)).all()
    plantings = db.exec(select(Planting).where(Planting.household_id == me.household_id)).all()
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
            capacity = layout.per_cell(bed.cell_cm, f["footprint"]) * len(cells)
            if cells:
                held += [(p.id, cell, first, last) for cell in cells]
                if live and p.quantity > capacity:
                    over.append(p.id)
            elif live:
                legacy.append((p.quantity, f["footprint"]))
            placements.append(
                {
                    "planting_id": p.id,
                    "crop": p.crop,
                    "name": f["name"],
                    "cells": p.cells,
                    "from": first,
                    "until": last,
                    "quantity": p.quantity,
                    "capacity": capacity,
                    "status": p.status,
                }
            )
        clash = layout.clashes(held)
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
            }
        )
    return out


@router.post("", status_code=201)
def add_bed(body: BedIn, me: EditorDep, db: SessionDep) -> Bed:
    row = Bed(household_id=me.household_id, **body.model_dump())
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
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    renamed = "name" in changes and changes["name"] != row.name
    for key, value in changes.items():
        setattr(row, key, value)
    cols, rows = grid_of(row)
    if cols * rows > MAX_CELLS:
        raise HTTPException(422, "That many cells is too many; use a bigger cell size")
    db.add(row)
    for p in db.exec(select(Planting).where(Planting.bed_id == bed_id)):
        if renamed:  # plantings and their jobs say "in <bed>", so they follow the new name
            p.location = row.name
        if {"width", "length", "cell_cm"} & changes.keys():  # a smaller or finer grid drops the cells that fell off
            p.cells = [x for x in p.cells if x[0] < cols and x[1] < rows] if "cell_cm" not in changes else []
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
