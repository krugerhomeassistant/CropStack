"""Garden layout maths: how much ground a plant needs and whether a bed is full. Pure."""

from __future__ import annotations

from dataclasses import dataclass

from .phenology import _fact


def _metres(item: dict, name: str) -> float | None:
    fact = _fact(item, "params", name)
    value = fact.get("value") if fact else None
    if not isinstance(value, int | float) or isinstance(value, bool) or value <= 0:
        return None
    return float(value) / (100 if fact.get("unit") == "cm" else 1)


def footprint_m2(item: dict) -> float | None:
    """Ground one plant needs, in m²: spread times row spacing, or spread squared when the row gap is unknown.
    None when the catalog has no spread for the crop (so no crowding warning is made for it)."""
    spread = _metres(item, "plant_spread")
    if spread is None:
        return None
    return spread * (_metres(item, "row_spacing") or spread)


def dims_cm(item: dict) -> tuple[float, float] | None:
    """Spacing in the row and between rows, in cm (the spread twice when the row gap is unknown); None without a spread."""
    spread = _metres(item, "plant_spread")
    if spread is None:
        return None
    return spread * 100, (_metres(item, "row_spacing") or spread) * 100


def yield_per_m2(item: dict) -> float | None:
    """Kilograms harvested per m² over one crop cycle; None when the catalog has no single positive number."""
    fact = _fact(item, "params", "yield_per_m2")
    value = fact.get("value") if fact else None
    if not isinstance(value, int | float) or isinstance(value, bool) or value <= 0:
        return None
    return float(value)


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


@dataclass(frozen=True)
class Patch:
    """The block of cells one planting unit takes at a crop's proper spacing: `w` x `h` cells holding `per` plants.
    A small plant shares one cell (1 x 1, several plants); a big one takes a block (a 45 cm tomato: 2 x 2 cells of 30 cm)."""

    w: int = 1
    h: int = 1
    per: int = 1

    @property
    def cells(self) -> int:
        return self.w * self.h

    def turned(self) -> Patch:
        return Patch(self.h, self.w, self.per)


def patch(cell_cm: int, dims: tuple[float, float] | None) -> Patch:
    """The patch for a crop with these spacings (in the row, between rows; cm). Never tighter than the spacing, rows may
    run either way, and the way that wastes the least ground wins. One plant per cell when the spacing is unknown."""
    if not dims:
        return Patch()
    best: tuple[tuple, Patch] | None = None
    for s, r in (dims, dims[::-1]):
        if s <= cell_cm and r <= cell_cm:
            cand = Patch(1, 1, min(MAX_PER_CELL, floor(cell_cm / s + 1e-9) * floor(cell_cm / r + 1e-9)))
        else:
            cand = Patch(ceil(s / cell_cm - 1e-9), ceil(r / cell_cm - 1e-9), 1)
        key = (cand.cells / cand.per, cand.cells, -cand.w)
        if best is None or key < best[0]:
            best = (key, cand)
    assert best
    return best[1]


def plants_in(cell_cm: int, dims: tuple[float, float] | None, n_cells: int) -> int:
    """How many plants of a crop `n_cells` cells hold at its proper spacing (at least 1)."""
    p = patch(cell_cm, dims)
    return p.per * n_cells if p.cells == 1 else max(1, n_cells // p.cells)


def best_block(cols: int, rows: int, free, p: Patch, m: int, key=None, limit: int = 40):
    """The best solid rectangle of up to `m` whole patches `p` on `free` cells, as (cells in reading order, patches), or
    None. The largest count that fits wins; among the places it fits, `key(cells)` (lower is better) decides, then the
    squarer shape, then reading order. Without a `key` the first place found is taken, which is fast."""
    free = set(free)
    pre = [[0] * (cols + 1) for _ in range(rows + 1)]
    for r in range(rows):
        for c in range(cols):
            pre[r + 1][c + 1] = pre[r][c + 1] + pre[r + 1][c] - pre[r][c] + ((c, r) not in free)

    def clear(c: int, r: int, w: int, h: int) -> bool:
        return pre[r + h][c + w] - pre[r][c + w] - pre[r + h][c] + pre[r][c] == 0

    for count in range(m, 0, -1):
        shapes = {(a * q.w, count // a * q.h) for a in range(1, count + 1) if count % a == 0 for q in (p, p.turned())}
        found = []
        for rw, rh in sorted(shapes, key=lambda s: (abs(s[0] - s[1]), s)):
            for r in range(rows - rh + 1):
                for c in range(cols - rw + 1):
                    if clear(c, r, rw, rh):
                        cells = [(x, y) for y in range(r, r + rh) for x in range(c, c + rw)]
                        found.append(((key(cells) if key else (), abs(rw - rh), r, c), cells))
                        if key is None:
                            return cells, count
                if len(found) >= limit:
                    break
        if found:
            return min(found, key=lambda f: f[0])[1], count
    return None


def remap(cells: list[list[int]], old_cm: int, new_cm: int) -> list[list[int]]:
    """The same ground on a grid of a different cell size: every new cell that overlaps an old one."""
    out = {
        (x, y)
        for c, r in cells
        for x in range(c * old_cm // new_cm, -(-(c + 1) * old_cm // new_cm))
        for y in range(r * old_cm // new_cm, -(-(r + 1) * old_cm // new_cm))
    }
    return [list(x) for x in sorted(out, key=lambda x: (x[1], x[0]))]


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
