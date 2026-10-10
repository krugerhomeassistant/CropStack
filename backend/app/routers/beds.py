"""Beds on the garden plan: where things grow, how big, and whether they are full (SPEC §7.1, §7.2)."""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from .. import catalog as cat
from ..deps import EditorDep, MemberDep, SessionDep
from ..engine import layout
from ..models import Bed, Planting
from .catalog import CatalogDep, _overrides
from .today import refresh_tasks

router = APIRouter(prefix="/api/v1/beds", tags=["beds"])
LIVE = ("planned", "sown", "germinated", "transplanted", "harvesting")
MAX_M = 1000.0


class BedIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    kind: Literal["bed", "container", "row"] = "bed"
    x: float = Field(0, ge=0, le=MAX_M)
    y: float = Field(0, ge=0, le=MAX_M)
    width: float = Field(gt=0, le=100)
    length: float = Field(gt=0, le=100)


class BedPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=60)
    kind: Literal["bed", "container", "row"] | None = None
    x: float | None = Field(None, ge=0, le=MAX_M)
    y: float | None = Field(None, ge=0, le=MAX_M)
    width: float | None = Field(None, gt=0, le=100)
    length: float | None = Field(None, gt=0, le=100)


def _own(db: SessionDep, household_id: int, bed_id: int) -> Bed:
    row = db.get(Bed, bed_id)
    if not row or row.household_id != household_id:
        raise HTTPException(404, "No such bed")
    return row


@router.get("")
def list_beds(me: MemberDep, db: SessionDep, c: CatalogDep) -> list[dict]:
    """Every bed with what is planted in it and how full it is."""
    beds = db.exec(select(Bed).where(Bed.household_id == me.household_id).order_by(Bed.id)).all()
    plantings = db.exec(
        select(Planting).where(Planting.household_id == me.household_id, Planting.status.in_(LIVE))  # type: ignore[attr-defined]
    ).all()
    out = []
    for bed in beds:
        inside = [p for p in plantings if p.bed_id == bed.id]
        feet = [
            (
                p.quantity,
                layout.footprint_m2(
                    cat.effective(c, "crop", p.crop, _overrides(db, me.household_id, "crop", p.crop)) or {}
                ),
            )
            for p in inside
        ]
        use = layout.bed_use(bed.width * bed.length, feet)
        out.append(
            bed.model_dump()
            | {
                "plantings": [p.id for p in inside],
                "area_m2": round(use.area_m2, 2),
                "needed_m2": round(use.needed_m2, 2),
                "unknown_footprint": use.unknown,
                "crowded": use.crowded,
            }
        )
    return out


@router.post("", status_code=201)
def add_bed(body: BedIn, me: EditorDep, db: SessionDep) -> Bed:
    row = Bed(household_id=me.household_id, **body.model_dump())
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
    db.add(row)
    if renamed:  # plantings and their jobs say "in <bed>", so they follow the new name
        for p in db.exec(select(Planting).where(Planting.bed_id == bed_id)):
            p.location = row.name
            db.add(p)
    db.commit()
    if renamed:
        refresh_tasks(db, me.household_id, c)
    db.refresh(row)
    return row


@router.delete("/{bed_id}", status_code=204)
def delete_bed(bed_id: int, me: EditorDep, db: SessionDep) -> None:
    db.delete(_own(db, me.household_id, bed_id))  # plantings stay, with bed_id emptied (ON DELETE SET NULL)
    db.commit()
