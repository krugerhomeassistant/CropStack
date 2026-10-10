"""Draft a year of plantings for a set of beds: greedy, one block of cells per crop per sowing window. Pure."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from . import layout

BLOCK = 6  # cells a crop starts with; shortcut: no yield targets yet, so every crop gets the same share. Upgrade with PLAN 8.2.


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


def draft(beds: list[Bed], taken: dict[int, list], wants: list[Want], today: date) -> list[dict]:
    """Place wants, earliest first (likelier first on a tie), in the bed with the most free ground for them.
    `taken[bed_id]` = (cell, from, to, family) already held by existing plantings. Rotation: cells that held the same
    family come last. Nothing is placed twice in a bed on overlapping days, and a crop is not repeated in a window."""
    held = {b.id: list(taken.get(b.id, [])) for b in beds}
    out, used = [], set()
    for w in sorted(wants, key=lambda w: (w.planted, -w.success, w.name)):
        first = w.planted
        last = layout.occupancy(w.start, w.set_out, None, "planned", w.cycle_days, today)[1]
        best = None
        for b in beds:
            free = layout.free_cells(b.cols, b.rows, [(c, a, z) for c, a, z, _ in held[b.id]], first, last)
            if not free:
                continue
            same = {c for c, _, _, fam in held[b.id] if w.family and fam == w.family}
            free.sort(key=lambda c: c in same)
            score = (-sum(c in same for c in free[:BLOCK]), len(free))
            if best is None or score > best[0]:
                best = (score, b, free[:BLOCK])
        if best is None or (w.crop, w.planted.year, w.planted.month) in used:
            continue
        _, b, cells = best
        used.add((w.crop, w.planted.year, w.planted.month))
        held[b.id] += [(c, first, last, w.family) for c in cells]
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
                "plants": layout.per_cell(b.cell_cm, w.footprint) * len(cells),
                "harvest_from": w.harvest_from,
                "harvest_to": w.harvest_to,
                "until": last,
            }
        )
    return sorted(out, key=lambda r: (r["set_out_date"] or r["start_date"], r["name"]))
