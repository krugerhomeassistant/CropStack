# Needs Model and Demand-Driven Year Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The owner enters how many people and draws beds; the year plan sizes every crop from what the household eats and reports how much of the need the beds cover.

**Architecture:** A pure `engine/needs.py` turns headcount into a weekly kg target per food group. `engine/yearplan.draft` is rewritten as a lazy-greedy loop that repeatedly places the crop block adding the most new food per cell, until targets are met or beds are full. The router feeds it per-crop `yield_per_m2` and `food_group` from the catalog, adds a coverage report and a "best change" (re-run with one extra 4 m² bed), and the Plan tab shows a coverage card with a people stepper.

**Tech Stack:** Python 3.13, FastAPI, SQLModel, pydantic, pytest, ruff (line length 120); React 19 + TypeScript + Tailwind; Playwright e2e (`frontend/scripts/e2e.mjs`).

**Spec:** `docs/superpowers/specs/2026-10-11-needs-model-design.md`

## Global Constraints

- Work on branch `claude/project-setup-f0c8f5`. Commit after every task. Commit message trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not put a model name anywhere else in commits, code or docs.
- Release is `v0.41.0` (minor). Version lives in `backend/app/__init__.py` and `frontend/package.json`; change it only with `python scripts/bump.py 0.41.0`.
- Basket: `BASKET_KG_PER_PERSON_DAY = 0.4` (WHO: at least 400 g of fruit and vegetables a day). Food groups and shares exactly: leafy .20, fruiting .20, root .15, brassica .12, legume .10, squash .10, allium .08, herb .05 (sum 1.0).
- `people` is an integer 1 to 20, default 2, stored in `Household.settings` (JSON). No DB migration.
- Catalog values need `sources` or `estimate: true` (`Value.cited`). Every `yield_per_m2` in this slice is an estimate: `evidence: traditional`, `confidence: low`, `estimate: true`, a `qualifiers.basis` string. Never invent a source.
- Catalog schema files in `catalog/schema/` are generated: after changing `backend/app/catalog.py` run `python scripts/catalog_schema.py`; CI runs it with `--check`.
- User-visible frontend strings go through `t()` (`frontend/src/i18n.ts`); English only for now.
- Pure engine modules (`backend/app/engine/*`) import nothing from FastAPI or the DB.
- No new dependencies.
- README and WIKI are refreshed on every release (standing requirement in `docs/ACTIVE_CONTEXT.md`).

## Review Focus

Input classes the spec implies but the happy path does not exercise (each has a test in the task that owns it):

1. A data-source toggle in Settings must not reset `people`. `DataSources.tsx` PUTs an object holding only the two switches, and `save_settings` replaces the whole settings dict. (Task 4: `PUT /household/settings` merges; test)
2. `people` of 0, 21 or a non-number is rejected with 422, not stored. (Task 4: test)
3. A crop with no `yield_per_m2` or `food_group` is never silently dropped: it is listed in `skipped_no_yield`. (Task 4: test; Task 2: engine leaves it out)
4. A household that already grows food: existing live plantings count toward supply, so a garden that already covers fruiting gets no more fruiting. (Task 2: engine test; Task 4: helper test)
5. Harvest windows entirely in the past, or beyond 52 weeks, must not crash or add supply. (Task 1 and Task 2 tests)
6. A viewer or member cannot change `people` (PUT is owner-only); the stepper is hidden for them. (Task 5)

## File Structure

| File | Responsibility |
|---|---|
| `backend/app/engine/needs.py` (new) | Basket, food groups, weekly targets, harvest spreading, coverage maths. Pure. |
| `backend/app/engine/yearplan.py` (rewrite `draft`) | Lazy-greedy demand-driven placement. Pure. |
| `backend/app/engine/layout.py` (add `yield_per_m2`) | Read the yield number from a catalog item, next to `footprint_m2`. |
| `backend/app/catalog.py` | `Crop.food_group` field. |
| `catalog/crops/*.yaml` (60 files) | `food_group` and `params.yield_per_m2`. |
| `catalog/schema/crop.json` | Regenerated. |
| `backend/app/routers/household.py` | `HouseholdSettings.people`; PUT merges. |
| `backend/app/routers/beds.py` (`crop_facts`) | Expose `yield_per_m2`, `food_group`. |
| `backend/app/routers/plan.py` | Wire needs, wants, existing supply, coverage, best change. |
| `scripts/coverage.py` | Report missing `yield_per_m2` / `food_group`. |
| `frontend/src/api.ts` | Types for coverage, people. |
| `frontend/src/components/CoverageCard.tsx` (new) | People stepper, overall %, bar per group, best change. |
| `frontend/src/components/YearPlan.tsx` | Show the card, redraft after people change. |
| `backend/tests/test_needs.py`, `test_yearplan.py` (new) | Engine tests. |
| `backend/tests/test_beds.py`, `test_household.py`, `test_catalog.py`, `fixtures/catalog/crops/testcrop.yaml` | Updated for new behaviour. |
| `frontend/scripts/e2e.mjs` | Coverage card step. |
| `CHANGELOG.md`, `README.md`, `docs/WIKI.md`, `docs/ACTIVE_CONTEXT.md`, `docs/PLAN.md`, `docs/COVERAGE.md` | Release docs. |

Run all Python commands from the repo root. Test command: `python -m pytest -q backend/tests/<file>`. Lint: `ruff check . && ruff format --check .` (run `ruff format .` to fix).

---

### Task 1: Needs engine (pure)

**Files:**
- Create: `backend/app/engine/needs.py`
- Test: `backend/tests/test_needs.py`

**Interfaces:**
- Produces:
  - `needs.GROUPS: tuple[str, ...]`, `needs.GROUP_SHARE: dict[str, float]`, `needs.WEEKS = 52`, `needs.BASKET_KG_PER_PERSON_DAY = 0.4`
  - `needs.weekly_target(people: int) -> dict[str, float]` (kg per week per group)
  - `needs.week_range(today: date, first: date, last: date) -> range` (week numbers 0..51 a harvest touches; empty if none)
  - `needs.spread(today, first, last, kg) -> dict[int, float]` (kg per week number, inside the year only)
  - `needs.coverage(target, supply, today) -> {"overall": float, "groups": {g: {"target_kg","supply_kg","covered","weeks_short"}}}` where `supply: dict[str, list[float]]` has 52 weekly values per group.

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_needs.py`:

```python
from datetime import date, timedelta

