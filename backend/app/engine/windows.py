"""Window finder (SPEC §6.4): for every possible sowing day, how likely is a crop to succeed, and how good is the
season? Each year on record is one possible future (environment.py), so every answer is a weighted share of years.

Direct sowing only. Indoor starts, transplanting and protected growing come next (PLAN 6.2).
shortcut: events are counted on daily minima and maxima of the gridded record; a sustained-heat rule of five days
stands in for the crop-specific flower-drop and bolting models, which need catalog data not yet written.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from dataclasses import dataclass
from itertools import accumulate

from ..environment import YEAR_DAYS, Climatology, doy_to_date, gdd_day, weighted_quantile
from .phenology import EMERGENCE_DAYS, CropProfile, design_days

HEAT_DAYS_TO_FAIL = 5  # days at or above stress_max, within the exposed part of the season
SLOW_FACTOR = 2.0  # a crop that needs more than this many times its longest cycle does not mature in practice
HEAD_START_CAP = 0.35  # the most of the heat-sum target a seedling raised indoors is credited with
BEST_SHARE = 0.95  # the best sub-window: days scoring within 5 % of the best day


def success_threshold(frost_probability: int) -> float:
    """Minimum success probability for a day to count as viable, from the household's frost-risk setting
    (10 = cautious, 50 = typical, 90 = bold): 0.9, 0.8 and 0.6, interpolated between."""
    p = min(90, max(10, frost_probability))
    return 0.9 - 0.1 * (p - 10) / 40 if p <= 50 else 0.8 - 0.2 * (p - 50) / 40


@dataclass
class _Year:
    weight: float
    tmin: list[float]
    tmax: list[float]
    soil: list[float]
    cum_gdd: list[float]
    cum_frost: list[int]
    cum_heat: list[int]
    cum_optimal: list[int]
    cum_soil_ok: list[int]


def _clean(values: list[float | None]) -> list[float]:
    return [math.nan if v is None else v for v in values]


def _prefix(flags: list[bool]) -> list[int]:
    return [0, *accumulate(int(f) for f in flags)]


def _years(c: Climatology, p: CropProfile) -> list[_Year]:
    """One entry per year that has a following year, so every start day has two years of weather to run through."""
    out = []
    soil_series = c.series.get("soil_t")
    for i in range(len(c.years) - 1):
        tmin = _clean(c.series["tmin"][i] + c.series["tmin"][i + 1])
        tmax = _clean(c.series["tmax"][i] + c.series["tmax"][i + 1])
        soil = _clean(soil_series[i] + soil_series[i + 1]) if soil_series else [math.nan] * len(tmin)
        gdd = [
            0.0 if math.isnan(lo) or math.isnan(hi) else gdd_day(lo, hi, p.base, p.cutoff)
            for lo, hi in zip(tmin, tmax, strict=True)
        ]
        lo_opt, hi_opt = p.optimal or (-math.inf, math.inf)
        out.append(
            _Year(
                weight=c.weights[i],
                tmin=tmin,
                tmax=tmax,
                soil=soil,
                cum_gdd=[0.0, *accumulate(gdd)],
                cum_frost=_prefix([p.lethal_min is not None and v <= p.lethal_min for v in tmin]),
                cum_heat=_prefix([p.stress_max is not None and v >= p.stress_max for v in tmax]),
                cum_optimal=_prefix([lo_opt <= (a + b) / 2 <= hi_opt for a, b in zip(tmin, tmax, strict=True)]),
                cum_soil_ok=_prefix(
                    [p.germination_min is None or math.isnan(v) or v >= p.germination_min for v in soil]
                ),
            )
        )
    total = sum(y.weight for y in out)
    for y in out:
        y.weight /= total
    return out


FACTORS = ("matures", "germination", "frost", "heat")


def _one_start(y: _Year, s: int, p: CropProfile, age: float = 0.0) -> dict | None:
    """What happens in one year when sowing (or, with `age` > 0, setting out a seedling raised indoors for `age`
    days) on day s (0-364): which risks hit, when it matures, how good it is."""
    if age:
        germ_ok = True  # germinated indoors
        credit = min(HEAD_START_CAP, age / design_days(p.cycle_days)) * p.gdd_to_maturity
        emerge = 0  # already up: exposed to frost and heat from the day it goes out
    else:
        germ_ok = y.cum_soil_ok[s + EMERGENCE_DAYS] - y.cum_soil_ok[s] >= EMERGENCE_DAYS * 0.5  # half the days warm
        credit, emerge = 0.0, EMERGENCE_DAYS
    end = bisect_left(
        y.cum_gdd, y.cum_gdd[s] + p.gdd_to_maturity - credit
    )  # first day index (1-based) with enough heat
    longest = SLOW_FACTOR * p.cycle_days[1]
    matures = end < len(y.cum_gdd) and end - s + age <= longest
    if not matures:
        return {"matures": False, "germination": germ_ok, "frost": True, "heat": True, "days": None, "quality": 0.0}
    exposed_from = s + emerge
    frost_hit = y.cum_frost[end] - y.cum_frost[exposed_from] > 0
    heat_hit = y.cum_heat[end] - y.cum_heat[exposed_from] >= HEAT_DAYS_TO_FAIL
    quality = (y.cum_optimal[end] - y.cum_optimal[s]) / (end - s) if p.optimal else 1.0
    return {
        "matures": True,
        "germination": germ_ok,
        "frost": not frost_hit,
        "heat": not heat_hit,
        "days": float(end - s + age),
        "quality": quality,
    }


def evaluate(c: Climatology, p: CropProfile, age: float = 0.0) -> list[dict]:
    """For each sowing day of the year (index 0 = 1 January): joint success, each factor on its own, season
    quality (share of days in the optimal band) and the spread of days to maturity in years that succeed."""
    if not p.usable:
        raise ValueError("profile is missing " + " and ".join(p.missing))
    years = _years(c, p)
    days = []
    for s in range(YEAR_DAYS):
        runs = [(y.weight, _one_start(y, s, p, age)) for y in years]
        factors = {f: sum(w for w, r in runs if r and r[f]) for f in FACTORS}
        good = [(w, r) for w, r in runs if r and all(r[f] for f in FACTORS)]
        success = sum(w for w, _ in good)
        entry = {
            "doy": s + 1,
            "success": success,
            "factors": factors,
            "quality": sum(w * r["quality"] for w, r in good) / success if success else 0.0,
            "days_to_maturity": None,
        }
        if good:
            pairs = [(r["days"], w) for w, r in good]
            entry["days_to_maturity"] = {
                q: weighted_quantile(pairs, v) for q, v in (("p10", 0.1), ("p50", 0.5), ("p90", 0.9))
            }
        days.append(entry)
    return days


def _runs(flags: list[bool]) -> list[tuple[int, int]]:
    """Runs of True around a 365-day circle as (first index, length); a run may cross the year end."""
    n = len(flags)
    if all(flags):
        return [(0, n)]
    first_false = flags.index(False)
    runs, start = [], None
    for k in range(1, n + 1):
        i = (first_false + k) % n
        if flags[i] and start is None:
            start = i
        elif not flags[i] and start is not None:
            runs.append((start, (i - start) % n))
            start = None
    return runs


def _date(doy: int) -> str:
    d = doy_to_date(doy)
    return f"{d.month:02d}-{d.day:02d}"


def find_windows(days: list[dict], threshold: float) -> list[dict]:
    """Consecutive viable sowing days form windows; each names its best sub-window (days within 5 % of the best)."""
    score = [d["success"] * (0.5 + 0.5 * d["quality"]) for d in days]
    out = []
    for first, length in _runs([d["success"] >= threshold for d in days]):
        idx = [(first + k) % YEAR_DAYS for k in range(length)]
        top = max(range(length), key=lambda k: score[idx[k]])
        lo = hi = top
        while lo > 0 and score[idx[lo - 1]] >= BEST_SHARE * score[idx[top]]:
            lo -= 1
        while hi < length - 1 and score[idx[hi + 1]] >= BEST_SHARE * score[idx[top]]:
            hi += 1
        mid = days[idx[top]]
        out.append(
            {
                "start": _date(idx[0] + 1),
                "end": _date(idx[-1] + 1),
                "length_days": length,
                "all_year": length == YEAR_DAYS,
                "best_start": _date(idx[lo] + 1),
                "best_end": _date(idx[hi] + 1),
                "success": round(mid["success"], 3),
                "quality": round(mid["quality"], 3),
                "days_to_maturity": {k: round(v) for k, v in mid["days_to_maturity"].items()},
            }
        )
    return sorted(out, key=lambda w: -w["success"])


def verdict(days: list[dict], windows: list[dict], threshold: float, p: CropProfile) -> dict:
    """'Can I grow this here?': yes, only at higher risk, or no; and what stands in the way."""
    best = max(d["success"] for d in days)
    if windows:
        state = "yes"
    elif best >= 0.5:
        state = "risky"
    else:
        state = "no"
    blockers = []
    if state != "yes":
        # The factor that is lowest at its own best sowing day is what holds the crop back.
        reach = {f: max(d["factors"][f] for d in days) for f in FACTORS}
        blockers = [f for f, v in sorted(reach.items(), key=lambda kv: kv[1]) if v < threshold]
    return {"state": state, "best_success": round(best, 3), "threshold": round(threshold, 3), "blockers": blockers}


def _analyse(c: Climatology, p: CropProfile, threshold: float, age: float = 0.0) -> dict:
    days = evaluate(c, p, age)
    windows = find_windows(days, threshold)
    return {
        "verdict": verdict(days, windows, threshold, p),
        "windows": windows,
        "success_by_day": [round(d["success"], 3) for d in days],
    }


def analyse(c: Climatology, p: CropProfile, threshold: float) -> dict:
    """Direct sowing, plus (when the crop has a transplant age) setting out seedlings raised indoors; for the
    second, dates are set-out dates and `age_days` says how long before that to sow indoors."""
    result = _analyse(c, p, threshold)
    if p.transplant_age:
        result["transplant"] = _analyse(c, p, threshold, p.transplant_age) | {"age_days": round(p.transplant_age)}
    return result
