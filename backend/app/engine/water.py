"""Soil-water balance for one planting (FAO-56, simplified): when will the root zone run dry?

Each day the crop uses ETc = Kc * ET0 and rain refills the soil. Starting full (at sowing or the last watering),
the water used since then is the depletion; the crop is stressed once it passes the readily available water
RAW = p * TAW, where TAW = soil water-holding capacity * root depth.
shortcut: one standard soil (120 mm of water per metre of depth) and 80 % of rain counted, until the setup
questions ask about soil; no mulch, shade or rain-shelter effects; roots grow in a straight line to full depth.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median

from .phenology import _number, _range

SOIL_AWC_MM_PER_M = 120.0
RAIN_USED = 0.8
SEEDLING_ROOT_M = 0.2
GENERIC_STAGES = (0.15, 0.25, 0.40, 0.20)  # FAO-56's rough split: initial, development, mid, late


@dataclass(frozen=True)
class WaterProfile:
    kc: tuple[float, float, float]  # initial, mid, late
    stage_days: tuple[float, float, float, float]  # initial, development, mid, late
    root_m: float  # depth at full growth
    depletion_fraction: float  # p: share of TAW the crop can use before it is stressed

    @property
    def total_days(self) -> float:
        return sum(self.stage_days)

    def kc_at(self, age: float) -> float:
        ini, dev, mid, late = self.stage_days
        k0, k1, k2 = self.kc
        if age <= ini:
            return k0
        if age <= ini + dev:
            return k0 + (k1 - k0) * (age - ini) / dev
        if age <= ini + dev + mid:
            return k1
        return k1 + (k2 - k1) * min(1.0, (age - ini - dev - mid) / late)

    def root_at(self, age: float) -> float:
        grown = min(1.0, age / max(1.0, self.stage_days[0] + self.stage_days[1]))
        return SEEDLING_ROOT_M + (self.root_m - SEEDLING_ROOT_M) * grown


def profile_from_item(item: dict, cycle_days: tuple[float, float] | None) -> WaterProfile | None:
    """From a catalog item: Kc, root depth and p are needed; stage lengths come from the catalog (median over its
    regions) or, failing that, a standard split of the growing cycle. None when anything needed is missing."""
    kc = [_number(item, "requirements", "water", k) for k in ("kc_initial", "kc_mid", "kc_late")]
    depth = _range(item, "requirements", "water", "root_depth")
    p = _number(item, "requirements", "water", "depletion_fraction")
    if None in kc or not depth or p is None or depth.get("min") is None or depth.get("max") is None:
        return None
    stages = []
    for name in ("initial", "development", "mid", "late"):
        node = item.get("params", {}).get(f"stage_days_{name}")
        values = [
            f["value"]
            for f in (node if isinstance(node, list) else [node])
            if f and isinstance(f.get("value"), int | float)
        ]
        stages.append(median(values) if values else None)
    if None in stages:
        if not cycle_days:
            return None
        total = sum(cycle_days) / 2
        stages = [total * f for f in GENERIC_STAGES]
    return WaterProfile((kc[0], kc[1], kc[2]), tuple(stages), (depth["min"] + depth["max"]) / 2, p)  # type: ignore[arg-type]


def depletion_path(
    w: WaterProfile, sown: date, wet_since: date, days: list[dict], awc: float = SOIL_AWC_MM_PER_M
) -> list[dict]:
    """Day by day from `wet_since` (soil full that day): depletion and the dry point, both in mm.
    `days` are weather rows (date ISO, et0 and precip in mm) in date order; missing numbers count as zero."""
    out, depletion = [], 0.0
    for row in days:
        d = date.fromisoformat(row["date"])
        if d <= wet_since:
            continue
        age = (d - sown).days
        taw = awc * w.root_at(age)
        used = w.kc_at(age) * (row.get("et0") or 0.0)
        depletion = min(taw, max(0.0, depletion + used - RAIN_USED * (row.get("precip") or 0.0)))
        out.append({"date": d, "depletion": depletion, "raw": w.depletion_fraction * taw})
    return out


def first_dry_day(path: list[dict], from_day: date, horizon: int = 3) -> dict | None:
    """The first day in [from_day, from_day + horizon] on which the crop passes its readily available water."""
    end = from_day + timedelta(days=horizon)
    return next((r for r in path if from_day <= r["date"] <= end and r["depletion"] >= r["raw"]), None)