from app.engine import needs

TODAY = date(2026, 10, 10)


def test_targets_scale_with_people_and_the_shares_cover_the_basket():
    assert abs(sum(needs.GROUP_SHARE.values()) - 1) < 1e-9
    one, four = needs.weekly_target(1), needs.weekly_target(4)
    assert all(abs(four[g] - 4 * one[g]) < 1e-9 for g in needs.GROUPS)
    assert abs(sum(one.values()) - 2.8) < 1e-9  # 0.4 kg a day for a week


def test_a_harvest_is_spread_evenly_over_its_weeks():
    got = needs.spread(TODAY, TODAY + timedelta(days=14), TODAY + timedelta(days=27), 4.0)
    assert got == {2: 2.0, 3: 2.0}


def test_a_harvest_is_clipped_to_the_year_and_the_past_counts_for_nothing():
    late = needs.spread(TODAY, TODAY + timedelta(days=357), TODAY + timedelta(days=400), 7.0)
    assert late == {51: 1.0}  # seven weeks of harvest, one of them inside the year
    assert needs.spread(TODAY, TODAY - timedelta(days=30), TODAY - timedelta(days=1), 5.0) == {}


def test_coverage_counts_each_week_only_up_to_its_target():
    target = {g: 1.0 for g in needs.GROUPS}
    supply = {g: [0.0] * needs.WEEKS for g in needs.GROUPS}
    supply["leafy"] = [3.0] * 26 + [0.0] * 26  # a glut, then nothing: the glut does not cover the gap
    cov = needs.coverage(target, supply, TODAY)
    assert cov["groups"]["leafy"]["covered"] == 0.5
    assert cov["groups"]["leafy"]["weeks_short"][0] == (TODAY + timedelta(weeks=26)).isoformat()
    assert cov["groups"]["herb"]["covered"] == 0.0
    assert cov["overall"] == 0.1  # leafy is a fifth of the basket, half covered
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest -q backend/tests/test_needs.py`
Expected: FAIL, `ImportError: cannot import name 'needs'`.

- [ ] **Step 3: Write the implementation**

Create `backend/app/engine/needs.py`:

```python
"""What a household eats: a weekly target of produce per food group, and how much of it a supply meets. Pure."""

from __future__ import annotations

from datetime import date, timedelta

BASKET_KG_PER_PERSON_DAY = 0.4  # WHO: at least 400 g of fruit and vegetables a day
GROUP_SHARE = {  # our own split of that basket, by how a crop is eaten; not nutrition advice
    "leafy": 0.20,
    "fruiting": 0.20,
    "root": 0.15,
    "brassica": 0.12,
    "legume": 0.10,
    "squash": 0.10,
    "allium": 0.08,
    "herb": 0.05,
}
GROUPS = tuple(GROUP_SHARE)
WEEKS = 52


def weekly_target(people: int) -> dict[str, float]:
    """Kilograms of each group the household eats in a week."""
    return {g: people * 7 * BASKET_KG_PER_PERSON_DAY * s for g, s in GROUP_SHARE.items()}


