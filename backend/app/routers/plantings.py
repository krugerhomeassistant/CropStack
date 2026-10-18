"""Plantings: what the household has sown or plans to sow (SPEC §6.2)."""

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlmodel import select

from .. import catalog as cat
from ..deps import EditorDep, MemberDep, SessionDep
from ..engine import layout
from ..models import Bed, Harvest, Planting, Task
from .catalog import CatalogDep
from .today import refresh_tasks

router = APIRouter(prefix="/api/v1/plantings", tags=["plantings"])

Status = Literal["planned", "sown", "germinated", "transplanted", "harvesting", "finished", "failed"]


class PlantingIn(BaseModel):
    crop: str = Field(min_length=1, max_length=80)
    method: Literal["direct", "transplant"]
    start_date: date
    set_out_date: date | None = None
    quantity: int | None = Field(None, ge=1, le=100000)  # blank: what the chosen cells hold, else 1
    location: str = Field("", max_length=120)
    bed_id: int | None = None
    cells: list[list[int]] = Field(default_factory=list, max_length=2500)
    spots: list[list[int]] = Field(default_factory=list, max_length=2500)  # [x, y, w, h] cm; blank: laid out from cells
    ends_on: date | None = None
    notes: str = Field("", max_length=2000)
    in_ground: bool = False  # logged as done even when dated today

    @model_validator(mode="after")
    def dates(self) -> "PlantingIn":
        if self.method == "direct" and self.set_out_date:
            raise ValueError("a direct-sown planting has no set-out date")
        if self.method == "transplant" and (not self.set_out_date or self.set_out_date < self.start_date):
            raise ValueError("a transplant needs a set-out date on or after the sowing date")
        return self


class PlantingPatch(BaseModel):
    status: Status | None = None
    start_date: date | None = None
    set_out_date: date | None = None
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


def _cells(cells: list[list[int]]) -> list[list[int]]:
    """The cells as a clean list of [column, row], without repeats. Never refused for lying outside the bed's
    grid: a bed that was resized keeps what grew there, and the grid shows those cells as outside."""
    seen: set[tuple[int, int]] = set()
    for cell in cells:
        if len(cell) != 2 or min(cell) < 0:
            raise HTTPException(422, f"Cell {cell} is not a cell")
        seen.add((cell[0], cell[1]))
    return [list(x) for x in sorted(seen, key=lambda x: (x[1], x[0]))]


def _spots(spots: list[list[int]]) -> list[list[int]]:
    for s in spots:
        if len(s) != 4 or min(s) < 0 or s[2] < 1 or s[3] < 1:
            raise HTTPException(422, f"Spot {s} is not a plant's place")
    return spots


def _bed(db: SessionDep, household_id: int, bed_id: int) -> Bed:
    bed = db.get(Bed, bed_id)
    if not bed or bed.household_id != household_id:
        raise HTTPException(422, "No such bed")
    return bed


def _place(
    db: SessionDep, c: CatalogDep, household_id: int, bed: Bed, crop: str, cells, first: date, last: date | None,
    keep=(), skip: int | None = None, limit: int = layout.MAX_CELLS,
) -> list[list[int]]:  # fmt: skip
    """The plants for painted `cells` of a bed: `keep` stay as they are and new ones are laid out at the crop's real
    spacing round the other plantings that hold the ground in that time."""
    from .beds import cm, crop_facts, ground_taken

    f = crop_facts(db, c, household_id, crop, {})
    last = last or first + timedelta(days=round(f["cycle_days"] or layout.DEFAULT_CYCLE_DAYS))
    avoid = [*ground_taken(db, c, household_id, bed, first, last, skip), *map(tuple, keep)]
    return [*map(list, keep), *map(list, layout.fill(cells, bed.cell_cm, *cm(bed), f["dims"], avoid, limit))]


def _view(row: Planting, c: CatalogDep) -> dict:
    item = cat.effective(c, "crop", row.crop, {})
    return row.model_dump() | {"purpose": item.get("purpose", "food") if item else "food"}


def outlook(db: SessionDep, household_id: int) -> dict[int, dict]:
    """Per planting: when its harvest is expected (from its harvest job) and its next open job."""
    out: dict[int, dict] = {}
    tasks = db.exec(
        select(Task).where(Task.household_id == household_id, Task.planting_id.is_not(None)).order_by(Task.ideal)  # type: ignore[union-attr]
    ).all()
    for t in tasks:
        o = out.setdefault(t.planting_id, {"harvest_from": None, "harvest_to": None, "next_job": None})
        if t.kind == "harvest":
            o["harvest_from"], o["harvest_to"] = t.earliest, t.latest
        if t.status == "open" and o["next_job"] is None and t.kind not in ("check", "water"):
            o["next_job"] = {"title": t.title, "date": t.ideal}
    return out


@router.get("")
def list_plantings(me: MemberDep, db: SessionDep, c: CatalogDep) -> list[dict]:
    """Every planting, with its expected harvest and next job."""
    rows = db.exec(select(Planting).where(Planting.household_id == me.household_id).order_by(Planting.start_date))
    ahead = outlook(db, me.household_id)
    empty = {"harvest_from": None, "harvest_to": None, "next_job": None}
    return [_view(p, c) | ahead.get(p.id, empty) for p in rows]


