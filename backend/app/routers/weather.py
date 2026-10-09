"""Coming and recent weather for the household's site (SPEC §4.3, §4.4), refreshed in the background."""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

from .. import external, scheduler, weather
from ..db import get_engine
from ..deps import MemberDep, SessionDep
from ..models import Forecast, Household, Site, now
from .garden import _archive, _climatology, _site
from .household import household_settings

router = APIRouter(prefix="/api/v1", tags=["weather"])

MAX_AGE = timedelta(hours=3)
SOURCE = "Open-Meteo.com (forecast, CC BY 4.0)"


def refresh_forecast(site: Site, db: Session) -> tuple[Forecast | None, bool]:
    """(forecast, stale): refetch when missing, moved or older than MAX_AGE; on failure keep the old one."""
    fc = db.get(Forecast, site.id)
    same_place = fc is not None and (fc.latitude, fc.longitude) == (site.latitude, site.longitude)
    if fc and same_place and now() - fc.fetched_at < MAX_AGE:
        return fc, False
    try:
        raw = external.fetch_forecast(site.latitude, site.longitude)
    except external.ExternalError:
        if fc and same_place:
            return fc, True
        raise
    values = {"latitude": site.latitude, "longitude": site.longitude, "raw": raw, "fetched_at": now()}
    fc = fc or Forecast(site_id=site.id, **values)
    fc.sqlmodel_update(values)
    db.add(fc)
    db.commit()
    db.refresh(fc)
    return fc, False


@scheduler.job("forecast", every=timedelta(minutes=30))
def refresh_all() -> None:
    """Keep every site's forecast at most ~3 hours old, so Today opens instantly."""
    with Session(get_engine()) as db:
        sites = db.exec(select(Site)).all()
        for site in sites:
            household = db.get(Household, site.household_id)
            if household and household_settings(household).forecast:
                refresh_forecast(site, db)


def local_today(raw: dict) -> date:
    """Today at the site (Open-Meteo reports the site's UTC offset with timezone=auto)."""
    return (datetime.now(UTC) + timedelta(seconds=raw.get("utc_offset_seconds", 0))).date()


@router.get("/sites/current/weather")
def get_weather(me: MemberDep, db: SessionDep) -> dict:
    household = db.get(Household, me.household_id)
    if not household or not household_settings(household).forecast:
        raise HTTPException(409, "The forecast is turned off (More → Settings → Data sources)")
    site = _site(me.household_id, db)
    try:
        fc, stale = refresh_forecast(site, db)
    except external.ExternalError as e:
        raise HTTPException(502, f"Forecast unavailable: {e}") from e
    assert fc
    today = local_today(fc.raw)
    past, future = weather.split(weather.daily_rows(fc.raw), today)
    try:  # the comparison with normal needs the climate record; the forecast itself doesn't
        anomaly = weather.anomaly(_climatology(_archive(site, db)), past, today)
    except HTTPException:
        anomaly = None
    return {
        "today": future[0] if future else None,
        "days": future,
        "recent": anomaly,
        "timezone": fc.raw.get("timezone"),
        "fetched_at": fc.fetched_at,
        "stale": stale,
        "source": SOURCE,
    }
