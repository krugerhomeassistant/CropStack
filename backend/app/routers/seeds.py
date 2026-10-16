"""Seeds the household has: the year plan favours these crops and lists the seed still to buy."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from ..deps import EditorDep, MemberDep, SessionDep
from ..models import Seed
from .catalog import CatalogDep

router = APIRouter(prefix="/api/v1/seeds", tags=["seeds"])


class SeedsIn(BaseModel):
    crops: list[str] = Field(max_length=500)


def owned(db: SessionDep, household_id: int) -> set[str]:
    return set(db.exec(select(Seed.crop).where(Seed.household_id == household_id)).all())


@router.get("")
def list_seeds(me: MemberDep, db: SessionDep) -> list[str]:
    return sorted(owned(db, me.household_id))


@router.put("")
def set_seeds(body: SeedsIn, me: EditorDep, db: SessionDep, c: CatalogDep) -> list[str]:
    """Replace the whole list: the crops the household has seed for."""
    want = set(body.crops)
    if bad := sorted(s for s in want if c.get("crop", s) is None):
        raise HTTPException(422, f"No crop {bad[0]!r} in the catalog")
    have = {s.crop: s for s in db.exec(select(Seed).where(Seed.household_id == me.household_id))}
    for crop, row in have.items():
        if crop not in want:
            db.delete(row)
    for crop in want - have.keys():
        db.add(Seed(household_id=me.household_id, crop=crop))
    db.commit()
    return sorted(want)
