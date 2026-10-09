"""Crop phenology from a requirement profile (SPEC §6.3): how many growing degree-days a crop needs and what
each day of weather means for it. Pure; reads the effective catalog item as a plain dict."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# SPEC §6.3: when only a cycle length is known, the thermal-time target is that many days at a 20 °C mean.
REFERENCE_MEAN_C = 20.0
EMERGENCE_DAYS = 7  # shortcut: a fixed week for the germination check; use days_to_emergence per soil temperature later


@dataclass(frozen=True)
class CropProfile:
    slug: str
    base: float  # GDD base temperature, °C
    cutoff: float | None  # GDD upper cutoff, °C
    gdd_to_maturity: float
    cycle_days: tuple[float, float]  # shortest and longest cycle on record
    germination_min: float | None = None  # soil temperature below which seeds do not germinate, °C
    lethal_min: float | None = None  # night temperature that kills or badly damages the crop, °C
    stress_max: float | None = None  # day temperature above which growth stops, °C
    optimal: tuple[float, float] | None = None  # mean-temperature band of best growth, °C
    estimates: tuple[str, ...] = ()  # fields whose values are estimates rather than sourced facts
    missing: tuple[str, ...] = field(default=())  # why a window cannot be worked out

    @property
    def usable(self) -> bool:
        return not self.missing


def design_days(cycle_days: tuple[float, float]) -> float:
    """Cycle length the thermal-time target is built on: the shortest cycle plus up to 30 days, as Recocrop does
    (ECOCROP ranges cover every variety and climate, and the shorter season is the relevant one)."""
    low, high = cycle_days
    return low + min(30.0, high - low)


def _fact(item: dict, *path: str) -> dict | None:
    node: Any = item
    for key in path:
        node = node.get(key) if isinstance(node, dict) else None
    if isinstance(node, list):
        node = node[0] if node else None
    return node if isinstance(node, dict) else None


def _number(item: dict, *path: str) -> float | None:
    fact = _fact(item, *path)
    value = fact.get("value") if fact else None
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def _range(item: dict, *path: str) -> dict | None:
    fact = _fact(item, *path)
    value = fact.get("value") if fact else None
    return value if isinstance(value, dict) else None


def profile_from_item(item: dict) -> CropProfile:
    """Read what the engine needs from an effective catalog item (crop or variety).

    The thermal base is the lowest temperature at which the crop grows (`stress_min`) unless the catalog gives a
    `base`; the cutoff is the top of the optimum unless it gives `upper_cutoff`."""
    temp = "requirements", "temperature"
    base = _number(item, *temp, "base")
    if base is None:
        base = _number(item, *temp, "stress_min")
    optimal = _range(item, *temp, "optimal")
    band = (
        (optimal["min"], optimal["max"]) if optimal and None not in (optimal.get("min"), optimal.get("max")) else None
    )
    cutoff = _number(item, *temp, "upper_cutoff") or (band[1] if band else None)
    cycle = _range(item, "params", "cycle_days")
    missing = []
    if base is None:
        missing.append("the lowest temperature it grows at")
    if not cycle or cycle.get("min") is None or cycle.get("max") is None:
        missing.append("the length of its growing cycle")
    cycle_days = (float(cycle["min"]), float(cycle["max"])) if not missing and cycle else (0.0, 0.0)
    gdd = design_days(cycle_days) * max(REFERENCE_MEAN_C - (base or 0.0), 5.0) if not missing else 0.0
    germ = _range(item, "requirements", "soil_temperature", "germination")
    estimates = tuple(
        name for name in ("lethal_min", "stress_max") if (fact := _fact(item, *temp, name)) and fact.get("estimate")
    )
    return CropProfile(
        slug=item.get("slug", ""),
        base=base if base is not None else 0.0,
        cutoff=cutoff,
        gdd_to_maturity=gdd,
        cycle_days=cycle_days,
        germination_min=float(germ["min"]) if germ and germ.get("min") is not None else None,
        lethal_min=_number(item, *temp, "lethal_min"),
        stress_max=_number(item, *temp, "stress_max"),
        optimal=band,
        estimates=estimates,
        missing=tuple(missing),
    )
