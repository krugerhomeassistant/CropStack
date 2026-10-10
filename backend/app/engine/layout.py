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


# ---------------------------------------------------------------- cells, time and free space

from datetime import date, timedelta  # noqa: E402
from math import ceil, floor  # noqa: E402

DEFAULT_CYCLE_DAYS = 90  # shortcut: used when a crop has no catalogued cycle length; replace with the crop's own
MAX_PER_CELL = 16


def grid(width: float, length: float, cell_cm: int) -> tuple[int, int]:
    """Columns (along the width) and rows (along the length) of cells that cover a bed."""
    cell = cell_cm / 100
    return max(1, ceil(width / cell - 1e-9)), max(1, ceil(length / cell - 1e-9))


def per_cell(cell_cm: int, footprint: float | None) -> int:
    """How many plants of a crop fit in one cell (1 when the catalog has no spread for it)."""
    if not footprint:
        return 1
    return max(1, min(MAX_PER_CELL, floor((cell_cm / 100) ** 2 / footprint + 1e-9)))


def occupancy(
    start: date, set_out: date | None, ends_on: date | None, status: str, cycle_days: float | None, today: date
) -> tuple[date, date]:
    """The days a planting holds its cells: from sowing (or set-out) to `ends_on`, else the crop's longest cycle.
    A finished or failed planting lets go of its cells today."""
    first = set_out or start
    last = ends_on or first + timedelta(days=round(cycle_days or DEFAULT_CYCLE_DAYS))
    if status in ("finished", "failed"):
        last = min(last, max(first, today))
    return first, max(first, last)


Cell = tuple[int, int]


def free_cells(cols: int, rows: int, taken: list[tuple[Cell, date, date]], first: date, last: date) -> list[Cell]:
    """Cells nobody holds at any point between `first` and `last`, in reading order (row by row)."""
    busy = {cell for cell, a, b in taken if a <= last and first <= b}
    return [(c, r) for r in range(rows) for c in range(cols) if (c, r) not in busy]


def clashes(held: list[tuple[int, Cell, date, date]]) -> list[tuple[Cell, int, int]]:
    """Pairs of plantings (ids) that hold the same cell on overlapping days. `held` = (planting id, cell, from, to)."""
    out = []
    for i, (p, cell, a, b) in enumerate(held):
        for q, other, c, d in held[i + 1 :]:
            if cell == other and p != q and a <= d and c <= b:
                out.append((cell, p, q))
    return out
