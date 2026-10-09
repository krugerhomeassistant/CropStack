"""Local climate from ~30 years of daily reanalysis data: frost dates, hardiness zone, daylight, monthly normals.

Pure functions only (no I/O); `external.py` fetches the data. Works in both hemispheres: frost statistics
are computed per *season-year* that starts at the climatologically warmest day, so each season contains
exactly one cold period (northern winter Dec-Feb, southern winter Jun-Aug).
"""

import math
from collections import defaultdict
from datetime import date, timedelta

FROST_C = 0.0  # air frost at 2 m; plants on the ground can frost a little above this
HOT_C = 30.0  # daily maximum at which most cool-season crops bolt or stall and fruit set starts to suffer
SUMMARY_VERSION = 2  # bump when summarize() output changes; older caches are refetched
REF_YEAR = 2001  # non-leap year used to turn day offsets into month-day labels
MIN_SEASON_DAYS = 360  # skip partial seasons at the ends of the record


def warmest_day(days: list[date], tmin: list[float | None]) -> tuple[int, int]:
    """(month, day) of the warmest point of the year: 31-day smoothed mean of daily minimum temperature."""
    sums, counts = [0.0] * 365, [0] * 365
    for d, t in zip(days, tmin, strict=True):
        if t is not None:
            i = min(d.timetuple().tm_yday, 365) - 1
            sums[i] += t
            counts[i] += 1
    means = [s / c if c else math.nan for s, c in zip(sums, counts, strict=True)]
    smooth = [_nanmean(means[(i + k) % 365] for k in range(-15, 16)) for i in range(365)]
    best = max(range(365), key=lambda i: -math.inf if math.isnan(smooth[i]) else smooth[i])
    ref = date(REF_YEAR, 1, 1) + timedelta(days=best)
    return ref.month, ref.day


def _nanmean(values) -> float:
    vals = [v for v in values if not math.isnan(v)]
    return sum(vals) / len(vals) if vals else math.nan


def season_stats(days: list[date], tmin: list[float | None]) -> dict:
    """Per-season frost offsets (days after season start) and extreme minimum temperatures."""
    month, day = warmest_day(days, tmin)
    seasons: dict[int, list[tuple[int, float]]] = defaultdict(list)
    for d, t in zip(days, tmin, strict=True):
        if t is None:
            continue
        year = d.year if (d.month, d.day) >= (month, day) else d.year - 1
        seasons[year].append(((d - date(year, month, day)).days, t))

    first, last, extreme = [], [], []
    for year in sorted(seasons):
        rows = seasons[year]
        if len(rows) < MIN_SEASON_DAYS:
            continue
        frosts = [off for off, t in rows if t <= FROST_C]
        first.append(min(frosts) if frosts else None)
        last.append(max(frosts) if frosts else None)
        extreme.append(min(t for _, t in rows))
    return {"season_start": f"{month:02d}-{day:02d}", "first_frost": first, "last_frost": last, "annual_min": extreme}


def frost_dates(stats: dict, probability: int) -> dict:
    """Spring and fall frost dates at a risk level.

    probability = chance (%) of frost *after* the spring date, and *before* the fall date.
    Seasons without frost count as an infinitely early last frost / infinitely late first frost.
    Returns month-day labels, or None when frost is rarer than the chosen risk.
    """
    p = probability / 100
    last = sorted(-math.inf if v is None else v for v in stats["last_frost"])
    first = sorted(math.inf if v is None else v for v in stats["first_frost"])
    n = len(last)
    if not n:
        raise ValueError("no complete seasons")
    k = min(math.floor(p * n), n - 1)
    spring, fall = last[n - 1 - k], first[k]  # k seasons have frost after `spring` / before `fall`

    month, day = map(int, stats["season_start"].split("-"))
    start = date(REF_YEAR, month, day)

    def label(offset: float) -> str | None:
        return None if math.isinf(offset) else (start + timedelta(days=int(offset))).strftime("%m-%d")

    # The fall frost is the start of the *next* cold period, i.e. in the following season.
    season_days = 365 if math.isinf(spring) or math.isinf(fall) else int(fall + 365 - spring)
    frost_seasons = sum(v is not None for v in stats["first_frost"])
    return {
        "last_spring_frost": label(spring),
        "first_fall_frost": label(fall),
        "growing_season_days": season_days,
        "frost_free": frost_seasons == 0,
        "frost_years_pct": round(100 * frost_seasons / n),
    }


