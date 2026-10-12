"""Draft a year of plantings for a set of beds so they feed the household: greedy by the most new food per cell. Pure."""

from __future__ import annotations

import heapq
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from math import ceil

from . import layout, needs

CAP = 12  # most cells one crop takes in one go, so no crop swallows a bed
COMPANION_BONUS = 0.25  # per good companion already in the bed that season (at most two count): prefer that bed
FLOWERS_SHOWN = 2
MIN_GAIN = 1.0  # kg a placement must add toward a shortfall; below this it is not worth a planting


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
    footprint: float | None
    harvest_from: date
    harvest_to: date
    kg_per_m2: float | None = None  # per crop cycle; a want without it cannot be sized and is left out
    food_group: str | None = None


def block(free: list, n: int, k: int) -> list:
    """`n` free cells for plants that each need `k` cells: reading order for single-cell plants, otherwise a compact
    patch around the first free cell, so one plant's cells sit together."""
    if k == 1:
        return free[:n]
    c0, r0 = free[0]
    near = sorted(
        free, key=lambda c: (max(abs(c[0] - c0), c[1] - r0), abs(c[0] - c0) + c[1] - r0, c[0] < c0, c[1], c[0])
    )
    return near[:n]


def draft(
    beds: list[Bed],
    taken: dict[int, list],
    wants: list[Want],
    today: date,
    target: dict[str, float],
    existing: Sequence[tuple[str, float, date, date]] = (),
    companions: dict | None = None,
    kept: dict[int, list[tuple[str, date, date]]] | None = None,
) -> tuple[list[dict], dict[str, list[float]]]:
    """Place the crop that adds the most food per cell, again and again, until the weekly target is met or the beds
    are full. Returns the plantings and the weekly supply per food group (existing plantings included).
    `taken[bed_id]` = (cell, from, to, family) already held; `existing` = (group, kg, harvest from, harvest to) of
    plantings that stay. Rotation: cells that held the same family come last. Nothing is placed twice on overlapping
    days and a crop is not repeated in a month. `companions` = {"good": {crop: {crops}}, "avoid": ..., "flowers": ...}:
    a bed that already holds a good companion that season is preferred, and a crop never goes into a bed that holds
    one of its "avoid" crops at the same time. `kept[bed_id]` = (crop, from, to) of plantings that stay."""
    good, avoid = (companions or {}).get("good", {}), (companions or {}).get("avoid", {})
    flowers = (companions or {}).get("flowers", {})
    neighbours = {b.id: list((kept or {}).get(b.id, [])) for b in beds}  # who grows in each bed, and when
    held = {b.id: list(taken.get(b.id, [])) for b in beds}
    by_id = {b.id: b for b in beds}
    supply = {g: [0.0] * needs.WEEKS for g in needs.GROUPS}
    for g, kg, a, z in existing:
        for week, k in needs.spread(today, a, z, kg).items():
            supply[g][week] += k
    wants = [w for w in wants if w.kg_per_m2 and w.food_group in supply]

    def evaluate(i: int, b: Bed):
        """The best block of cells for want `i` in bed `b` right now, with its sort key; None when it adds too little."""
        w = wants[i]
        last = layout.occupancy(w.start, w.set_out, None, "planned", w.cycle_days, today)[1]
        free = layout.free_cells(b.cols, b.rows, [(c, a, z) for c, a, z, _ in held[b.id]], w.planted, last)
        weeks = needs.week_range(today, w.harvest_from, w.harvest_to)
        if not free or not weeks:
            return None
        same = {c for c, _, _, fam in held[b.id] if w.family and fam == w.family}
        near = {c for c, a, z in neighbours[b.id] if a <= last and w.planted <= z and c != w.crop}
        if near & avoid.get(w.crop, set()):
            return None  # a bad neighbour is in this bed at the same time
        free.sort(key=lambda c: c in same)
        harvest_weeks = max(1, (w.harvest_to - w.harvest_from).days // 7 + 1)
        per_week = w.kg_per_m2 * (b.cell_cm / 100) ** 2 / harvest_weeks  # kg a week from one cell
        short = [max(0.0, target[w.food_group] - supply[w.food_group][k]) for k in weeks]
        k = layout.cells_per_plant(b.cell_cm, w.footprint)  # cells one plant needs at its proper spacing
        n = max(k, min(max(CAP, k), len(free), ceil(sum(short) / len(short) / per_week - 1e-9)))
        n = min(ceil(n / k) * k, len(free) // k * k)  # whole plants only
        if n < k:
            return None
        chosen = block(free, n, k)
        gain = sum(min(n * per_week, s) for s in short)
        if gain < MIN_GAIN:
            return None
        pals = len(near & good.get(w.crop, set()))
        score = -gain / n * (1 + COMPANION_BONUS * min(2, pals))
        key = (score, sum(c in same for c in chosen), -len(free), w.name, b.id, i)
        return key, chosen, last

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
        held[b.id] += [(c, w.planted, last, w.family) for c in cells]
        neighbours[b.id].append((w.crop, w.planted, last))
        kg = w.kg_per_m2 * (b.cell_cm / 100) ** 2 * len(cells)
        for week, k in needs.spread(today, w.harvest_from, w.harvest_to, kg).items():
            supply[w.food_group][week] += k
        out.append(
            {
                "crop": w.crop,
                "name": w.name,
                "method": w.method,
                "start_date": w.start,
                "set_out_date": w.set_out,
                "bed_id": b.id,
                "bed": b.name,
                "cells": [list(c) for c in sorted(cells, key=lambda c: (c[1], c[0]))],
                "plants": layout.plants_in(b.cell_cm, w.footprint, len(cells)),
                "cells_per_plant": layout.cells_per_plant(b.cell_cm, w.footprint),
                "harvest_from": w.harvest_from,
                "harvest_to": w.harvest_to,
                "until": last,
                "food_group": w.food_group,
                "kg": round(kg, 1),
            }
        )
    names = {w.crop: w.name for w in wants}
    for r in out:  # who it shares the bed with that season, and flowers that are traditionally grown beside it
        start = r["set_out_date"] or r["start_date"]
        with_ = {
            c
            for c, a, z in neighbours[r["bed_id"]]
            if c in good.get(r["crop"], set()) and a <= r["until"] and start <= z
        }
        r["pairs_with"] = sorted(names.get(c, c.replace("-", " ").title()) for c in with_)
        r["flowers"] = [f for f in flowers.get(r["crop"], [])[:FLOWERS_SHOWN]]
    return sorted(out, key=lambda r: (r["set_out_date"] or r["start_date"], r["name"])), supply