def make_planting(body: PlantingIn, me: EditorDep, db: SessionDep, c: CatalogDep) -> Planting:
    """A Planting row for `body`, added to the session but not committed."""
    if c.get("crop", body.crop) is None:
        raise HTTPException(422, f"No crop {body.crop!r} in the catalog")
    data = body.model_dump(exclude={"in_ground"})
    if body.bed_id is not None:
        bed = _bed(db, me.household_id, body.bed_id)
        data["location"] = bed.name
        data["cells"] = _cells(body.cells)
        first = body.set_out_date or body.start_date
        spots = _spots(body.spots) or _place(
            db, c, me.household_id, bed, body.crop, data["cells"], first, body.ends_on, limit=body.quantity or layout.MAX_CELLS
        )  # fmt: skip
        if spots:  # the cells hold exactly the ground these plants take
            data["spots"], data["cells"], data["quantity"] = spots, layout.cover(spots, bed.cell_cm), len(spots)
    elif body.cells:
        raise HTTPException(422, "Cells need a bed")
    data["quantity"] = data["quantity"] or 1
    # Already in the ground: a planting dated in the past starts as sown (or set out), so no overdue sowing job appears.
    today = datetime.now(UTC).date()
    # `in_ground` is for a planting logged today (painted into a bed); a plan made for today is still to do.
    reached = (lambda d: d <= today) if body.in_ground else (lambda d: d < today)
    if body.method == "transplant" and body.set_out_date and reached(body.set_out_date):
        data["status"] = "transplanted"
    elif reached(body.start_date):
        data["status"] = "sown"
    return Planting(household_id=me.household_id, created_by=me.user_id, **data)


@router.post("", status_code=201)
def add_planting(body: PlantingIn, me: EditorDep, db: SessionDep, c: CatalogDep) -> dict:
    row = make_planting(body, me, db, c)
    db.add(row)
    db.commit()
    refresh_tasks(db, me.household_id, c)  # commits, which expires `row`
    db.refresh(row)
    return _view(row, c)


@router.patch("/{planting_id}")
def update_planting(planting_id: int, body: PlantingPatch, me: EditorDep, db: SessionDep, c: CatalogDep) -> Planting:
    row = _own(db, me.household_id, planting_id)
    changes = body.model_dump(exclude_unset=True)
    status = changes.pop("status", None)
    if changes.get("quantity") is None:
        changes.pop("quantity", None)  # a count cannot be cleared
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
        if not (changes.get("bed_id") or row.bed_id):
            raise HTTPException(422, "Cells need a bed")
        changes["cells"] = _cells(changes["cells"])
        bed = _bed(db, me.household_id, changes.get("bed_id") or row.bed_id)
        from .beds import crop_facts, spots_of

        # Plants already there keep their place and size; only the newly painted cells get new ones.
        same = bed.id == row.bed_id
        painted = {tuple(x) for x in changes["cells"]}
        keep = [
            s for s in (spots_of(row, bed, crop_facts(db, c, me.household_id, row.crop, {})["dims"]) if same else [])
            if (( s[0] + s[2] // 2) // bed.cell_cm, (s[1] + s[3] // 2) // bed.cell_cm) in painted
        ]  # fmt: skip
        fresh = painted - ({tuple(x) for x in row.cells} if same else set())
        first = changes.get("set_out_date") or row.set_out_date or changes.get("start_date") or row.start_date
        spots = _place(db, c, me.household_id, bed, row.crop, fresh, first, row.ends_on, keep, row.id)
        if spots:
            changes["spots"], changes["cells"] = spots, layout.cover(spots, bed.cell_cm)
            changes.setdefault("quantity", len(spots))
    elif "cells" in changes and changes["cells"] is None:
        changes.pop("cells")
    if changes.get("cells") == []:
        changes["spots"] = []
    if status and status != row.status:
        if status == "transplanted" and row.method != "transplant":
            raise HTTPException(409, "Only transplants are set out")
        row.status = status
    for key, value in changes.items():
        if key == "start_date" and value is None:
            continue  # the sowing date cannot be cleared
        setattr(row, key, value)
    if row.method == "transplant" and (not row.set_out_date or row.set_out_date < row.start_date):
        db.rollback()
        raise HTTPException(422, "A transplant needs a set-out date on or after the sowing date")
    if row.method == "direct":
        row.set_out_date = None
    db.add(row)
    db.commit()
    refresh_tasks(db, me.household_id, c)  # commits, which expires `row`
    db.refresh(row)
    return _view(row, c)


@router.post("/{planting_id}/place")
def place_planting(planting_id: int, me: EditorDep, db: SessionDep, c: CatalogDep) -> Planting:
    """Give a planting that stands nowhere on its bed's grid (made before plants had places) its plants, in the free
    ground of that bed at the crop's real spacing."""
    from .beds import grid_of

    row = _own(db, me.household_id, planting_id)
    bed = db.get(Bed, row.bed_id) if row.bed_id else None
    if bed is None:
        raise HTTPException(422, "Put the planting in a bed first")
    cols, rows = grid_of(bed)
    everywhere = [(x, y) for x in range(cols) for y in range(rows)]
    first = row.set_out_date or row.start_date
    spots = _place(
        db, c, me.household_id, bed, row.crop, everywhere, first, row.ends_on, skip=row.id, limit=row.quantity
    )
    if not spots:
        raise HTTPException(409, "There is no free room for it in this bed")
    row.spots, row.cells = spots, layout.cover(spots, bed.cell_cm)
    db.add(row)
    db.commit()
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
