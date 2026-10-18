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


MAX_CELLS = 2500  # per bed
CELL_SIZES = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50)  # cm; the fit picks the one nearest 30


def fits(width: float, length: float, cell_cm: int) -> bool:
    """True when whole cells of this size exactly cover the bed, so none hangs over its edge."""
    return round(width * 100) % cell_cm == 0 and round(length * 100) % cell_cm == 0


def fit_cell(width: float, length: float, target: int = 30) -> int:
    """The cell size (cm) for a bed: the one nearest `target` whose whole cells exactly cover it. A bed whose sides
    share no such size (not a multiple of 5 cm) keeps 30 cm, and its last cell is partial."""
    for c in sorted(CELL_SIZES, key=lambda c: (abs(c - target), c)):
        if fits(width, length, c) and (round(width * 100) // c) * (round(length * 100) // c) <= MAX_CELLS:
            return c
    return 30


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


def stagger(cells, cols: int, rows: int, free, p: Patch, key=None) -> list[tuple[int, int]] | None:
    """The patches of the solid block `cells`, re-laid in offset rows: every other row of patches moves half a patch
    along the row (a brick pattern), so plants do not line up in one block. The same count of patches, on `free`
    ground; None when a patch is one cell wide (no half to move), the block is a single row, or the moved rows do not
    fit. Several offsets may fit; `key(cells)` (lower is better) picks, else the first."""
    free = set(free)
    xs, ys = [c for c, _ in cells], [r for _, r in cells]
    c0, r0, rw, rh = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    for q in (p, p.turned()):
        if rw % q.w or rh % q.h:
            continue
        a, b, shift = rw // q.w, rh // q.h, q.w // 2
        if not shift or b < 2:
            continue
        fits = []
        for x0 in (c0, c0 - shift):  # the rows alternate between x0 and x0 + shift, either row first
            for flip in (0, 1):
                out = [
                    (x0 + (shift if (j + flip) % 2 else 0) + i * q.w + dx, r0 + j * q.h + dy)
                    for j in range(b)
                    for i in range(a)
                    for dx in range(q.w)
                    for dy in range(q.h)
                ]
                if all(0 <= x < cols and 0 <= y < rows and (x, y) in free for x, y in out):
                    fits.append(out)
        if fits:
            return min(fits, key=key) if key else fits[0]
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


# ---------------------------------------------------------------- plants at their real size

Spot = tuple[int, int, int, int]  # one plant: x, y, width, height in cm from the bed's top left corner


def spot_size(cell_cm: int, dims: tuple[float, float] | None) -> tuple[int, int]:
    """The ground one plant takes, in cm: its spacing in the row by between rows (a cell when the spacing is unknown)."""
    return (max(1, round(dims[0])), max(1, round(dims[1]))) if dims else (cell_cm, cell_cm)


def overlap(a: Spot, b: Spot) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def fill(cells, cell_cm: int, width_cm: int, length_cm: int, dims, avoid=(), limit: int = MAX_CELLS) -> list[Spot]:
    """Plants at their real spacing over painted `cells`, in rows with every other row shifted half a plant (so they
    stagger, never a solid block). A plant goes where its centre is in a painted cell, so one tapped cell takes one plant
    even when the plant is bigger than the cell; it is moved in from the bed's edge, and never lands on `avoid` spots
    (other crops on the ground then) or on a plant of its own. At most `limit` plants."""
    region = {tuple(c) for c in cells}
    w, h = spot_size(cell_cm, dims)
    if not region or w > width_cm or h > length_cm:
        return []
    x0, y0 = min(c for c, _ in region) * cell_cm, min(r for _, r in region) * cell_cm
    x1, y1 = (max(c for c, _ in region) + 1) * cell_cm, (max(r for _, r in region) + 1) * cell_cm
    out: list[Spot] = []
    row: list[Spot] = []
    j, cy = 0, y0 + h / 2
    while cy < y1 and len(out) < limit:
        before, row = row, []  # a plant can only touch its own row and the one before it
        cx = x0 + w / 2 + (w / 2 if j % 2 else 0)
        while cx < x1 and len(out) < limit:
            if cx < width_cm and cy < length_cm and (int(cx // cell_cm), int(cy // cell_cm)) in region:
                s = (
                    min(max(round(cx - w / 2), 0), width_cm - w),
                    min(max(round(cy - h / 2), 0), length_cm - h),
                    w,
                    h,
                )
                if not any(overlap(s, o) for o in (*avoid, *before, *row)):
                    row.append(s)
                    out.append(s)
            cx += w
        j, cy = j + 1, cy + h
    return out


def cover(spots, cell_cm: int) -> list[list[int]]:
    """The grid cells that plants touch, in reading order."""
    out = {
        (x, y)
        for sx, sy, w, h in spots
        for x in range(sx // cell_cm, (sx + w - 1) // cell_cm + 1)
        for y in range(sy // cell_cm, (sy + h - 1) // cell_cm + 1)
    }
    return [list(c) for c in sorted(out, key=lambda c: (c[1], c[0]))]


def spot_clashes(held, cell_cm: int) -> list[tuple[Cell, int, int]]:
    """Pairs of plantings (ids) with plants on the same ground on overlapping days, each with a cell it happens in.
    `held` = (planting id, spot, from, to). Plants of different crops sharing a cell but not the ground do not clash."""
    by_cell: dict[tuple[int, int], list] = {}
    for item in held:
        for c, r in cover([item[1]], cell_cm):
            by_cell.setdefault((c, r), []).append(item)
    found: dict[tuple[int, int], Cell] = {}
    for cell, group in by_cell.items():
        for i, (p, a, f, t) in enumerate(group):
            for q, b, g, u in group[i + 1 :]:
                if p != q and f <= u and g <= t and overlap(a, b):
                    found.setdefault((min(p, q), max(p, q)), cell)
    return [(cell, p, q) for (p, q), cell in sorted(found.items())]