def week_range(today: date, first: date, last: date) -> range:
    """Week numbers (0 = the week starting today) that a harvest from `first` to `last` touches, inside the year."""
    return range(max(0, (first - today).days // 7), min(WEEKS - 1, (last - today).days // 7) + 1)


def spread(today: date, first: date, last: date, kg: float) -> dict[int, float]:
    """`kg` harvested evenly from `first` to `last`: kg per week number, for the weeks inside the year only.
    ponytail: even spread; a real harvest curve (slow start, peak, tail) needs crop data we do not have."""
    weeks = max(1, (last - first).days // 7 + 1)
    return {w: kg / weeks for w in week_range(today, first, last)}


def coverage(target: dict[str, float], supply: dict[str, list[float]], today: date) -> dict:
    """How much of the weekly target the supply meets. A surplus one week does not make up for a gap in another."""
    groups, overall = {}, 0.0
    for g in GROUPS:
        need = target[g] * WEEKS
        covered = sum(min(s, target[g]) for s in supply[g]) / need if need else 1.0
        overall += GROUP_SHARE[g] * covered
        groups[g] = {
            "target_kg": round(need, 1),
            "supply_kg": round(sum(supply[g]), 1),
            "covered": round(covered, 3),
            "weeks_short": [
                (today + timedelta(weeks=i)).isoformat() for i, s in enumerate(supply[g]) if s < target[g] * 0.5
            ],
        }
    return {"overall": round(overall, 3), "groups": groups}
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest -q backend/tests/test_needs.py && ruff check backend/app/engine/needs.py backend/tests/test_needs.py && ruff format --check backend/app/engine/needs.py backend/tests/test_needs.py`
Expected: 4 passed, ruff clean (run `ruff format` on the two files if it complains).

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/needs.py backend/tests/test_needs.py
git commit -m "Add the needs engine: weekly food-group targets and coverage" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Demand-driven drafter

**Files:**
- Modify: `backend/app/engine/yearplan.py` (full rewrite, shown below)
- Modify: `backend/tests/test_beds.py` (delete `test_the_drafter_rotates_and_never_double_books_cells`, lines ~203-222; it is replaced)
- Test: `backend/tests/test_yearplan.py` (new)

**Interfaces:**
- Consumes: `needs.GROUPS`, `needs.WEEKS`, `needs.week_range`, `needs.spread` (Task 1); `layout.free_cells`, `layout.occupancy`, `layout.per_cell` (existing).
- Produces:
  - `Want` gains two trailing defaults: `kg_per_m2: float | None = None`, `food_group: str | None = None`. All 12 earlier fields unchanged and positional.
  - `draft(beds, taken, wants, today, target, existing=()) -> tuple[list[dict], dict[str, list[float]]]`: the plantings and the weekly supply per group (existing included). Each planting dict keeps its old keys and gains `food_group: str` and `kg: float`.
  - `existing` items are `(group, kg, harvest_from, harvest_to)`.
  - A want with falsy `kg_per_m2` or a `food_group` outside `needs.GROUPS` is left out (the router reports these).

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_yearplan.py`:

```python
from datetime import date, timedelta

from app.engine import needs
from app.engine.yearplan import Bed, Want, draft

TODAY = date(2026, 10, 10)
CROPS = {  # crop: (food group, kg per m2 per cycle, days in the ground)
    "lettuce": ("leafy", 3.0, 60),
    "tomato": ("fruiting", 8.0, 120),
    "carrot": ("root", 4.0, 90),
    "kale": ("brassica", 3.0, 100),
    "pea": ("legume", 1.2, 80),
    "zucchini": ("squash", 8.0, 80),
    "onion": ("allium", 3.0, 120),
    "basil": ("herb", 1.0, 60),
}


def want(crop, group, planted, kg=4.0, family="", days=60):
    harvest = planted + timedelta(days=days - 20)
    return Want(
        crop, crop, family, "direct", planted, None, planted, days, 0.9, None,
        harvest, harvest + timedelta(days=21), kg, group,
    )  # fmt: skip


YEAR = [want(c, g, TODAY + timedelta(days=30 * m), kg, days=d) for m in range(12) for c, (g, kg, d) in CROPS.items()]


def cells(items):
    return sum(len(i["cells"]) for i in items)


def run(people, beds, taken=None, wants=YEAR, existing=()):
    grid = [Bed(i, f"B{i}", 12, 8, 30) for i in range(1, beds + 1)]
    return draft(grid, taken or {}, wants, TODAY, needs.weekly_target(people), list(existing))


def test_more_people_plant_more_until_the_target_is_met():
    assert cells(run(4, 3)[0]) > cells(run(1, 3)[0])
    assert cells(run(1, 3)[0]) == cells(run(1, 8)[0])  # a household of one is fed: more ground adds nothing


def test_nothing_is_double_booked_and_the_draft_is_repeatable():
    items, _ = run(2, 2)
    assert items == run(2, 2)[0]
    for bed in (1, 2):
        held = [
            (tuple(c), i["set_out_date"] or i["start_date"], i["until"])
            for i in items
            if i["bed_id"] == bed
            for c in i["cells"]
        ]
        for n, (cell, a, z) in enumerate(held):
            assert not any(cell == c and a <= y and b <= z for c, b, y in held[n + 1 :])


def test_cells_that_held_the_same_family_come_last_so_crops_rotate():
    one_tomato = [want("tomato", "fruiting", TODAY, kg=8.0, family="Solanaceae")]
    every_cell = [((c, r), date(2026, 5, 1), date(2026, 10, 1), "Solanaceae") for c in range(12) for r in range(8)]
    assert {i["bed_id"] for i in run(4, 2, wants=one_tomato)[0]} == {1}
    assert {i["bed_id"] for i in run(4, 2, {1: every_cell}, one_tomato)[0]} == {2}


def test_a_crop_with_no_yield_or_group_is_left_out():
    bare = [want("mystery", None, TODAY, kg=None), want("nogroup", None, TODAY)]
    assert run(4, 1, wants=bare)[0] == []


def test_what_already_grows_counts_toward_the_target():
    glut = [("fruiting", 5000.0, TODAY, TODAY + timedelta(days=360))]
    items, supply = run(4, 3, existing=glut)
    assert not [i for i in items if i["food_group"] == "fruiting"]
    assert supply["fruiting"][10] > 0


def test_harvests_outside_the_year_are_ignored():
    gone = [want("lettuce", "leafy", TODAY - timedelta(days=200)), want("kale", "brassica", TODAY + timedelta(days=500))]
    assert run(4, 1, wants=gone)[0] == []
```

Then open `backend/tests/test_beds.py` and delete the whole function `test_the_drafter_rotates_and_never_double_books_cells` (from its `def` line up to the blank lines before `def test_many_plantings_at_once_all_succeed`). Its rotation and no-double-booking checks now live in `test_yearplan.py`.

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest -q backend/tests/test_yearplan.py`
Expected: FAIL (`TypeError`: `draft()` takes 4 positional arguments / `Want` has no `kg_per_m2`).

- [ ] **Step 3: Rewrite the drafter**

Replace the whole content of `backend/app/engine/yearplan.py` with:

```python
"""Draft a year of plantings for a set of beds so they feed the household: greedy by the most new food per cell. Pure."""

from __future__ import annotations

import heapq
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from math import ceil

from . import layout, needs

CAP = 12  # most cells one crop takes in one go, so no crop swallows a bed
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


def draft(
    beds: list[Bed],
    taken: dict[int, list],
    wants: list[Want],
    today: date,
    target: dict[str, float],
    existing: Sequence[tuple[str, float, date, date]] = (),
) -> tuple[list[dict], dict[str, list[float]]]:
    """Place the crop that adds the most food per cell, again and again, until the weekly target is met or the beds
    are full. Returns the plantings and the weekly supply per food group (existing plantings included).
    `taken[bed_id]` = (cell, from, to, family) already held; `existing` = (group, kg, harvest from, harvest to) of
    plantings that stay. Rotation: cells that held the same family come last. Nothing is placed twice on overlapping
    days and a crop is not repeated in a month."""
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
        free.sort(key=lambda c: c in same)
        harvest_weeks = max(1, (w.harvest_to - w.harvest_from).days // 7 + 1)
        per_week = w.kg_per_m2 * (b.cell_cm / 100) ** 2 / harvest_weeks  # kg a week from one cell
        short = [max(0.0, target[w.food_group] - supply[w.food_group][k]) for k in weeks]
        n = max(1, min(CAP, len(free), ceil(sum(short) / len(short) / per_week - 1e-9)))
        gain = sum(min(n * per_week, s) for s in short)
        if gain < MIN_GAIN:
            return None
        key = (-gain / n, sum(c in same for c in free[:n]), -len(free), w.name, b.id, i)
        return key, free[:n], last

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
                "plants": layout.per_cell(b.cell_cm, w.footprint) * len(cells),
                "harvest_from": w.harvest_from,
                "harvest_to": w.harvest_to,
                "until": last,
                "food_group": w.food_group,
                "kg": round(kg, 1),
            }
        )
    return sorted(out, key=lambda r: (r["set_out_date"] or r["start_date"], r["name"])), supply
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest -q backend/tests/test_yearplan.py backend/tests/test_needs.py backend/tests/test_beds.py && ruff check backend && ruff format --check backend`
Expected: all pass, ruff clean. `plan.py` still calls the old `draft` signature, so `test_beds.py` year-plan API tests that hit `GET /plan/year` with a site could fail; the existing ones only hit the no-site path and accept path, so they pass. Task 4 fixes the router. If ruff format wants changes in the files you wrote, run `ruff format` on them.

- [ ] **Step 5: Commit**

```bash
git add backend/app/engine/yearplan.py backend/tests/test_yearplan.py backend/tests/test_beds.py
git commit -m "Draft the year plan from what the household eats, not a fixed block" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Catalog fields and data for all 60 crops

**Files:**
- Modify: `backend/app/catalog.py:176-181` (the `Crop` model)
- Modify: `backend/app/engine/layout.py` (add `yield_per_m2`)
- Modify: `catalog/crops/*.yaml` (60 files, via a throwaway script kept outside the repo)
- Modify: `catalog/schema/crop.json` (regenerated)
- Modify: `backend/tests/fixtures/catalog/crops/testcrop.yaml`
- Modify: `scripts/coverage.py`, `docs/COVERAGE.md` (regenerated)
- Test: `backend/tests/test_catalog.py`, `backend/tests/test_beds.py` (small unit test for `yield_per_m2`)

**Interfaces:**
- Produces:
  - `Crop.food_group: Literal["leafy", "fruiting", "root", "brassica", "legume", "squash", "allium", "herb"] | None = None` (the same names as `needs.GROUPS`).
  - `layout.yield_per_m2(item: dict) -> float | None` (a positive number or None).
  - Every real crop YAML has a top-level `food_group` and `params.yield_per_m2`.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_catalog.py` (it already imports `cat` and `REPO`):

```python
def test_every_crop_says_how_it_is_eaten_and_roughly_what_it_yields():
    from app.engine import layout, needs

    c = cat.load(REPO / "catalog")
    crops = list(c.list("crop"))
    assert crops
    for slug, item in crops:
        assert item.get("food_group") in needs.GROUPS, slug
        assert layout.yield_per_m2(item), slug
```

Append to `backend/tests/test_beds.py`:

```python
def test_yield_reads_a_positive_number_and_nothing_else():
    from app.engine.layout import yield_per_m2

    item = lambda v: {"params": {"yield_per_m2": {"value": v, "unit": "kg/m2"}}}  # noqa: E731
    assert yield_per_m2(item(8.0)) == 8.0
    assert yield_per_m2(item(0)) is None
    assert yield_per_m2(item(True)) is None
    assert yield_per_m2(item({"min": 1, "max": 2})) is None
    assert yield_per_m2({}) is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest -q backend/tests/test_catalog.py backend/tests/test_beds.py -k "eaten or yield"`
Expected: FAIL (`KeyError: 'food_group'`; `ImportError: yield_per_m2`).

- [ ] **Step 3: Model, reader, fixture**

In `backend/app/catalog.py` add above `class Crop` and change the model:

```python
class Crop(Item):
    kind: Literal["crop"]
    scientific_name: str
    family: str  # APG IV family, e.g. Solanaceae
    rotation_group: str | None = None
    life_cycle: Literal["annual", "biennial", "perennial"]
    food_group: Literal["leafy", "fruiting", "root", "brassica", "legume", "squash", "allium", "herb"] | None = None
```

(The `Literal` is spelled out so the generated JSON schema lists the values; the catalog test below checks it stays in step with `needs.GROUPS`.)

In `backend/app/engine/layout.py`, directly after `footprint_m2`, add:

```python
def yield_per_m2(item: dict) -> float | None:
    """Kilograms harvested per m² over one crop cycle; None when the catalog has no single positive number."""
    fact = _fact(item, "params", "yield_per_m2")
    value = fact.get("value") if fact else None
    if not isinstance(value, int | float) or isinstance(value, bool) or value <= 0:
        return None
    return float(value)
```

In `backend/tests/fixtures/catalog/crops/testcrop.yaml` add `food_group: fruiting` after the `life_cycle: annual` line, and under `params:` add (aligned with the other params, two-space indent):

```yaml
  yield_per_m2: {value: 5, unit: kg/m2, evidence: grower-reported, confidence: low, estimate: true}
```

Regenerate schemas: `python scripts/catalog_schema.py` (rewrites `catalog/schema/crop.json`).

- [ ] **Step 4: Add the data to the 60 crops with a throwaway script**

Create the script in the scratchpad directory (NOT in the repo): `<scratchpad>/add_needs_data.py`. It inserts text lines, so it keeps every file's existing formatting, and it is idempotent.

```python
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])  # repo root
GROUPS = {
    "leafy": "spinach lettuce rocket swiss-chard endive mustard-greens pak-choi watercress celery asparagus",
    "brassica": "broccoli brussels-sprouts cabbage cauliflower kale kohlrabi",
    "fruiting": "tomato chilli sweet-pepper eggplant okra sweet-corn strawberry globe-artichoke rhubarb",
    "squash": "cucumber melon watermelon pumpkin zucchini",
    "root": "beetroot carrot celeriac parsnip potato radish swede sweet-potato turnip jerusalem-artichoke horseradish fennel",
    "legume": "pea green-bean runner-bean broad-bean",
    "allium": "onion shallot garlic leek chives",
    "herb": "basil coriander dill mint oregano parsley rosemary sage thyme",
}
YIELD = {  # kg per m2 per crop cycle, typical home garden; estimates
    "asparagus": 0.6, "basil": 1.0, "beetroot": 3.0, "broad-bean": 1.5, "broccoli": 1.5, "brussels-sprouts": 1.5,
    "cabbage": 4.0, "carrot": 4.0, "cauliflower": 2.0, "celeriac": 3.0, "celery": 5.0, "chilli": 1.5, "chives": 1.5,
    "coriander": 1.0, "cucumber": 6.0, "dill": 1.0, "eggplant": 3.5, "endive": 2.5, "fennel": 3.0, "garlic": 1.0,
    "globe-artichoke": 1.0, "green-bean": 2.0, "horseradish": 1.5, "jerusalem-artichoke": 3.0, "kale": 3.0,
    "kohlrabi": 3.0, "leek": 3.5, "lettuce": 3.0, "melon": 3.0, "mint": 1.5, "mustard-greens": 2.5, "okra": 1.5,
    "onion": 3.0, "oregano": 1.0, "pak-choi": 3.0, "parsley": 2.0, "parsnip": 2.5, "pea": 1.2, "potato": 4.0,
    "pumpkin": 3.5, "radish": 2.0, "rhubarb": 3.0, "rocket": 1.5, "rosemary": 1.0, "runner-bean": 3.0, "sage": 1.0,
    "shallot": 2.0, "spinach": 2.0, "strawberry": 1.5, "swede": 4.0, "sweet-corn": 1.0, "sweet-pepper": 3.0,
    "sweet-potato": 2.5, "swiss-chard": 4.0, "thyme": 1.0, "tomato": 8.0, "turnip": 3.0, "watercress": 2.0,
    "watermelon": 3.0, "zucchini": 8.0,
}
group_of = {slug: g for g, slugs in GROUPS.items() for slug in slugs.split()}
files = sorted((ROOT / "catalog" / "crops").glob("*.yaml"))
assert len(files) == 60 == len(group_of) == len(YIELD), (len(files), len(group_of), len(YIELD))
BLOCK = """  yield_per_m2:
    value: {v}
    unit: kg/m2
    evidence: traditional
    confidence: low
    estimate: true
    qualifiers: {{basis: 'typical home-garden yield per crop cycle; replace with an extension-service figure'}}
"""
for f in files:
    slug = f.stem
    text = f.read_text(encoding="utf-8", newline="")  # keep line endings as they are
    nl = "\r\n" if "\r\n" in text else "\n"
    if "\nfood_group:" in text:
        continue
    lines = text.split(nl)
    i = next(n for n, l in enumerate(lines) if l.startswith("life_cycle:"))
    lines.insert(i + 1, f"food_group: {group_of[slug]}")
    j = next(n for n, l in enumerate(lines) if l == "params:")
    lines[j + 1 : j + 1] = BLOCK.format(v=YIELD[slug]).rstrip("\n").split("\n")
    f.write_text(nl.join(lines), encoding="utf-8", newline="")
