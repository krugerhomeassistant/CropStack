"""Plantings: what the household has sown or plans to sow (SPEC §6.2)."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlmodel import select

from ..deps import EditorDep, MemberDep, SessionDep
from ..engine import layout
from ..models import Bed, Harvest, Planting
from .catalog import CatalogDep
from .today import refresh_tasks

router = APIRouter(prefix="/api/v1/plantings", tags=["plantings"])

Status = Literal["planned", "sown", "germinated", "transplanted", "harvesting", "finished", "failed"]
# Forward only, and "failed" from anywhere that is not already over; a mistake is fixed by deleting the planting.
NEXT: dict[str, set[str]] = {
    "planned": {"sown", "failed"},
    "sown": {"germinated", "failed"},
    "germinated": {"transplanted", "harvesting", "failed"},
    "transplanted": {"harvesting", "failed"},
    "harvesting": {"finished", "failed"},
    "finished": set(),
    "failed": set(),
}


class PlantingIn(BaseModel):
    crop: str = Field(min_length=1, max_length=80)
    method: Literal["direct", "transplant"]
    start_date: date
    set_out_date: date | None = None
    quantity: int | None = Field(None, ge=1, le=100000)  # blank: what the chosen cells hold, else 1
    location: str = Field("", max_length=120)
    bed_id: int | None = None
    cells: list[list[int]] = Field(default_factory=list, max_length=2500)
    ends_on: date | None = None
    notes: str = Field("", max_length=2000)

    @model_validator(mode="after")
    def dates(self) -> "PlantingIn":
        if self.method == "direct" and self.set_out_date:
            raise ValueError("a direct-sown planting has no set-out date")
        if self.method == "transplant" and (not self.set_out_date or self.set_out_date < self.start_date):
            raise ValueError("a transplant needs a set-out date on or after the sowing date")
        return self


class PlantingPatch(BaseModel):
    status: Status | None = None
    quantity: int | None = Field(None, ge=1, le=100000)
    location: str | None = Field(None, max_length=120)
    bed_id: int | None = None
    cells: list[list[int]] | None = Field(None, max_length=2500)
    ends_on: date | None = None
    notes: str | None = Field(None, max_length=2000)


def _own(db: SessionDep, household_id: int, planting_id: int) -> Planting:
    row = db.get(Planting, planting_id)
    if not row or row.household_id != household_id:
        raise HTTPException(404, "No such planting")
    return row


def _cells(bed: Bed, cells: list[list[int]]) -> list[list[int]]:
    """The cells as a clean list of [column, row] inside the bed, without repeats."""
    from .beds import grid_of

    cols, rows = grid_of(bed)
    seen: set[tuple[int, int]] = set()
    for cell in cells:
        if len(cell) != 2 or not (0 <= cell[0] < cols and 0 <= cell[1] < rows):
            raise HTTPException(422, f"Cell {cell} is outside {bed.name}")
        seen.add((cell[0], cell[1]))
    return [list(x) for x in sorted(seen, key=lambda x: (x[1], x[0]))]


def _bed(db: SessionDep, household_id: int, bed_id: int) -> Bed:
    bed = db.get(Bed, bed_id)
    if not bed or bed.household_id != household_id:
        raise HTTPException(422, "No such bed")
    return bed


@router.get("")
def list_plantings(me: MemberDep, db: SessionDep) -> list[Planting]:
    return list(db.exec(select(Planting).where(Planting.household_id == me.household_id).order_by(Planting.start_date)))


@router.post("", status_code=201)
def add_planting(body: PlantingIn, me: EditorDep, db: SessionDep, c: CatalogDep) -> Planting:
    if c.get("crop", body.crop) is None:
        raise HTTPException(422, f"No crop {body.crop!r} in the catalog")
    data = body.model_dump()
    if body.bed_id is not None:
        bed = _bed(db, me.household_id, body.bed_id)
        data["location"] = bed.name
        data["cells"] = _cells(bed, body.cells)
        if body.quantity is None:
            from .beds import crop_facts

            f = crop_facts(db, c, me.household_id, body.crop, {})
            data["quantity"] = layout.per_cell(bed.cell_cm, f["footprint"]) * max(1, len(data["cells"]))
    elif body.cells:
        raise HTTPException(422, "Cells need a bed")
    data["quantity"] = data["quantity"] or 1
    row = Planting(household_id=me.household_id, created_by=me.user_id, **data)
    db.add(row)
    db.commit()
    refresh_tasks(db, me.household_id, c)  # commits, which expires `row`
    db.refresh(row)
    return row


@router.patch("/{planting_id}")
def update_planting(planting_id: int, body: PlantingPatch, me: EditorDep, db: SessionDep, c: CatalogDep) -> Planting:
    row = _own(db, me.household_id, planting_id)
    changes = body.model_dump(exclude_unset=True)
    status = changes.pop("status", None)
    if changes.get("bed_id") is not None:
        bed = _bed(db, me.household_id, changes["bed_id"])
        changes["location"] = bed.name
        if "cells" not in changes and changes["bed_id"] != row.bed_id:
            changes["cells"] = []  # a new bed: the old cells mean nothing there
    elif "bed_id" in changes:
        changes.pop("bed_id")
        row.bed_id = None  # taken out of its bed; the free-text place stays
        changes["cells"] = []
    if changes.get("cells"):
        target = (
            _bed(db, me.household_id, changes.get("bed_id") or row.bed_id)
            if (changes.get("bed_id") or row.bed_id)
            else None
        )
        if target is None:
            raise HTTPException(422, "Cells need a bed")
        changes["cells"] = _cells(target, changes["cells"])
    elif "cells" in changes and changes["cells"] is None:
        changes.pop("cells")
    if status and status != row.status:
        if status not in NEXT[row.status]:
            raise HTTPException(409, f"A planting cannot go from {row.status} to {status}")
        if status == "transplanted" and row.method != "transplant":
            raise HTTPException(409, "Only transplants are set out")
        row.status = status
    for key, value in changes.items():
        setattr(row, key, value)
    db.add(row)
    db.commit()
    refresh_tasks(db, me.household_id, c)  # commits, which expires `row`
    db.refresh(row)
    return row


@router.delete("/{planting_id}", status_code=204)
def delete_planting(planting_id: int, me: EditorDep, db: SessionDep) -> None:
    db.delete(_own(db, me.household_id, planting_id))  # its tasks go with it (ON DELETE CASCADE)
    db.commit()


class HarvestIn(BaseModel):
    harvested_on: date
    quantity: float = Field(gt=0, le=1_000_000)
    unit: Literal["kg", "g", "count", "bunch"]
    notes: str = Field("", max_length=500)


@router.get("/harvests")
def list_harvests(me: MemberDep, db: SessionDep) -> list[Harvest]:
    return list(db.exec(select(Harvest).where(Harvest.household_id == me.household_id).order_by(Harvest.harvested_on)))


@router.post("/{planting_id}/harvests", status_code=201)
def add_harvest(planting_id: int, body: HarvestIn, me: EditorDep, db: SessionDep) -> Harvest:
    _own(db, me.household_id, planting_id)
    row = Harvest(household_id=me.household_id, planting_id=planting_id, created_by=me.user_id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/harvests/{harvest_id}", status_code=204)
def delete_harvest(harvest_id: int, me: EditorDep, db: SessionDep) -> None:
    row = db.get(Harvest, harvest_id)
    if not row or row.household_id != me.household_id:
        raise HTTPException(404, "No such harvest")
    db.delete(row)
    db.commit()
