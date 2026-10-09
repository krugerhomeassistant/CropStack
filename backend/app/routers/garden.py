"""The household's site (garden location and frost-risk preference), its climate, and place search."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .. import climate, external
from ..deps import MemberDep, OwnerDep, SessionDep, UserDep
from ..models import ClimateCache, Site, now

router = APIRouter(prefix="/api/v1", tags=["site"])


class GardenIn(BaseModel):
    name: str = Field("My garden", min_length=1, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    postal_code: str = Field("", max_length=16)
    frost_probability: int = Field(50, ge=10, le=90)


# shortcut: one site per household, addressed as "current" until the multi-site UI exists (SPEC 4.1).
@router.get("/sites/current")
def get_garden(me: MemberDep, db: SessionDep) -> Site:
    return _site(me.household_id, db)


def _site(household_id: int, db: Session) -> Site:
    site = db.exec(select(Site).where(Site.household_id == household_id)).first()
    if not site:
        raise HTTPException(404, "No garden yet")
    return site


@router.put("/sites/current")
def save_garden(body: GardenIn, owner: OwnerDep, db: SessionDep) -> Site:
    site = db.exec(select(Site).where(Site.household_id == owner.household_id)).first() or Site(
        household_id=owner.household_id, latitude=body.latitude, longitude=body.longitude
    )
    site.sqlmodel_update(body.model_dump() | {"updated_at": now()})
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("/sites/current/climate")
def get_climate(me: MemberDep, db: SessionDep) -> dict:
    """Frost dates, zone and monthly normals for the site; fetched once per location, then cached."""
    site = _site(me.household_id, db)
    cache = db.get(ClimateCache, site.id)
    stale = not cache or cache.summary.get("version") != climate.SUMMARY_VERSION
    if stale or (cache.latitude, cache.longitude) != (site.latitude, site.longitude):
        try:
            summary = climate.summarize(external.fetch_climate_archive(site.latitude, site.longitude))
        except external.ExternalError as e:
            raise HTTPException(502, f"Climate data unavailable: {e}") from e
        cache = cache or ClimateCache(site_id=site.id, latitude=site.latitude, longitude=site.longitude, summary={})
        cache.sqlmodel_update(
            {"latitude": site.latitude, "longitude": site.longitude, "summary": summary, "fetched_at": now()}
        )
        db.add(cache)
        db.commit()
    return climate.report(cache.summary, site.latitude, site.frost_probability) | {
        "fetched_at": cache.fetched_at,
        "source": "Open-Meteo.com (ERA5 / ERA5-Land, CC BY 4.0)",
    }


@router.get("/places")
def search_places(_: UserDep, q: str = Query(min_length=2, max_length=120)) -> list[dict]:
    try:
        return external.search_places(q)
    except external.ExternalError as e:
        raise HTTPException(502, f"Place search unavailable: {e}") from e
