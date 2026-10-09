"""Environment engine v2 (SPEC §4.2): the site's past ~30 years of daily weather as equally plausible futures.

Every question is answered the same way for every place on Earth: run it through each historical year and
take the (recency-weighted) share of years in which it happens. "Chance of a night at or below -2 °C between
1 and 20 September", "days until 900 growing degree-days from a 15 March sowing", "irrigation needed in
January" are all one loop over years. Sequences within a year stay intact, which daily averages cannot give.

- Years are 365 days: 29 February is dropped (DOY 1 = 1 January, 365 = 31 December).
- Recency weights: weight = 0.5 ** ((last_year - year) / half_life).
- Warming/cooling trend: if the year-to-year trend of a temperature variable is significant, each past year
  is shifted to today's level (value + slope * (as_of_year - year)), so old years don't pull estimates back.
- Windows may cross 31 December: they continue into the following year (the last year can't, so it drops out).

Pure functions only; fetching and storage live in external.py / routers.
"""

import math
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import date, timedelta

YEAR_DAYS = 365
TEMPERATURE_VARS = ("tmin", "tmax", "soil_t")
POOL_HALF_WIDTH = 7  # days either side pooled for day-of-year curves (15-day window)

Values = list[float | None]


@dataclass
class Climatology:
    years: list[int]  # complete calendar years, ascending
    series: dict[str, list[Values]]  # variable -> one 365-value list per year (trend-adjusted temperatures)
    weights: list[float]  # one per year, sums to 1
    trends: dict[str, float] = field(default_factory=dict)  # °C per year applied; absent = not significant
    as_of_year: int = 0


# ---------------------------------------------------------------- building


def doy(d: date) -> int:
    """Day of year on the 365-day calendar (29 Feb maps to 28 Feb's slot; callers skip it when building)."""
    n = d.timetuple().tm_yday
    return n - 1 if d.month > 2 and _leap(d.year) else n


def doy_to_date(day: int, year: int = 2001) -> date:
    return date(year, 1, 1) + timedelta(days=day - 1)  # 2001 is not a leap year