def hardiness_zone(annual_min_c: list[float]) -> dict:
    """USDA-style zone from the mean annual extreme minimum (zone 1a starts at -60 °F; 10 °F per zone)."""
    mean_c = sum(annual_min_c) / len(annual_min_c)
    f = mean_c * 9 / 5 + 32
    steps = max(0, min(25, math.floor((f + 60) / 5)))  # 26 half-zones: 1a … 13b
    return {"zone": f"{steps // 2 + 1}{'ab'[steps % 2]}", "extreme_min_c": round(mean_c, 1)}


def day_length_hours(latitude: float, day_of_year: int) -> float:
    """Daylight hours from sunrise to sunset (sun centre at -0.833°, includes refraction)."""
    decl = math.radians(23.44) * math.sin(2 * math.pi * (284 + day_of_year) / 365)
    lat = math.radians(latitude)
    cos_h = (math.sin(math.radians(-0.833)) - math.sin(lat) * math.sin(decl)) / (math.cos(lat) * math.cos(decl))
    return 2 * math.degrees(math.acos(max(-1.0, min(1.0, cos_h)))) / 15


def monthly_daylight(latitude: float) -> list[float]:
    """Day length on the 15th of each month."""
    return [round(day_length_hours(latitude, date(REF_YEAR, m, 15).timetuple().tm_yday), 1) for m in range(1, 13)]


def monthly_means(days: list[date], values: list[float | None]) -> list[float | None]:
    sums, counts = [0.0] * 12, [0] * 12
    for d, v in zip(days, values, strict=True):
        if v is not None:
            sums[d.month - 1] += v
            counts[d.month - 1] += 1
    return [round(s / c, 1) if c else None for s, c in zip(sums, counts, strict=True)]


def monthly_totals(days: list[date], values: list[float | None]) -> list[float | None]:
    """Average per-year total for each calendar month (e.g. mm of rain in a typical March)."""
    sums, years = [0.0] * 12, [set() for _ in range(12)]
    for d, v in zip(days, values, strict=True):
        if v is not None:
            sums[d.month - 1] += v
            years[d.month - 1].add(d.year)
    return [round(s / len(y), 1) if y else None for s, y in zip(sums, years, strict=True)]


def rainfall_regime(rain: list[float | None], tmin: list[float | None]) -> str:
    """'winter', 'summer' or 'year-round': where the rain falls relative to the 6 coldest months.

    Using the coldest months rather than calendar months makes it hemisphere-independent.
    """
    pairs = [(t, r or 0.0) for t, r in zip(tmin, rain, strict=True) if t is not None]
    total = sum(r for _, r in pairs)
    if not total:
        return "dry"
    cold_share = sum(r for _, r in sorted(pairs)[:6]) / total
    return "winter" if cold_share >= 0.6 else "summer" if cold_share <= 0.4 else "year-round"


def summarize(raw: dict) -> dict:
    """Condense an Open-Meteo daily archive response into what we store (a few KB)."""
    daily = raw["daily"]
    days = [date.fromisoformat(d) for d in daily["time"]]
    tmin, tmax = daily["temperature_2m_min"], daily["temperature_2m_max"]
    return {
        "version": SUMMARY_VERSION,
        **season_stats(days, tmin),
        "elevation_m": raw.get("elevation"),
        "timezone": raw.get("timezone"),
        "period": f"{days[0].year}-{days[-1].year}",
        "monthly": {
            "tmin": monthly_means(days, tmin),
            "tmax": monthly_means(days, tmax),
            "soil": monthly_means(days, daily["soil_temperature_0_to_7cm_mean"]),
            "rain": monthly_totals(days, daily["precipitation_sum"]),
            "hot_days": monthly_totals(days, [None if t is None else float(t >= HOT_C) for t in tmax]),
        },
    }


def report(summary: dict, latitude: float, frost_probability: int) -> dict:
    """Everything the app shows, computed from the stored summary and the garden's risk preference."""
    monthly = summary["monthly"]
    return {
        "rainfall_regime": rainfall_regime(monthly["rain"], monthly["tmin"]),
        "annual_rain_mm": round(sum(r or 0 for r in monthly["rain"])),
        "hot_days_per_year": round(sum(h or 0 for h in monthly["hot_days"])),
        **frost_dates(summary, frost_probability),
        **hardiness_zone(summary["annual_min"]),
        "frost_probability": frost_probability,
        "daylight_hours": monthly_daylight(latitude),
        "monthly": monthly,
        "elevation_m": summary["elevation_m"],
        "period": summary["period"],
        "southern_hemisphere": latitude < 0,
    }