print("done", len(files))
```

Run it from the repo root: `python <scratchpad>/add_needs_data.py .` Expected: `done 60`. Then `git diff --stat catalog/crops | tail -1` should show 60 files changed with 9 insertions each.

If the assertion on counts fails, a slug in the script does not match a file name: fix the script's table (the directory listing is the truth) and rerun.

- [ ] **Step 5: Coverage report**

In `scripts/coverage.py` add to `CROP_FIELDS` (after `"params.cycle_days"`): `"params.yield_per_m2"`. Run `python scripts/coverage.py` (regenerates `docs/COVERAGE.md`). `food_group` is a plain string, not a cited fact, so it is not a coverage row; the catalog test enforces it.

- [ ] **Step 6: Run to verify it passes**

Run: `python -m pytest -q backend/tests && python scripts/catalog_schema.py --check && python scripts/coverage.py --check && ruff check . && ruff format --check .`
Expected: all green (if `--check` for coverage reports stale, run `python scripts/coverage.py` and include `docs/COVERAGE.md`).

- [ ] **Step 7: Commit**

```bash
git add backend catalog scripts docs/COVERAGE.md
git commit -m "Catalog: food group and estimated yield per m2 for the 60 crops" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: People setting and the plan endpoint

**Files:**
- Modify: `backend/app/routers/household.py:34-38,125-132` (`HouseholdSettings`, `save_settings`)
- Modify: `backend/app/routers/beds.py:55-66` (`crop_facts`)
- Modify: `backend/app/routers/plan.py` (`year_plan` and a helper)
- Test: `backend/tests/test_household.py`, `backend/tests/test_beds.py`

