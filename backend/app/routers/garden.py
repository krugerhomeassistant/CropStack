"""The user's garden profile (location and frost-risk preference)."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import select

from ..deps import SessionDep, UserDep
from ..models import Garden, now

router = APIRouter(prefix="/api/garden", tags=["garden"])


class GardenIn(BaseModel):
    name: str = Field("My garden", min_length=1, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    postal_code: str = Field("", max_length=16)
    frost_probability: int = Field(50, ge=10, le=90)


@router.get("")
def get_garden(user: UserDep, db: SessionDep) -> Garden:
    garden = db.exec(select(Garden).where(Garden.user_id == user.id)).first()
    if not garden:
        raise HTTPException(404, "No garden yet")
    return garden


@router.put("")
def save_garden(body: GardenIn, user: UserDep, db: SessionDep) -> Garden:
    garden = db.exec(select(Garden).where(Garden.user_id == user.id)).first() or Garden(
        user_id=user.id, latitude=body.latitude, longitude=body.longitude
    )
    garden.sqlmodel_update(body.model_dump() | {"updated_at": now()})
    db.add(garden)
    db.commit()
    db.refresh(garden)
    return garden
