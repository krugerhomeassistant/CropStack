"""The pantry: food that has been put by, and what to use first."""

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from ..deps import EditorDep, MemberDep, SessionDep
from ..models import PantryItem

router = APIRouter(prefix="/api/v1/pantry", tags=["pantry"])

Method = Literal["canned", "frozen", "dried", "fermented", "cellar", "fresh"]
# shortcut: one generic shelf life per method (days) when no best-before is given; storage life per crop
# (USDA AH-66 is already a registered source) replaces it when that data is added.
SHELF_DAYS: dict[str, int | None] = {
    "canned": 365,
    "frozen": 270,
    "dried": 365,
    "fermented": 180,
    "cellar": 90,
    "fresh": 7,
}
SOON_DAYS = 30


class PantryIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    method: Method
    crop: str = Field("", max_length=80)
    quantity: float = Field(gt=0, le=100000)
    unit: Literal["jars", "bags", "kg", "g", "litres", "count"]
    made_on: date
    best_before: date | None = None
    location: str = Field("", max_length=80)
    notes: str = Field("", max_length=500)


class PantryPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    quantity: float | None = Field(None, gt=0, le=100000)
    best_before: date | None = None
    location: str | None = Field(None, max_length=80)
    notes: str | None = Field(None, max_length=500)


def _view(row: PantryItem, today: date) -> dict:
    left = (row.best_before - today).days if row.best_before else None
    state = "ok" if left is None or left > SOON_DAYS else "soon" if left >= 0 else "past"
    return row.model_dump() | {"days_left": left, "state": state}


def _own(db: SessionDep, household_id: int, item_id: int) -> PantryItem:
    row = db.get(PantryItem, item_id)
    if not row or row.household_id != household_id:
        raise HTTPException(404, "No such pantry item")
    return row


@router.get("")
def list_pantry(me: MemberDep, db: SessionDep) -> list[dict]:
    """Everything put by, what to use first at the top (no date last)."""
    today = datetime.now(UTC).date()
    rows = db.exec(select(PantryItem).where(PantryItem.household_id == me.household_id)).all()
    return [
        _view(r, today) for r in sorted(rows, key=lambda r: (r.best_before is None, r.best_before or date.max, r.id))
    ]


@router.post("", status_code=201)
def add_item(body: PantryIn, me: EditorDep, db: SessionDep) -> dict:
    data = body.model_dump()
    if data["best_before"] is None and SHELF_DAYS[body.method]:
        data["best_before"] = body.made_on + timedelta(days=SHELF_DAYS[body.method])
    row = PantryItem(household_id=me.household_id, created_by=me.user_id, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _view(row, datetime.now(UTC).date())


@router.patch("/{item_id}")
def update_item(item_id: int, body: PantryPatch, me: EditorDep, db: SessionDep) -> dict:
    row = _own(db, me.household_id, item_id)
    for key, value in body.model_dump(exclude_unset=True).items():
        if value is not None or key == "best_before":
            setattr(row, key, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return _view(row, datetime.now(UTC).date())


@router.delete("/{item_id}", status_code=204)
def delete_item(item_id: int, me: EditorDep, db: SessionDep) -> None:
    db.delete(_own(db, me.household_id, item_id))
    db.commit()
