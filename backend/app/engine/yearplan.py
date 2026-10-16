"""Draft a year of plantings for a set of beds so they feed the household: greedy by the most new food per cell. Pure.

Placement is geometric: a plant's patch (`layout.Patch`) is sized from its spacing in both directions, a crop's block is a
solid rectangle of whole patches, and companions count by what actually touches: a crop is placed against its good
companions, never in a bed with its bad ones, and a companion flower goes on the edge of the block it accompanies."""

from __future__ import annotations

import heapq
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil

from . import layout, needs

CAP = 12  # most cells one crop takes in one go, so no crop swallows a bed
COMPANION_BONUS = 0.25  # per good companion touching the block (at most two count): prefer that place
BED_COMPANION_BONUS = 0.1  # per good companion elsewhere in the bed that season (at most two count)
FLOWERS_SHOWN = 2
FLOWER_PATCHES = 2  # patches of a companion flower beside a crop: a small stand, not a bed
FLOWER_LEAD_DAYS = 28  # a flower may go in this long before the crop it accompanies
FLOWER_BLOOM_AFTER = 30  # ...and must be sown at least this long before that crop is done
SEED_BONUS = 1.0  # extra weight for a crop the household already has seed for (suggest, never require)
MIN_GAIN = 1.0  # kg a placement must add toward a shortfall; below this it is not worth a planting

Cell = tuple[int, int]


@dataclass(frozen=True)
class Bed:
    id: int
    name: str
    cols: int
    rows: int
    cell_cm: int


@dataclass(frozen=True)
class Want:
    """One way to start one crop: the day it goes in the ground (set-out day for seedlings) and how long it holds cells."""

    crop: str
    name: str
    family: str
    method: str
    start: date  # sowing day
    set_out: date | None
    planted: date
    cycle_days: int
    success: float
    dims: tuple[float, float] | None  # spacing in the row and between rows, cm
    harvest_from: date
    harvest_to: date
    kg_per_m2: float | None = None  # per crop cycle; a want without it cannot be sized and is left out
    food_group: str | None = None


def _touching(cells: set[Cell], cols: int, rows: int) -> set[Cell]:
    """The cells that share an edge with `cells` (inside the bed, not part of it)."""
    return {
        (c + dc, r + dr)
        for c, r in cells
        for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if 0 <= c + dc < cols and 0 <= r + dr < rows and (c + dc, r + dr) not in cells
    }


def _on_edge(cells, cols: int, rows: int) -> bool:
    return any(c in (0, cols - 1) or r in (0, rows - 1) for c, r in cells)


def _entry(t: Sequence) -> tuple[Cell, date, date, str, str]:
    """A held cell as (cell, from, to, family, crop); `taken` may give just the first four."""
    return (t[0], t[1], t[2], t[3], t[4] if len(t) > 4 else "")