**Interfaces:**
- Consumes: `needs.*` (Task 1), `yearplan.draft`/`Want` (Task 2), `layout.yield_per_m2` and crop YAML fields (Task 3).
- Produces:
  - `HouseholdSettings.people: int = Field(2, ge=1, le=20)`. `PUT /household/settings` merges the sent fields into the stored dict (fields not sent are kept) and returns the full settings.
  - `crop_facts(...)` result gains `"yield_per_m2": float | None` and `"food_group": str | None`.
  - `GET /plan/year` returns, in addition to today's keys: `people: int`, and when a site and beds exist `coverage: {overall, groups, best_change}`, `skipped_no_yield: list[str]`; each item gains `food_group`, `kg`. With no site or no beds it returns `people` but no `coverage`.
  - `plan.py` helper `existing_supply(plantings, facts_of, beds_by_id, window_of, today) -> list[tuple[str, float, date, date]]`, where `facts_of(crop) -> dict` and `window_of(planting) -> (first, last)` are callables so the helper needs no database.

- [ ] **Step 1: Write the failing tests**

Append to `backend/tests/test_household.py` (it has the `owner` fixture):

```python
def test_people_default_to_two_and_a_switch_does_not_reset_them(owner):
    assert owner.get("/api/v1/household/settings").json()["people"] == 2
    assert owner.put("/api/v1/household/settings", json={"people": 5}).json()["people"] == 5
    after = owner.put("/api/v1/household/settings", json={"forecast": False}).json()  # what Settings → Data sources sends
    assert after == {"forecast": False, "place_search": True, "people": 5}
    assert owner.get("/api/v1/household/settings").json()["people"] == 5


@pytest.mark.parametrize("bad", [0, 21, "many", 2.5, None])
def test_people_must_be_a_whole_number_from_one_to_twenty(owner, bad):
    assert owner.put("/api/v1/household/settings", json={"people": bad}).status_code == 422
```

(`pytest` is already imported in that file; the fixture is defined there.)

Append to `backend/tests/test_beds.py`:

```python
def test_the_plan_knows_how_many_people_it_feeds_and_how_much_that_is(owner):  # noqa: F811
    assert owner.get("/api/v1/plan/year").json()["people"] == 2
    owner.put("/api/v1/household/settings", json={"people": 6})
    assert owner.get("/api/v1/plan/year").json()["people"] == 6


def test_what_already_grows_is_counted_as_supply_from_its_last_third():
    from datetime import date

    from app.routers.plan import existing_supply

    class P:  # the few planting fields the helper reads
        def __init__(self, crop, bed_id, cells, status="growing"):
            self.crop, self.bed_id, self.cells, self.status = crop, bed_id, cells, status

    class B:
        cell_cm = 30

    today = date(2026, 10, 10)
    facts = {"tomato": {"yield_per_m2": 8.0, "food_group": "fruiting"}, "mystery": {"yield_per_m2": None, "food_group": None}}
    window = lambda p: (date(2026, 9, 10), date(2026, 12, 10))  # noqa: E731  (91 days)
    got = existing_supply(
        [P("tomato", 1, [[0, 0], [1, 0]]), P("tomato", 1, [], "growing"), P("mystery", 1, [[0, 0]]), P("tomato", 1, [[0, 0]], "finished")],
        lambda crop: facts[crop], {1: B()}, window, today,
    )  # fmt: skip
    assert len(got) == 1  # no cells, no yield and finished plantings add nothing
    group, kg, first, last = got[0]
    assert (group, round(kg, 2), last) == ("fruiting", round(8.0 * 0.09 * 2, 2), date(2026, 12, 10))
    assert first > date(2026, 11, 8)  # the last 30% of the 91 days
```

`existing_supply` takes the facts and window as callables so it stays testable without a database.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest -q backend/tests/test_household.py backend/tests/test_beds.py -k "people or supply"`
Expected: FAIL (`KeyError: 'people'`, `ImportError: existing_supply`).

- [ ] **Step 3: Household settings**

In `backend/app/routers/household.py` change the model and the PUT:

```python
class HouseholdSettings(BaseModel):
    """Household-wide switches and the head count the year plan feeds. Turning a source off stops every call to it."""

    forecast: bool = True
    place_search: bool = True
    people: int = Field(2, ge=1, le=20)  # how many the garden should feed (PLAN 8.2)
```

(`Field` must be imported from pydantic: `from pydantic import BaseModel, Field` — check the file's existing import line and extend it.) Replace `save_settings` with a merge so a partial PUT keeps the rest:

```python
@router.put("/household/settings")
def save_settings(body: HouseholdSettings, owner: OwnerDep, db: SessionDep) -> HouseholdSettings:
    household = db.get(Household, owner.household_id)
    assert household
    merged = HouseholdSettings(**(household.settings | body.model_dump(exclude_unset=True)))
    household.settings = merged.model_dump()
    db.add(household)
    db.commit()
    return merged
```

`exclude_unset=True` tells a field the caller left out (kept as stored) from one it sent, and `{"people": null}` fails the `int` check with 422. Add `Field` to the pydantic import (`from pydantic import BaseModel, Field`). `get_settings` and `household_settings` are unchanged (stored dicts without `people` default to 2).

- [ ] **Step 4: Crop facts**

In `backend/app/routers/beds.py` `crop_facts`, add two keys to the cached dict:

```python
            "yield_per_m2": layout.yield_per_m2(item),
            "food_group": item.get("food_group"),
```

and update its docstring to say it also reads yield and food group.

- [ ] **Step 5: The plan endpoint**

In `backend/app/routers/plan.py`:

1. Imports: add `needs` to `from ..engine import ...`; add `Household` to the models import; add `from .household import household_settings`; add `from datetime import date` is already covered by the existing `datetime` import line (extend it: `from datetime import UTC, date, datetime, timedelta`).

2. Add near the top (after `MIN_SUCCESS`):

```python
EXTRA_BED = yearplan.Bed(-1, "Extra bed", 7, 7, 30)  # 7 x 7 cells of 30 cm, about 4 m²
EXTRA_M2 = 4
ENOUGH = 0.95  # coverage at which no further change is suggested
```

3. Add the helper:

```python
def existing_supply(plantings, facts_of, beds_by_id, window_of, today: date) -> list[tuple[str, float, date, date]]:
    """Food that plantings already in the ground will give: (group, kg, harvest from, harvest to).
    ponytail: the harvest is taken as the last 30% of the days a planting holds its cells; a real per-planting
    outlook (`plantings.outlook`) could replace it."""
    out = []
    for p in plantings:
        f, bed = facts_of(p.crop), beds_by_id.get(p.bed_id)
        if bed is None or not p.cells or p.status in ("finished", "failed") or not f["yield_per_m2"] or not f["food_group"]:
            continue
        first, last = window_of(p)
        if last < today:
            continue
        kg = f["yield_per_m2"] * (bed.cell_cm / 100) ** 2 * len(p.cells)
        out.append((f["food_group"], kg, max(first, first + (last - first) * 0.7), last))
    return out
```

4. In `year_plan`:
   - After loading `site`/`beds`: `people = household_settings(db.get(Household, me.household_id)).people`.
   - The early return (no site or no beds) gains `"people": people`.
   - Build `Want`s with the two new fields: append `f["yield_per_m2"], f["food_group"]` after the `planted + timedelta(days=days)` argument of `yearplan.Want(...)` (positional order: after `harvest_to`).
   - Collect `skipped = sorted({w.crop for w in wants if not (w.kg_per_m2 and w.food_group in needs.GROUPS)})`.
   - Replace the final return with:

```python
    target = needs.weekly_target(people)
    beds_by_id = {b.id: b for b in beds}
    existing = existing_supply(
        [p for p in plantings if not replaceable(p)],
        lambda crop: crop_facts(db, c, me.household_id, crop, cache),
        beds_by_id,
        lambda p: holds(p, crop_facts(db, c, me.household_id, p.crop, cache), today),
        today,
    )
    grid = [yearplan.Bed(b.id, b.name, *grid_of(b), b.cell_cm) for b in beds]
    items, supply = yearplan.draft(grid, taken, wants, today, target, existing)
    cov = needs.coverage(target, supply, today)
    cov["best_change"] = None
    if cov["overall"] < ENOUGH:
        _, more = yearplan.draft([*grid, EXTRA_BED], taken, wants, today, target, existing)
        gain = needs.coverage(target, more, today)["overall"] - cov["overall"]
        if gain >= 0.01:
            cov["best_change"] = {"kind": "add_bed_area", "m2": EXTRA_M2, "gain": round(gain, 3)}
    return {
        "garden": True,
        "beds": True,
        "today": today,
        "scheduled": sum(replaceable(p) for p in plantings),
        "people": people,
        "items": items,
        "coverage": cov,
        "skipped_no_yield": skipped,
    }