def _leap(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def build(
    days: Sequence[date], variables: dict[str, Values], half_life: float = 10.0, as_of_year: int | None = None
) -> Climatology:
    """Group a daily record into complete 365-day years, weight them, and remove significant trends."""
    by_year: dict[int, dict[str, Values]] = {}
    for i, d in enumerate(days):
        if d.month == 2 and d.day == 29:
            continue
        year = by_year.setdefault(d.year, {v: [None] * YEAR_DAYS for v in variables})
        for name, values in variables.items():
            year[name][doy(d) - 1] = values[i]
    # A year counts when its first variable is at least 95% present (one bad sensor day is fine, half a year isn't).
    first = next(iter(variables))
    years = sorted(y for y, v in by_year.items() if sum(x is not None for x in v[first]) >= 0.95 * YEAR_DAYS)
    if not years:
        raise ValueError("no complete years in the record")
    as_of = as_of_year or years[-1] + 1
    raw = [0.5 ** ((years[-1] - y) / half_life) for y in years]
    weights = [w / sum(raw) for w in raw]
    series = {name: [by_year[y][name] for y in years] for name in variables}

    trends: dict[str, float] = {}
    for name in TEMPERATURE_VARS:
        if name not in series:
            continue
        slope = significant_trend(years, [_mean(v) for v in series[name]])
        if slope:
            trends[name] = slope
            series[name] = [
                [None if x is None else x + slope * (as_of - y) for x in vals]
                for y, vals in zip(years, series[name], strict=True)
            ]
    return Climatology(years, series, weights, trends, as_of)


def from_open_meteo(raw: dict, half_life: float = 10.0) -> Climatology:
    """Build from an Open-Meteo archive response (variables mapped by external.ARCHIVE_VARIABLES)."""
    from .external import ARCHIVE_VARIABLES

    daily = raw["daily"]
    days = [date.fromisoformat(d) for d in daily["time"]]
    variables = {name: daily[key] for key, name in ARCHIVE_VARIABLES.items() if key in daily}
    return build(days, variables, half_life=half_life)


def significant_trend(xs: Sequence[float], ys: Sequence[float | None]) -> float | None:
    """Least-squares slope of ys over xs if |t| exceeds the two-sided 5% critical value, else None."""
    pts = [(x, y) for x, y in zip(xs, ys, strict=True) if y is not None and not math.isnan(y)]
    n = len(pts)
    if n < 8:
        return None
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    slope = sum((x - mx) * (y - my) for x, y in pts) / sxx
    resid = sum((y - my - slope * (x - mx)) ** 2 for x, y in pts)
    se = math.sqrt(resid / (n - 2) / sxx) if resid > 0 else 0.0
    if se == 0:
        return slope if slope else None
    # shortcut: t critical value approximated as 1.96 + 2.5/df (within ~0.05 of the table for df >= 8);
    # replace with an exact quantile if a stats dependency arrives for other reasons.
    return slope if abs(slope / se) > 1.96 + 2.5 / (n - 2) else None


def _mean(values: Values) -> float:
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else math.nan


# ---------------------------------------------------------------- per-year windows


def windows(c: Climatology, var: str, start_doy: int, days: int) -> list[tuple[Values, float]]:
    """(values, weight) per year for the window [start_doy, start_doy + days), continuing into the next year
    when it crosses 31 December. Weights are renormalised over the years that can supply the whole window."""
    if not 1 <= start_doy <= YEAR_DAYS or not 1 <= days <= 2 * YEAR_DAYS:
        raise ValueError("start_doy must be 1..365 and days 1..730")
    series = c.series[var]
    years_needed = (start_doy - 1 + days - 1) // YEAR_DAYS + 1
    out = []
    for i in range(len(c.years) - years_needed + 1):
        joined: Values = [x for k in range(years_needed) for x in series[i + k]]
        out.append((joined[start_doy - 1 : start_doy - 1 + days], c.weights[i]))
    total = sum(w for _, w in out)
    return [(vals, w / total) for vals, w in out]


def compare(op: str, x: float) -> Callable[[float], bool]:
    ops = {"le": lambda v: v <= x, "lt": lambda v: v < x, "ge": lambda v: v >= x, "gt": lambda v: v > x}
    if op not in ops:
        raise ValueError("op must be one of le, lt, ge, gt")
    return ops[op]


def prob_any(c: Climatology, var: str, op: str, x: float, start_doy: int, days: int) -> float:
    """Chance that at least one day in the window meets the condition (e.g. any night <= lethal_min)."""
    test = compare(op, x)
    return sum(w for vals, w in windows(c, var, start_doy, days) if any(v is not None and test(v) for v in vals))


def per_year(
    c: Climatology, var: str, start_doy: int, days: int, reduce: Callable[[Values], float | None]
) -> list[tuple[float, float]]:
    """(value, weight) per year after reducing each year's window; years where reduce gives None drop out."""
    pairs = [(reduce(vals), w) for vals, w in windows(c, var, start_doy, days)]
    kept = [(v, w) for v, w in pairs if v is not None]
    total = sum(w for _, w in kept)
    return [(v, w / total) for v, w in kept] if total else []


# ---------------------------------------------------------------- distributions


def weighted_quantile(pairs: Iterable[tuple[float, float]], q: float) -> float:
    """Weighted inverse-CDF quantile of (value, weight) pairs; weights need not sum to 1.

    The smallest value whose cumulative weight passes q; exactly on a boundary between two values, their
    average (so the median of 1, 2, 3, 4 is 2.5, and a value holding 75% of the weight is the median)."""
    items = sorted(pairs)
    if not items:
        raise ValueError("no values")
    total = sum(w for _, w in items)
    target, cum, eps = q * total, 0.0, 1e-12 * total
    for k, (v, w) in enumerate(items):
        cum += w
        if cum > target + eps:
            return v
        if abs(cum - target) <= eps:
            return (v + items[k + 1][0]) / 2 if k + 1 < len(items) else v
    return items[-1][0]


def summary(pairs: list[tuple[float, float]]) -> dict[str, float]:
    """Weighted mean and 10th/50th/90th percentiles."""
    return {
        "mean": sum(v * w for v, w in pairs) / sum(w for _, w in pairs),
        "p10": weighted_quantile(pairs, 0.1),
        "p50": weighted_quantile(pairs, 0.5),
        "p90": weighted_quantile(pairs, 0.9),
    }


def _pooled(c: Climatology, var: str, day: int) -> list[tuple[float, float]]:
    """All (value, weight) pairs within ±POOL_HALF_WIDTH days of a day of year, across all years (wrapping)."""
    pairs = []
    for vals, w in zip(c.series[var], c.weights, strict=True):
        for k in range(-POOL_HALF_WIDTH, POOL_HALF_WIDTH + 1):
            v = vals[(day - 1 + k) % YEAR_DAYS]
            if v is not None:
                pairs.append((v, w))
    return pairs


def daily_prob(c: Climatology, var: str, op: str, x: float) -> list[float]:
    """Chance of the condition on a single day, for each day of year (smoothed over a 15-day window)."""
    test = compare(op, x)
    out = []
    for day in range(1, YEAR_DAYS + 1):
        pairs = _pooled(c, var, day)
        total = sum(w for _, w in pairs)
        out.append(sum(w for v, w in pairs if test(v)) / total if total else 0.0)
    return out


def daily_quantiles(c: Climatology, var: str, qs: Sequence[float] = (0.1, 0.5, 0.9)) -> list[list[float | None]]:
    """For each day of year, the requested quantiles (smoothed over a 15-day window)."""
    out = []
    for day in range(1, YEAR_DAYS + 1):
        pairs = _pooled(c, var, day)
        out.append([weighted_quantile(pairs, q) if pairs else None for q in qs])
    return out


# ---------------------------------------------------------------- agronomy helpers


def gdd_day(tmin: float, tmax: float, base: float, cutoff: float | None = None) -> float:
    """Growing degree-days for one day: averaging method with the maximum capped at the upper cutoff."""
    hi = min(tmax, cutoff) if cutoff is not None else tmax
    lo = min(tmin, hi)
    return max(0.0, (hi + lo) / 2 - base)


def _paired(c: Climatology, start_doy: int, days: int) -> list[tuple[list[tuple[float | None, float | None]], float]]:
    mins = windows(c, "tmin", start_doy, days)
    maxs = windows(c, "tmax", start_doy, days)
    return [(list(zip(a, b, strict=True)), w) for (a, w), (b, _) in zip(mins, maxs, strict=True)]


def gdd_totals(
    c: Climatology, start_doy: int, days: int, base: float, cutoff: float | None = None
) -> list[tuple[float, float]]:
    """(total GDD, weight) per year over a window."""
    return [
        (sum(gdd_day(lo, hi, base, cutoff) for lo, hi in pairs if lo is not None and hi is not None), w)
        for pairs, w in _paired(c, start_doy, days)
    ]


def days_to_gdd(
    c: Climatology, start_doy: int, target: float, base: float, cutoff: float | None = None, max_days: int = 730
) -> list[tuple[float, float]]:
    """(days needed to accumulate `target` GDD from start_doy, weight) per year. Years that never get there
    within max_days are reported as math.inf, so callers can see "doesn't mature" as a probability."""
    out = []
    for pairs, w in _paired(c, start_doy, max_days):
        total, needed = 0.0, math.inf
        for i, (lo, hi) in enumerate(pairs, start=1):
            if lo is not None and hi is not None:
                total += gdd_day(lo, hi, base, cutoff)
            if total >= target:
                needed = float(i)
                break
        out.append((needed, w))
    return out


def water_deficit(c: Climatology, start_doy: int, days: int, kc: float) -> list[tuple[float, float]]:
    """(crop water need minus rain in mm, weight) per year: sum(ET0 * Kc - precipitation), floored at 0.

    shortcut: a simple bucket without soil storage or effective-rain losses; the per-bed FAO-56 balance
    (SPEC §6.6, PLAN 6.5) replaces it for irrigation tasks."""
    et0 = windows(c, "et0", start_doy, days)
    rain = windows(c, "precip", start_doy, days)
    out = []
    for (e, w), (r, _) in zip(et0, rain, strict=True):
        need = sum((ev or 0.0) * kc for ev in e)
        got = sum(rv or 0.0 for rv in r)
        out.append((max(0.0, need - got), w))
    return out