def draft(
    beds: list[Bed],
    taken: dict[int, list],
    wants: list[Want],
    today: date,
    target: dict[str, float],
    existing: Sequence[tuple[str, float, date, date]] = (),
    companions: dict | None = None,
    owned: frozenset[str] = frozenset(),
) -> tuple[list[dict], dict[str, list[float]]]:
    """Place the crop that adds the most food per cell, again and again, until the weekly target is met or the beds
    are full. Returns the plantings and the weekly supply per food group (existing plantings included).
    `taken[bed_id]` = (cell, from, to, family, crop) already held (crop optional); `existing` = (group, kg, harvest
    from, harvest to) of plantings that stay. Rotation: a block avoids cells that held the same family. Nothing is
    placed twice on overlapping days and a crop is not repeated in a month. `companions` = {"good": {crop: {crops}},
    "avoid": ..., "flowers": {crop: [flowers]}}: a block is placed touching a good companion that grows then, and a
    crop never goes into a bed that holds one of its "avoid" crops at the same time. `owned` = crops with seed on
    hand: a block of one scores higher, so the plan leans on them without leaving the rest out."""
    good, avoid = (companions or {}).get("good", {}), (companions or {}).get("avoid", {})
    flowers = (companions or {}).get("flowers", {})
    held = {b.id: [_entry(t) for t in taken.get(b.id, [])] for b in beds}
    by_id = {b.id: b for b in beds}
    supply = {g: [0.0] * needs.WEEKS for g in needs.GROUPS}
    for g, kg, a, z in existing:
        for week, k in needs.spread(today, a, z, kg).items():
            supply[g][week] += k
    all_wants, wants = wants, [w for w in wants if w.kg_per_m2 and w.food_group in supply]

    def evaluate(i: int, b: Bed):
        """The best block for want `i` in bed `b` right now, with its sort key; None when it adds too little."""
        w = wants[i]
        last = layout.occupancy(w.start, w.set_out, None, "planned", w.cycle_days, today)[1]
        free = layout.free_cells(b.cols, b.rows, [(c, a, z) for c, a, z, _, _ in held[b.id]], w.planted, last)
        weeks = needs.week_range(today, w.harvest_from, w.harvest_to)
        if not free or not weeks:
            return None
        grows = {c: crop for c, a, z, _, crop in held[b.id] if crop and a <= last and w.planted <= z}
        about = {crop for _, a, z, _, crop in held[b.id] if crop and a <= last and w.planted <= z and crop != w.crop}
        if about & avoid.get(w.crop, set()):
            return None  # a bad neighbour is in this bed at the same time
        pals = {c: crop for c, crop in grows.items() if crop in good.get(w.crop, set())}
        same = {c for c, _, _, fam, _ in held[b.id] if w.family and fam == w.family}
        p = layout.patch(b.cell_cm, w.dims)
        harvest_weeks = max(1, (w.harvest_to - w.harvest_from).days // 7 + 1)
        per_week = w.kg_per_m2 * (b.cell_cm / 100) ** 2 / harvest_weeks  # kg a week from one cell
        short = [max(0.0, target[w.food_group] - supply[w.food_group][k]) for k in weeks]
        wanted = min(max(CAP, p.cells), ceil(sum(short) / len(short) / per_week - 1e-9))
        m = min(max(1, ceil(wanted / p.cells)), CAP, len(free) // p.cells)
        if m < 1:
            return None

        def beside(cells) -> int:  # how many good companions touch this block
            return len({pals[c] for c in _touching(set(cells), b.cols, b.rows) if c in pals})

        def key(cells):
            return (sum(c in same for c in cells), -beside(cells))

        found = layout.best_block(b.cols, b.rows, free, p, m, key if (same or pals) else None)
        if not found:
            return None
        cells, _ = found
        n = len(cells)
        gain = sum(min(n * per_week, s) for s in short)
        if gain < MIN_GAIN:
            return None
        touching = beside(cells) if pals else 0
        elsewhere = len(set(pals.values())) - touching if pals else 0
        boost = 1 + COMPANION_BONUS * min(2, touching) + BED_COMPANION_BONUS * min(2, max(0, elsewhere))
        boost += SEED_BONUS * (w.crop in owned)
        k = (-gain / n * boost, sum(c in same for c in cells), -len(free), w.name, b.id, i)
        return k, cells, last

    # ponytail: lazy greedy. A stale key is only a hint; every pick is re-evaluated against the live state first.
    # A bed that has filled up since can score slightly better per cell (fewer cells, same shortfall); accepted.
    heap = [r[0] for i in range(len(wants)) for b in beds if (r := evaluate(i, b))]
    heapq.heapify(heap)
    out, used, done = [], set(), set()
    while heap:
        i, b = (key := heapq.heappop(heap))[-1], by_id[key[-2]]
        w = wants[i]
        if i in done or (w.crop, w.planted.year, w.planted.month) in used or not (fresh := evaluate(i, b)):
            continue
        if heap and fresh[0] > heap[0]:  # worse than the runner-up now: let it have a turn
            heapq.heappush(heap, fresh[0])
            continue
        _, cells, last = fresh
        done.add(i)
        used.add((w.crop, w.planted.year, w.planted.month))
        held[b.id] += [(c, w.planted, last, w.family, w.crop) for c in cells]
        kg = w.kg_per_m2 * (b.cell_cm / 100) ** 2 * len(cells)
        for week, k in needs.spread(today, w.harvest_from, w.harvest_to, kg).items():
            supply[w.food_group][week] += k
        out.append(_item(w, b, cells, last, kg=round(kg, 1)))
    names = {w.crop: w.name for w in all_wants}
    out += _flower_blocks(out, beds, held, [w for w in all_wants if w.cycle_days], flowers, today)
    for r in out:  # who touches it that season (a good companion), and the flowers that go with it
        if "companion_for" in r:
            continue
        b, start = by_id[r["bed_id"]], r["set_out_date"] or r["start_date"]
        cells = {tuple(c) for c in r["cells"]}
        edge = _touching(cells, b.cols, b.rows)
        grows = {crop for c, a, z, _, crop in held[b.id] if c in edge and crop and a <= r["until"] and start <= z}
        r["pairs_with"] = sorted(names.get(c, c.replace("-", " ").title()) for c in grows & good.get(r["crop"], set()))
        beside = sorted(
            {
                f["name"]
                for f in out
                if "companion_for" in f
                and f["bed_id"] == r["bed_id"]
                and f["start_date"] <= r["until"]
                and start <= f["until"]
                and r["name"] in f["companion_for"]
            }
        )
        r["flowers"] = beside  # planned in the same bed for it
        r["flower_hints"] = (
            [] if beside else [names.get(f, f.title()) for f in flowers.get(r["crop"], [])[:FLOWERS_SHOWN]]
        )
    return sorted(out, key=lambda r: (r["set_out_date"] or r["start_date"], r["name"])), supply


def _item(w: Want, b: Bed, cells: list[Cell], last: date, **extra) -> dict:
    p = layout.patch(b.cell_cm, w.dims)
    return {
        "crop": w.crop,
        "name": w.name,
        "method": w.method,
        "start_date": w.start,
        "set_out_date": w.set_out,
        "bed_id": b.id,
        "bed": b.name,
        "cells": [list(c) for c in sorted(cells, key=lambda c: (c[1], c[0]))],
        "plants": layout.plants_in(b.cell_cm, w.dims, len(cells)),
        "plants_per_cell": p.per,
        "cells_per_plant": p.cells if p.per == 1 else 1,
        "patch": [p.w, p.h],
        "harvest_from": w.harvest_from,
        "harvest_to": w.harvest_to,
        "until": last,
        "food_group": w.food_group,
        "kg": 0,
    } | extra


def _flower_blocks(out, beds, held, fwants, flowers, today) -> list[dict]:
    """A small stand of each crop's traditional companion flower, in the same bed, touching the crop's block and on the
    edge of the bed where it can, timed to bloom while the crop grows. One stand serves every crop in the bed that goes
    with that flower while it lasts. Needs the flower in the catalog with a sowing window; a crop whose flowers are
    missing or have no room simply gets none."""
    by_id = {b.id: b for b in beds}
    groups: dict[tuple[int, str, date], list] = {}  # (bed, crop, first day) -> [last day, cells]: one planting's block
    for bed_id, rows in held.items():
        for cell, a, z, _, crop in rows:
            if crop in flowers:
                g = groups.setdefault((bed_id, crop, a), [z, set()])
                g[0] = max(g[0], z)
                g[1].add(cell)
    names = {r["crop"]: r["name"] for r in out}
    placed: list[dict] = []
    for (bed_id, crop, a), (z, host_cells) in sorted(groups.items(), key=lambda kv: (kv[0][2], kv[0][:2])):
        b = by_id[bed_id]
        host = names.get(crop, crop.replace("-", " ").title())
        for slug in flowers[crop]:
            have = [
                f
                for f in placed
                if f["bed_id"] == bed_id and f["crop"] == slug and f["start_date"] <= z and a <= f["until"]
            ]
            if have:  # a stand of this flower already grows in the bed while this crop does
                have[0]["companion_for"] = sorted({*have[0]["companion_for"], host})
                break
            options = [
                w
                for w in fwants
                if w.crop == slug
                and a - timedelta(days=FLOWER_LEAD_DAYS) <= w.planted <= z - timedelta(days=FLOWER_BLOOM_AFTER)
            ]
            for w in sorted(options, key=lambda w: abs((w.planted - a).days)):
                last = layout.occupancy(w.start, w.set_out, None, "planned", w.cycle_days, today)[1]
                free = layout.free_cells(b.cols, b.rows, [(c, x, y) for c, x, y, _, _ in held[bed_id]], w.planted, last)
                reach = _touching(host_cells, b.cols, b.rows)

                def key(cells, reach=reach, b=b):
                    return (-len(reach & set(cells)), not _on_edge(cells, b.cols, b.rows))

                found = layout.best_block(b.cols, b.rows, free, layout.patch(b.cell_cm, w.dims), FLOWER_PATCHES, key)
                if not found:
                    continue
                cells, _ = found
                held[bed_id] += [(c, w.planted, last, "", w.crop) for c in cells]
                placed.append(
                    _item(w, b, cells, last, companion_for=[host], pairs_with=[], flowers=[], flower_hints=[])
                )
                break
            else:
                continue  # no window or no room for this flower: try the crop's next one
            break
    return placed