```

   Remove the old `grid = ...` line that sat above the old return (it moved into the block above).

5. Add this end-to-end router test to `backend/tests/test_beds.py` (imports at the top of the file: `from app import external`, `from tests.test_auth_garden import GARDEN`, `from tests.test_climate import synthetic`; `date` from `datetime`). It runs the whole path, so it catches wiring mistakes the unit tests cannot:

```python
def test_the_plan_reports_coverage_and_targets_scale_with_people(owner, monkeypatch):  # noqa: F811
    monkeypatch.setattr(external, "fetch_climate_archive", lambda lat, lon: synthetic(mean=14, amplitude=7, coldest=date(2001, 7, 15)))
    owner.put("/api/v1/sites/current", json=GARDEN)
    owner.post("/api/v1/beds", json={"name": "Big", "width": 2.4, "length": 3.6})
    two = owner.get("/api/v1/plan/year").json()
    owner.put("/api/v1/household/settings", json={"people": 4})
    four = owner.get("/api/v1/plan/year").json()
    assert two["people"] == 2 and four["people"] == 4
    for group in ("leafy", "fruiting", "root"):
        assert four["coverage"]["groups"][group]["target_kg"] == 2 * two["coverage"]["groups"][group]["target_kg"]
    assert 0 <= four["coverage"]["overall"] <= 1 and "skipped_no_yield" in four
```

The fixture catalog has one crop, so the draft itself may be short or empty; the test deliberately asserts only the report's shape and the target scaling, which do not depend on it.

- [ ] **Step 6: Run to verify it passes**

Run: `python -m pytest -q backend/tests && ruff check . && ruff format --check .`
Expected: all pass. If the new coverage test fails because the synthetic climate gives the fixture crop no usable window, still assert the keys and target scaling (they do not depend on wants); do not weaken it further.

- [ ] **Step 7: Commit**

```bash
git add backend
git commit -m "Year plan: size crops from head count, report coverage and the best change" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Coverage card on the Plan tab

**Files:**
- Modify: `frontend/src/api.ts:125,247` (types)
- Create: `frontend/src/components/CoverageCard.tsx`
- Modify: `frontend/src/components/YearPlan.tsx`
- Modify: `frontend/scripts/e2e.mjs` (~line 188)
- Modify: `frontend/scripts/screenshots.mjs` only if it already captures the Plant tab (check; if it does, nothing to add)

**Interfaces:**
- Consumes: `GET /plan/year` fields from Task 4; `GET/PUT /household/settings` (`people`, partial PUT).
- Produces: types `Coverage`, `FoodGroupCoverage`; `HouseholdSettings` gains `people: number`; `YearPlan` type gains `people: number; coverage?: Coverage; skipped_no_yield?: string[]`; `PlanItem` gains `food_group?: string; kg?: number`; `<CoverageCard coverage people canChange onPeople />`.

- [ ] **Step 1: Types and API**

In `frontend/src/api.ts`:

```ts
export type FoodGroupCoverage = { target_kg: number; supply_kg: number; covered: number; weeks_short: string[] }
export type Coverage = {
  overall: number
  groups: Record<string, FoodGroupCoverage>
  best_change: { kind: 'add_bed_area'; m2: number; gain: number } | null
}
export type YearPlan = { garden: boolean; beds: boolean; scheduled: number; people: number; items: PlanItem[]; coverage?: Coverage; skipped_no_yield?: string[] }
```

(replacing the existing `YearPlan` line), add `food_group?: string; kg?: number` to `PlanItem`, and change `HouseholdSettings` to `{ forecast: boolean; place_search: boolean; people: number }`. `saveHouseholdSettings` must accept a partial: change its signature to `(settings: Partial<HouseholdSettings>) => request<HouseholdSettings>('PUT', '/household/settings', settings)`. In `components/DataSources.tsx` the object cast `as HouseholdSettings` becomes `as Partial<HouseholdSettings>`. Run `npm run build` in `frontend/` and fix any other type errors it reports (e.g. `keyof HouseholdSettings` at `DataSource.switch` now also allows `'people'`; narrow it to `'forecast' | 'place_search'`).

- [ ] **Step 2: The card**

Create `frontend/src/components/CoverageCard.tsx` using the existing UI kit (`../components/ui`; read `ui/index.tsx` for the exact exports of `Button`, `IconButton`, `Section` and use the same patterns `YearPlan.tsx` uses). Behaviour, not markup, is the contract:

- Props: `{ coverage: Coverage; people: number; canChange: boolean; onPeople: (n: number) => void }`.
- Heading line: `t('Feeds {n} people', { n: people })` with minus and plus `IconButton`s (lucide `Minus`, `Plus`), labels `t('Fewer people')` and `t('More people')`, only rendered when `canChange`; minus disabled at 1, plus disabled at 20.
- Overall: `t('{pct}% of what your household eats', { pct: Math.round(coverage.overall * 100) })`.
- One row per food group in a fixed order (leafy, fruiting, root, brassica, legume, squash, allium, herb): label via `t()` (`'Leafy greens'`, `'Fruiting vegetables'`, `'Roots and tubers'`, `'Brassicas'`, `'Beans and peas'`, `'Squash family'`, `'Onion family'`, `'Herbs'`), a bar whose width is `covered * 100%`, and text `t('{pct}%', ...)`. The bar is decorative: the text carries the value. When `weeks_short.length > 0` add small muted text `t('{n} weeks short', { n })`.
- If `coverage.best_change`, a sentence: `t('Adding about {m2} m² of bed would raise this by {pct} points.', { m2, pct: Math.round(gain * 100) })`.
- Use design tokens already in `index.css` (the same classes `YearPlan.tsx` uses: `text-muted`, `divide-line`); no new colours.

