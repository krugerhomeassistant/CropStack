"""Recent and coming weather for a site, described against its own climate (SPEC §4.3, §4.4). Pure functions."""

from datetime import date, timedelta

from . import environment as env
from .external import FORECAST_VARIABLES


def daily_rows(raw: dict) -> list[dict]:
    """Open-Meteo daily arrays → one dict per day with engine names (tmin, tmax, precip, precip_prob, …)."""
    daily = raw["daily"]
    names = {key: name for key, name in FORECAST_VARIABLES.items() if key in daily}
    return [{"date": day} | {name: daily[key][i] for key, name in names.items()} for i, day in enumerate(daily["time"])]


def split(rows: list[dict], today: date) -> tuple[list[dict], list[dict]]:
    """(days before today, today and later)."""
    iso = today.isoformat()
    return [r for r in rows if r["date"] < iso], [r for r in rows if r["date"] >= iso]


def anomaly(c: env.Climatology, past: list[dict], today: date, days: int = 30) -> dict | None:
    """The last `days` days against the same days in the site's climate: temperature difference and where the
    rain total ranks among past years. None when too few observed days are available."""
    window = [r for r in past if r["date"] >= (today - timedelta(days=days)).isoformat()]
    temps = [(r["tmin"] + r["tmax"]) / 2 for r in window if r.get("tmin") is not None and r.get("tmax") is not None]
    if len(temps) < 0.8 * days:
        return None
    start = env.doy(today - timedelta(days=days))
    mins, maxs = env.windows(c, "tmin", start, days), env.windows(c, "tmax", start, days)
    normal = 0.0
    for (lo, w), (hi, _) in zip(mins, maxs, strict=True):
        pairs = [(a + b) / 2 for a, b in zip(lo, hi, strict=True) if a is not None and b is not None]
        normal += w * sum(pairs) / len(pairs)
    observed_rain = sum(r.get("precip") or 0.0 for r in window)
    rain_years = env.per_year(c, "precip", start, days, lambda v: sum(x or 0.0 for x in v))
    below = sum(w for v, w in rain_years if v < observed_rain) + sum(w for v, w in rain_years if v == observed_rain) / 2
    return {
        "days": days,
        "temp_diff_c": round(sum(temps) / len(temps) - normal, 1),
        "rain_mm": round(observed_rain, 1),
        "rain_normal_mm": round(env.weighted_quantile(rain_years, 0.5), 1),
        "rain_percentile": round(100 * below),  # 50 = a typical month; 90 = wetter than 9 in 10 years
    }
