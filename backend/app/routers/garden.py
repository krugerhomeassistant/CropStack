"""The user's garden profile (location and frost-risk preference)."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .. import climate, external
from ..deps import SessionDep, UserDep
from ..models import ClimateCache, Garden, now

router = APIRouter(prefix="/api", tags=["garden"])


class GardenIn(BaseModel):
    name: str = Field("My garden", min_length=1, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    postal_code: str = Field("", max_length=16)
    frost_probability: int = Field(50, ge=10, le=90)


@router.get("/garden")
def get_garden(user: UserDep, db: SessionDep) -> Garden:
    return _garden(user.id, db)


def _garden(user_id: int | None, db: Session) -> Garden:
    garden = db.exec(select(Garden).where(Garden.user_id == user_id)).first()
    if not garden:
        raise HTTPException(404, "No garden yet")
    return garden


@router.put("/garden")
def save_garden(body: GardenIn, user: UserDep, db: SessionDep) -> Garden:
    garden = db.exec(select(Garden).where(Garden.user_id == user.id)).first() or Garden(
        user_id=user.id, latitude=body.latitude, longitude=body.longitude
    )
    garden.sqlmodel_update(body.model_dump() | {"updated_at": now()})
    db.add(garden)
    db.commit()
    db.refresh(garden)
    return garden


@router.get("/garden/climate")
def get_climate(user: UserDep, db: SessionDep) -> dict:
    """Frost dates, zone and monthly normals for the garden; fetched once per location, then cached."""
    garden = _garden(user.id, db)
    cache = db.get(ClimateCache, garden.id)
    if not cache or (cache.latitude, cache.longitude) != (garden.latitude, garden.longitude):
        try:
            summary = climate.summarize(external.fetch_climate_archive(garden.latitude, garden.longitude))
        except external.ExternalError as e:
            raise HTTPException(502, f"Climate data unavailable: {e}") from e
        cache = cache or ClimateCache(
            garden_id=garden.id, latitude=garden.latitude, longitude=garden.longitude, summary={}
        )
        cache.sqlmodel_update(
            {"latitude": garden.latitude, "longitude": garden.longitude, "summary": summary, "fetched_at": now()}
        )
        db.add(cache)
        db.commit()
    return climate.report(cache.summary, garden.latitude, garden.frost_probability) | {
        "fetched_at": cache.fetched_at,
        "source": "Open-Meteo.com (ERA5 / ERA5-Land, CC BY 4.0)",
    }


@router.get("/places")
def search_places(_: UserDep, q: str = Query(min_length=2, max_length=120)) -> list[dict]:
    try:
        return external.search_places(q)
    except external.ExternalError as e:
        raise HTTPException(502, f"Place search unavailable: {e}") from e