- [ ] **Step 3: Wire it into YearPlan**

In `YearPlan.tsx`: keep `coverage` and `people` in local state; set both in `draft()` from the response (`setCoverage(r.coverage ?? null); setPeople(r.people)`); on mount also call `api.householdSettings()` to show the head count before the first draft. Render `<CoverageCard>` above the draft button when `coverage` exists; when it does not, still render a small people stepper (owner only). `canChange` is `useApp().user.role === 'owner'`. `onPeople(n)`: `api.saveHouseholdSettings({ people: n })` then `draft()`. Show `skipped_no_yield` (when non-empty) as muted text `t('Left out, no yield data yet: {crops}', { crops: list.join(', ') })`. On error use the existing `fail` handler.

Viewers and members never see the stepper buttons (only the number).

- [ ] **Step 4: e2e**

In `frontend/scripts/e2e.mjs`, directly after the existing line `await owner.getByRole('button', { name: /Use this plan/ }).or(owner.getByText(/Nothing fits right now/)).waitFor()` (~line 189), add:

```js
  await owner.getByText(/% of what your household eats/).waitFor()
  const feeds = () => owner.getByText(/^Feeds \d+ people$/).textContent()
  const before = await feeds()
  await owner.getByRole('button', { name: 'More people' }).click()
  await owner.waitForFunction((was) => [...document.querySelectorAll('*')].some((e) => /^Feeds \d+ people$/.test(e.textContent ?? '') && e.textContent !== was && !e.children.length), before)
  assert.notEqual(await feeds(), before, 'more people changes the head count')
  step('year plan: coverage card, head count changes')
```

If `Draft a year plan` yields "Nothing fits right now" in the stub environment (no coverage card is shown without a draft), keep the card visible in that case too: the card renders whenever the response carries `coverage`, which it does whenever a site and beds exist, whether or not any item fits.

- [ ] **Step 5: Verify**

Run (from `frontend/`): `npm run build` — expect no type errors. Then the repo's e2e procedure (see `docs/ACTIVE_CONTEXT.md` process note: start `backend/tests/e2e_server.py` against a fresh data dir, then `npm run e2e`). Then `npm run screenshots` and look at the Plant tab in light/dark and phone/desktop (standing requirement). Fix layout issues before committing.

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "Plan tab: coverage card with a head-count stepper" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Docs and release v0.41.0

**Files:**
- Modify: `CHANGELOG.md`, `README.md`, `docs/WIKI.md`, `docs/ACTIVE_CONTEXT.md`, `docs/PLAN.md`
- Run: `python scripts/bump.py 0.41.0`

- [ ] **Step 1: Bump**

Run: `python scripts/bump.py 0.41.0` (updates `backend/app/__init__.py`, `frontend/package.json`, `package-lock.json`, and cuts the changelog section).

- [ ] **Step 2: Changelog**

Under the new `## [0.41.0]` section write, in plain English for the owner: Added — "**The year plan feeds your household.** Set how many people you feed; the plan sizes each crop from a balanced basket (400 g of vegetables per person per day, split across leafy greens, fruiting vegetables, roots, brassicas, beans and peas, squash, onions and herbs), fills your beds as well as it can, and shows how much of the need they cover, the weeks that fall short, and what adding about 4 m² of bed would change." Changed — "Crop areas in a drafted plan now depend on yield, not a fixed six cells." Notes — "Yields per m² are labelled estimates for now (low confidence); they will be replaced with sourced figures." Also mention the settings fix: "Switching a data source on or off no longer touches other settings."

- [ ] **Step 3: README, WIKI, ACTIVE_CONTEXT, PLAN**

- README: update the "what works now" list for the head-count-driven plan and coverage; regenerate screenshots if the Plant tab is shown (`npm run screenshots` copies to `docs/images/`; check the script's output path).
- WIKI: add the needs model (basket, groups, how the draft is chosen, known limits from the spec).
- `docs/ACTIVE_CONTEXT.md`: append a `## v0.41.0` section: what shipped; known limits (estimated yields, even harvest spread, live crops hold cells only to cycle end); next steps (sourced yields, setup interview 8.1, Climate/Crops/More facelift, move planting + undo).
- `docs/PLAN.md`: 8.2 first bullet becomes `- [~] (v0.41.0: head count × a 400 g basket across 8 food groups; no diet or per-member model) Consumption targets…`; 8.4 "Quantities from targets ÷ expected yield" becomes `- [x] (v0.41.0)`; "Constraint fit… explain unmet demand; single most effective change" becomes `- [~] (v0.41.0: area and rotation only; coverage report and one best change)`.

- [ ] **Step 4: Final verification**

Run: `python -m pytest -q && ruff check . && ruff format --check . && python scripts/catalog_schema.py --check && python scripts/coverage.py --check && (cd frontend && npm run build)`
Expected: all green.

- [ ] **Step 5: Commit, push, PR**

```bash
git add -A
git commit -m "Release v0.41.0: the year plan feeds your household" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
git push -u origin claude/project-setup-f0c8f5
```

Then open a draft PR (mirror `.github/PULL_REQUEST_TEMPLATE.md` if present) and subscribe to its activity. End the PR body with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

---

## Self-review notes

- Spec coverage: input (Task 4/5), catalog fields (3), demand (1), planner (2), output/coverage/best change (1, 4), UI (5), error handling: no site/beds (4), missing yield listed (4), `people` validation (4), tests (1-5), release (6). The spec's `weeks_short: [..]` is a list of ISO week-start dates where supply is under half the target (Task 1).
- Spec gap closed: the spec's "household-level `needs_shares` override is deferred" and "perennials" are intentionally not built.
- Settings merge (Task 4) is not in the spec; it is required because `DataSources.tsx` would otherwise reset `people`. Called out in Review Focus 1.
- Performance: the drafter is lazy-greedy; a prototype with 96 wants/month × 12 months × 2 beds ran in about 0.02 s.
