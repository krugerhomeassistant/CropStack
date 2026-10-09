"""Calls to outside services: Open-Meteo (climate archive) and OpenStreetMap Nominatim (place search).

Both are free for non-commercial self-hosting; the app shows their attribution where their data appears.
"""

from datetime import date

import httpx

from . import VERSION

USER_AGENT = f"CropStack/{VERSION} (+https://github.com/krugerhomeassistant/CropStack)"  # Nominatim requires one
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CLIMATE_YEARS = 30
# Open-Meteo daily variable -> environment engine name. Seven variables: still one weighted request (≤ 10).
ARCHIVE_VARIABLES = {
    "temperature_2m_min": "tmin",
    "temperature_2m_max": "tmax",
    "soil_temperature_0_to_7cm_mean": "soil_t",
    "precipitation_sum": "precip",
    "et0_fao_evapotranspiration": "et0",
    "relative_humidity_2m_mean": "rh",
    "wind_speed_10m_max": "wind",
}


class ExternalError(Exception):
    """An outside service failed or refused; the message is safe to show to the user."""


def _get(url: str, params: dict, timeout: float) -> httpx.Response:
    try:
        resp = httpx.get(url, params=params, headers={"User-Agent": USER_AGENT}, timeout=timeout)
    except httpx.HTTPError as e:
        raise ExternalError(f"Could not reach {httpx.URL(url).host}: {e.__class__.__name__}") from e
    if resp.status_code != 200:
        try:
            reason = resp.json().get("reason", resp.reason_phrase)  # Open-Meteo errors are {"error", "reason"}
        except ValueError:
            reason = resp.reason_phrase
        raise ExternalError(f"{httpx.URL(url).host} answered {resp.status_code}: {reason}")
    return resp


def fetch_climate_archive(latitude: float, longitude: float, today: date | None = None) -> dict:
    """Daily weather (ARCHIVE_VARIABLES) for the last CLIMATE_YEARS complete years.

    Cost: ~800 of Open-Meteo's 10,000 free daily calls (long ranges are weighted), so callers must cache.
    """
    end_year = (today or date.today()).year - 1
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": f"{end_year - CLIMATE_YEARS + 1}-01-01",
        "end_date": f"{end_year}-12-31",
        "daily": ",".join(ARCHIVE_VARIABLES),
        "timezone": "auto",
        "models": "era5_seamless",  # ERA5-Land (~11 km) where available, ERA5 (~25 km) elsewhere, e.g. coasts
    }
    return _get(ARCHIVE_URL, params, timeout=90).json()


FORECAST_VARIABLES = ARCHIVE_VARIABLES | {"precipitation_probability_max": "precip_prob", "weather_code": "code"}
FORECAST_DAYS, PAST_DAYS = 16, 92  # Open-Meteo maximums


def fetch_forecast(latitude: float, longitude: float) -> dict:
    """Daily weather for the past 92 days (observed/analysis) and the next 16 days (forecast), local time.

    Cost: ~8 weighted calls (108 days, 9 variables), so a refresh every 3 hours stays far inside the free tier.
    Soil temperature falls back from 0-7 cm to 0-10 cm depending on the forecast model."""
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join(FORECAST_VARIABLES),
        "timezone": "auto",
        "past_days": PAST_DAYS,
        "forecast_days": FORECAST_DAYS,
    }
    return _get(FORECAST_URL, params, timeout=30).json()


def search_places(query: str, limit: int = 5) -> list[dict]:
    """Place names, addresses or postal codes → candidate locations."""
    params = {"q": query, "format": "jsonv2", "limit": limit, "addressdetails": 1}
    results = _get(NOMINATIM_URL, params, timeout=15).json()
    return [
        {
            "label": r["display_name"],
            "latitude": round(float(r["lat"]), 4),
            "longitude": round(float(r["lon"]), 4),
            "postal_code": r.get("address", {}).get("postcode", ""),
        }
        for r in results
    ]
