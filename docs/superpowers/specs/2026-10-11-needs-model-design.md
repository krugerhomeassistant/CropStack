# Needs model and demand-driven year plan (PLAN 8.2, part of 8.4)

Status: draft for owner review · 2026-10-11

## Intent (agreed with owner)

The owner enters **how many people** and **lays out the beds**. The app then plans and recommends everything else: which crops, how many cells, when to sow and succession-sow, which bed, and what the garden will yield.

- Space is almost always smaller than household need, so the planner works **backwards from the space**: it fills the beds as well as it can, then reports coverage and the one change that helps most.
- When space cannot cover everything, favour a **balanced, year-round vegetable supply** (variety per person per week, weighted to crops with the most food per m²), not calories first.
- Everything beyond headcount and beds defaults sensibly and is editable later but never required.

Out of scope: animals, preservation, calorie staples, budget, labour limits, sun model, the setup interview (8.1), per-crop targets, a solver library.

## Existing code this extends

- `backend/app/engine/yearplan.py`: pure greedy `draft(beds, taken, wants, today)`. `BLOCK = 6` is the placeholder this work removes.
- `backend/app/routers/plan.py` `year_plan()`: builds `Want`s from catalog windows and calls `draft`.
- `Household.settings` (JSON, validated by `HouseholdSettings` in `routers/household.py`): holds `people`. No migration needed.
- Catalog `params` with `value/unit/evidence/confidence/sources` (as `sow_depth`): holds `yield_per_m2`.

## Design

### 1. Household input
`HouseholdSettings.people: int = 2` (1 to 20). Exposed through the existing household settings API. UI: a stepper on the Plan tab empty state and in Settings. Changing it re-drafts on next view (the draft is computed on GET; nothing is stored until accepted).

### 2. Catalog data
- `params.yield_per_m2`: kg of harvested produce per m² per crop cycle, for all 60 crops. Sourced from extension-service tables where found; otherwise `estimate: true`, `confidence: low`, the same convention as `sow_depth`. Per cycle, so multi-harvest crops (tomato, beans) use the full-season figure.
- `food_group`: one of `leafy, brassica, fruiting, root, allium, legume, squash, herb`. A plain classification, not a measured value, so a top-level string on the crop with no sources. The catalog schema and validator must accept it (check in the plan; extend the schema if it rejects unknown keys).
- Coverage report (`docs/COVERAGE.md` tooling) gets a "missing yield / food_group" row so gaps are visible.

### 3. Demand (`engine/needs.py`, pure)
```
BASKET_KG_PER_PERSON_DAY = 0.4   # WHO: at least 400 g fruit and vegetables a day
GROUP_SHARE = {leafy .20, brassica .12, fruiting .20, root .15, allium .08,
               legume .10, squash .10, herb .05}   # sums to 1.0
weekly_target(people)[group] = people * 7 * BASKET * GROUP_SHARE[group]
```
Shares are our own reasonable split, documented as a modelling choice with the WHO figure cited for the total. Not shown as nutritional advice. A household-level override (`needs_shares`) is deferred until someone asks.

### 4. Planner (`engine/yearplan.py`)
`Want` gains `kg_per_cell = yield_per_m2 * cell_area_m2` per bed (computed at placement, since cell size varies per bed) and `food_group`.

Loop, replacing the current sorted single pass:
1. State: per group, weekly supply array (52 weeks from today), starting from existing non-replaceable plantings' expected yield.
2. Candidate = (want, bed, block of free cells). Block size is chosen as the number of cells that closes the remaining shortfall for the want's harvest weeks, capped by free contiguous cells and by a per-crop cap (default 12 cells) so one crop never swallows a bed.
3. Gain = sum over harvest weeks of `min(added_kg, shortfall)` for its group, divided by the cells used, so small beds are used efficiently. Highest gain per cell wins; ties go to higher `success`, then name (deterministic).
4. Place it, update supply, repeat until no candidate has positive gain or no free cells remain.
5. Existing rules stay: rotation (cells that held the same family come last), no overlap, a crop is not repeated within a month.

Harvest is spread evenly across `harvest_from..harvest_to` of the want. This is a stated simplification; per-week yield curves are a later refinement.

### 5. Output
`GET /plan/year` returns the existing fields plus:
```
"people": 4,
"coverage": {
  "overall": 0.62,                       # kg supplied / kg needed over the year, per group, each capped at 1, averaged by share
  "groups": {"leafy": {"target_kg": .., "supply_kg": .., "weeks_short": [..]}, ...},
  "best_change": {"kind": "add_bed_area", "m2": 4, "gain": 0.18} | null
}
```
`best_change` is computed by re-running the draft with one extra virtual bed of 4 m² (one candidate change only; more kinds later) and reporting the coverage delta. If coverage is already at or above 0.95 it is null.

### 6. UI (Plan tab)
A coverage card above the draft: people stepper, overall percentage, a bar per food group (target vs supply), the weeks with gaps, and the `best_change` sentence. Existing review / leave-out / accept flow is unchanged. Copy follows the rules in `docs/DESIGN.md`. Light/dark and phone/desktop screenshots checked before release.

## Error handling
- No site or no beds: unchanged early return (`items: []`), coverage omitted.
- Crop missing `yield_per_m2` or `food_group`: skipped by the demand-driven loop and listed in `skipped_no_yield` so it is visible, never silently dropped. (All 60 are filled in this slice, so this only guards future additions.)
- Untrusted input: `people` validated 1 to 20 by Pydantic.

## Testing
- `tests/test_needs.py` (pure): `weekly_target` scales linearly with people; shares sum to 1; supply and shortfall maths.
- `tests/test_yearplan.py` additions: doubling people increases planted cells until beds are full; a full space stops adding; a group with zero shortfall gets no more; result is deterministic; rotation still honoured.
- `tests/test_plan.py` API: `coverage` present, `people` round-trips through settings, `best_change` is null at full coverage.
- Catalog test: every crop has `food_group` in the allowed set and a `yield_per_m2` with unit and evidence.
- Playwright e2e: change people, coverage card updates.

## Release
Minor version bump (v0.41.0), CHANGELOG, README and WIKI refreshed, ACTIVE_CONTEXT updated, PLAN 8.2 and 8.4 checkboxes annotated.

## Known limits (stated, not hidden)
- Yield per m² is a single typical figure per crop, not site-, variety- or skill-adjusted.
- Even harvest spread within a harvest window.
- Basket and group shares are a defensible default, not personalised nutrition.
- Live crops hold cells only to cycle end (open item from v0.40.0) remains.
