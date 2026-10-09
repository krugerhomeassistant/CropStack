"""The household's site (garden location and frost-risk preference), its climate, and place search."""

from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from .. import climate, external
from .. import environment as env
from ..catalog import effective
from ..deps import MemberDep, OwnerDep, SessionDep
from ..engine import phenology, windows
from ..models import ClimateArchive, Household, Site, now
from .catalog import CatalogDep, _overrides

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


ARCHIVE_VERSION = 1  # bump when external.ARCHIVE_VARIABLES changes: stored archives are then refetched
SOURCE = "Open-Meteo.com (ERA5 / ERA5-Land, CC BY 4.0)"
EngineVar = Literal["tmin", "tmax", "soil_t", "precip", "et0", "rh", "wind"]


def _archive(site: Site, db: Session) -> ClimateArchive:
    """The site's daily record; refetched when the site moved, a newer complete year exists, or the format changed."""
    archive = db.get(ClimateArchive, site.id)
    same_place = archive is not None and (archive.latitude, archive.longitude) == (site.latitude, site.longitude)
    if archive and same_place and archive.version == ARCHIVE_VERSION and archive.last_year >= date.today().year - 1:
        return archive
    try:
        raw = external.fetch_climate_archive(site.latitude, site.longitude)
    except external.ExternalError as e:
        if archive and same_place:
            return archive  # last year's record still answers everything; refresh again on a later visit
        raise HTTPException(502, f"Climate data unavailable: {e}") from e
    values = {
        "latitude": site.latitude,
        "longitude": site.longitude,
        "version": ARCHIVE_VERSION,
        "last_year": int(raw["daily"]["time"][-1][:4]),
        "raw": raw,
        "fetched_at": now(),
    }
    archive = archive or ClimateArchive(site_id=site.id, **values)
    archive.sqlmodel_update(values)
    db.add(archive)
    db.commit()
    db.refresh(archive)
    return archive


# shortcut: per-process cache of built climatologies (one uvicorn worker); keyed by fetch time so a refetch
# rebuilds. Move to a shared cache if the app ever runs several workers.
_BUILT: dict[tuple[int, str], env.Climatology] = {}


def _climatology(archive: ClimateArchive) -> env.Climatology:
    key = (archive.site_id, archive.fetched_at.isoformat())
    if key not in _BUILT:
        if len(_BUILT) >= 16:
            _BUILT.pop(next(iter(_BUILT)))
        _BUILT[key] = env.from_open_meteo(archive.raw)
    return _BUILT[key]


@router.get("/sites/current/climate")
def get_climate(me: MemberDep, db: SessionDep) -> dict:
    """Climate summary for the site's card (frost dates, zone, monthly normals, rain, daylight)."""
    site = _site(me.household_id, db)
    archive = _archive(site, db)
    trends = _climatology(archive).trends
    return climate.report(climate.summarize(archive.raw), site.latitude, site.frost_probability, trends) | {
        "fetched_at": archive.fetched_at,
        "source": SOURCE,
    }


@router.get("/sites/current/climate/probability")
def climate_probability(
    me: MemberDep,
    db: SessionDep,
    var: EngineVar,
    x: float,
    op: Literal["le", "lt", "ge", "gt"] = "le",
) -> dict:
    """Chance, for each day of the year, that `var` is `op` `x` (e.g. tmin le 0 = a night at or below 0 °C)."""
    c = _climatology(_archive(_site(me.household_id, db), db))
    return {
        "var": var,
        "op": op,
        "x": x,
        "days": [round(p, 3) for p in env.daily_prob(c, var, op, x)],
        "years": f"{c.years[0]}-{c.years[-1]}",
        "source": SOURCE,
    }


@router.get("/sites/current/climate/bands")
def climate_bands(me: MemberDep, db: SessionDep, var: EngineVar) -> dict:
    """10th, 50th and 90th percentile of `var` for each day of the year (charts)."""
    c = _climatology(_archive(_site(me.household_id, db), db))
    rows = env.daily_quantiles(c, var, (0.1, 0.5, 0.9))
    r = lambda v: None if v is None else round(v, 2)  # noqa: E731
    return {
        "var": var,
        "p10": [r(row[0]) for row in rows],
        "p50": [r(row[1]) for row in rows],
        "p90": [r(row[2]) for row in rows],
        "trend_per_decade": round(c.trends[var] * 10, 2) if var in c.trends else None,
        "years": f"{c.years[0]}-{c.years[-1]}",
        "source": SOURCE,
    }


@router.get("/places")
def search_places(me: MemberDep, db: SessionDep, q: str = Query(min_length=2, max_length=120)) -> list[dict]:
    from .household import household_settings  # household imports nothing from here; avoid a cycle at import time

    household = db.get(Household, me.household_id)
    if household and not household_settings(household).place_search:
        raise HTTPException(409, "Place search is turned off (More → Settings → Data sources)")
    try:
        return external.search_places(q)
    except external.ExternalError as e:
        raise HTTPException(502, f"Place search unavailable: {e}") from e


@router.get("/crops/{slug}/windows")
def crop_windows(slug: str, me: MemberDep, db: SessionDep, c: CatalogDep) -> dict:
    """When this crop can be direct-sown at the household's site, from its requirements and the local climate."""
    item = effective(c, "crop", slug, _overrides(db, me.household_id, "crop", slug))
    if item is None:
        raise HTTPException(404, f"No crop {slug!r} in the catalog")
    site = _site(me.household_id, db)
    profile = phenology.profile_from_item(item)
    if not profile.usable:
        return {"slug": slug, "usable": False, "missing": list(profile.missing)}
    threshold = windows.success_threshold(site.frost_probability)
    result = windows.analyse(_climatology(_archive(site, db)), profile, threshold)
    return {
        "slug": slug,
        "usable": True,
        "estimates": list(profile.estimates),
        **result,
    }
