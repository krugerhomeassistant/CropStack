"""Flocks of animals (hens first), where they live, and the eggs they lay."""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from ..deps import EditorDep, MemberDep, SessionDep
from ..models import Bed, EggLog, Flock

router = APIRouter(prefix="/api/v1/flocks", tags=["flocks"])

# shortcut: one rule-of-thumb floor area per hen (m², estimate, common extension guidance: about 4 sq ft in the coop and
# 10 sq ft in the run); replace with catalog species data (cited, per breed size) when species are added.
COOP_M2_PER_HEN = 0.4
RUN_M2_PER_HEN = 1.0
WEEK = 7


class FlockIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    species: str = Field("hen", max_length=40)
    breed: str = Field("", max_length=60)
    count: int = Field(1, ge=1, le=10000)
    got_on: date
    coop_id: int | None = None
    notes: str = Field("", max_length=500)


class FlockPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=60)
    breed: str | None = Field(None, max_length=60)
    count: int | None = Field(None, ge=1, le=10000)
    coop_id: int | None = None
    notes: str | None = Field(None, max_length=500)


class EggsIn(BaseModel):
    laid_on: date
    count: int = Field(ge=0, le=100000)


def _own(db: SessionDep, household_id: int, flock_id: int) -> Flock:
    row = db.get(Flock, flock_id)
    if not row or row.household_id != household_id:
        raise HTTPException(404, "No such flock")
    return row


def _coop(db: SessionDep, household_id: int, coop_id: int | None) -> Bed | None:
    if coop_id is None:
        return None
    bed = db.get(Bed, coop_id)
    if not bed or bed.household_id != household_id or bed.kind != "coop":
        raise HTTPException(422, "That is not a coop")
    return bed


def _view(db: SessionDep, row: Flock, today: date) -> dict:
    coop = db.get(Bed, row.coop_id) if row.coop_id else None
    eggs = db.exec(select(EggLog).where(EggLog.flock_id == row.id, EggLog.laid_on > today - timedelta(days=WEEK))).all()
    area = coop.width * coop.length if coop else None
    return row.model_dump() | {
        "coop": coop.name if coop else None,
        "coop_m2": round(area, 1) if area else None,
        "wanted_m2": round(row.count * (COOP_M2_PER_HEN + RUN_M2_PER_HEN), 1),  # a suggestion, never a limit
        "eggs_week": sum(e.count for e in eggs),
        "eggs_today": next((e.count for e in eggs if e.laid_on == today), None),
        "per_hen_day": round(sum(e.count for e in eggs) / (row.count * WEEK), 2),
    }


@router.get("")
def list_flocks(me: MemberDep, db: SessionDep) -> list[dict]:
    today = datetime.now(UTC).date()
    rows = db.exec(select(Flock).where(Flock.household_id == me.household_id).order_by(Flock.id)).all()
    return [_view(db, r, today) for r in rows]


@router.post("", status_code=201)
def add_flock(body: FlockIn, me: EditorDep, db: SessionDep) -> dict:
    _coop(db, me.household_id, body.coop_id)
    row = Flock(household_id=me.household_id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _view(db, row, datetime.now(UTC).date())


@router.patch("/{flock_id}")
def update_flock(flock_id: int, body: FlockPatch, me: EditorDep, db: SessionDep) -> dict:
    row = _own(db, me.household_id, flock_id)
    changes = body.model_dump(exclude_unset=True)
    if "coop_id" in changes:
        _coop(db, me.household_id, changes["coop_id"])
    for k, v in changes.items():
        setattr(row, k, v)
    db.add(row)
    db.commit()
    return _view(db, row, datetime.now(UTC).date())


@router.post("/{flock_id}/eggs")
def log_eggs(flock_id: int, body: EggsIn, me: EditorDep, db: SessionDep) -> dict:
    """Eggs for a day; logging the same day again replaces the number."""
    row = _own(db, me.household_id, flock_id)
    log = db.exec(select(EggLog).where(EggLog.flock_id == flock_id, EggLog.laid_on == body.laid_on)).first()
    if log is None:
        log = EggLog(household_id=me.household_id, flock_id=flock_id, laid_on=body.laid_on, count=body.count)
    log.count = body.count
    db.add(log)
    db.commit()
    return _view(db, row, datetime.now(UTC).date())


@router.delete("/{flock_id}", status_code=204)
def delete_flock(flock_id: int, me: EditorDep, db: SessionDep) -> None:
    db.delete(_own(db, me.household_id, flock_id))  # its egg log goes with it
    db.commit()
