"""Garden layout maths: how much ground a plant needs and whether a bed is full. Pure."""

from __future__ import annotations

from dataclasses import dataclass

from .phenology import _fact


def footprint_m2(item: dict) -> float | None:
    """Ground one plant needs, in m²: spread times row spacing, or spread squared when the row gap is unknown.
    None when the catalog has no spread for the crop (so no crowding warning is made for it)."""

    def metres(name: str) -> float | None:
        fact = _fact(item, "params", name)
        value = fact.get("value") if fact else None
        if not isinstance(value, int | float) or isinstance(value, bool) or value <= 0:
            return None
        return float(value) / (100 if fact.get("unit") == "cm" else 1)

    spread = metres("plant_spread")
    if spread is None:
        return None
    return spread * (metres("row_spacing") or spread)


@dataclass(frozen=True)
class Use:
    area_m2: float
    needed_m2: float  # for the plants whose footprint is known
    unknown: int  # plants whose footprint is not in the catalog

    @property
    def crowded(self) -> bool:
        return self.needed_m2 > self.area_m2 * 1.0001


def bed_use(area_m2: float, plants: list[tuple[int, float | None]]) -> Use:
    """`plants` = (quantity, footprint m² or None) for each live planting in the bed."""
    return Use(
        area_m2,
        sum(q * f for q, f in plants if f),
        sum(q for q, f in plants if not f),
    )
