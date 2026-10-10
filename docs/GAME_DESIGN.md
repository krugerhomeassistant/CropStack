# Garden game: design

Status: plan, written 2026-10-10 from the owner's idea. Nothing here is built yet unless a PLAN.md box (Phase 15) says so.
Working title: **Garden view** (the owner may rename it, see §14).

> A slow, calm game that is also your garden tracker. You lay out your real garden, dig the beds, sow what you really sowed, and the plants grow in real time with your real garden: same days, same weather, same frost. What you do in the game is what you did outside.

## 1. Why this exists

CropStack already knows a lot about the garden: the beds and their cells, every planting and its dates, the site's climate and live weather, growing degree-days, the water balance and the jobs due today. Today all of that is shown as forms, lists and a flat plan. The game shows the same data as a living place you want to open every day, and turns logging (the part people skip) into the fun part: watering a bed in the game *is* logging the watering.

What it adds that the app does not have:
- A daily reason to open the app that is not a to-do list.
- A visual estimate of where each plant is (sprout, leafy, flowering, fruiting, ripe) that the gardener can confirm or correct, which calibrates the crop engine (SPEC §6.3 "Calibration").
- A safe place to practise: a sandbox plot that replays real past years of the owner's own site at high speed.

## 2. Pillars

1. **One garden, two views.** The game is a view of CropStack data, never a copy. Beds, plantings, jobs and harvests are the same rows the app uses. There is no game state that can disagree with the real garden, and nothing is entered twice.
2. **Real time, real weather.** Plants grow at the pace of the real garden, driven by the same engines (GDD, water balance, forecast). The light is the real time of day at the site, the rain is today's rain. Nothing is sped up in the real garden.
3. **Honest.** Every growth state is an *estimate* and says so. The game never invents outcomes: a plant only dies when the gardener says the real one died; a pest only appears when a real Check job is open or a real finding was logged. Ambient life (birds, bees, wind) is decoration and is never presented as a measurement.
4. **Calm, never punishing.** No energy bars, timers, streaks, currencies, shops or nagging. Missing a week costs nothing in the game that it did not cost in the garden. A visit can be 30 seconds.
5. **Hands in the soil.** The verbs are real garden work (dig, amend, sow, plant out, water, mulch, weed, check, harvest, clear). Each one is a real record.
6. **Professional and accessible.** Same design system as the app, phone first, works one-handed, reduced-motion and colour-blind safe, and every cue in the game also exists in the normal app (Today, Garden).

## 3. Core loop

**Daily (30 s to 5 min):** open → the garden at the real time of day and weather → notice what changed (new sprouts, a thirsty bed, ripe fruit, a pest marker) → act (water, harvest, check) → each act is logged and the matching job is done → close.

**Seasonal:** plan and build (beds, paths) → prepare (dig, amend) → sow and plant out → tend (water, feed, check, weed) → harvest → clear and cover (cover crop or mulch) → winter: read the season's almanac and plan the next one in the practice plot.

**Long term:** rotation history shows on the soil itself; the almanac fills year by year; the crop engine learns the garden from confirmed stages.

## 4. Two places

| | **Your garden** (live) | **Practice plot** (sandbox) |
|---|---|---|
| What it is | The real garden, mirrored | A separate plot to experiment in |
| Time | Real time only; rewind to look at the past, peek ahead (ghosted, labelled estimate) | Fast: 1 day = 1–5 s, pause, step, scrub |
| Weather | Observed + today's forecast | A replayed real past year of the site's own record (an analog year): "typical", "cold spring", "hot summer" or a named year |
| Writes | Real records (plantings, journal, harvests, jobs) | Only to the practice plot; "Use this plan" turns it into *planned* plantings in the real garden after a diff and confirm |
| Look | Normal | Framed and labelled "Practice plot, not your garden" at all times |

The practice plot reuses the analog years the environment engine already builds (SPEC §4.2), so a simulated season is never made up: it is what a real year did at this site.

## 5. Verbs and what they record

Every verb opens a small sheet with sensible defaults (today, the whole bed, the usual amount), so most actions are one tap plus confirm. An undo toast stays for 10 s.

| Verb | Where | Records | Completes job |
|---|---|---|---|
| Build | empty ground | bed, path, ground type, structure, tree, fence (shared with the Garden plan, §7) | – |
| Dig / fork ("plough") | bed | journal `dig` | – |
| Amend | bed | journal `amend` (what, how much); later the inputs inventory (SPEC §10) | Feed |
| Sow / plant | cells | planting (existing API) | Plant |
| Plant out | planting | `set_out_date`, status `transplanted` | Plant (set out) |
| Water | bed or planting | journal `water` (litres, estimated from a can or hose time) → water balance `irrigation_logged` (SPEC §6.6) | Water |
| Mulch, weed, stake, prune, cover | bed or planting | journal entry of that kind | matching care job |
| Check | planting | Check job done; optional finding (organism, severity) | Check |
| Look closer | planting | stage confirmation ("it is flowering"), optional photo | – |
| Harvest | planting | harvest row (existing API) | Harvest |
| Clear | bed or planting | planting `finished` (or `failed` with a reason), cells freed | – |

## 6. Growth and state model

All rules live in the backend as **pure** functions (like `engine/phenology.py` and `engine/water.py`), so the app, the game and the practice plot share one source of truth and one set of tests. The client only renders and animates.

**Growth (new `engine/growth.py`)** per planting and day:
- `progress` = GDD accumulated since sowing (or set-out) ÷ the crop's GDD target, using observed temperatures for past days (archive, then the forecast's `past_days` for the last weeks the archive lacks) and the forecast for today.
- `stage` from progress, mapped to the SPEC §6.3 stages and a BBCH principal stage (0 germination … 8 ripening, 9 senescence). Crops without stage GDD targets use days-to-maturity, linearly, and are flagged `rough`.
- `size` (0–1) from progress through a logistic curve, scaled to the crop's catalogued height and spread.
- `flags`: `thirsty` (bed water deficit past readily available water), `frost_risk` / `frost_hit` (forecast or observed minimum below the crop's lethal minimum; *hit* only asks "check for frost damage", it never kills), `heat_stress`, `ripe` (harvest job open), `pest` (Check job open or finding logged), `bolting_risk` later.
- `confidence`: high when a confirmed stage is recent, low when only days-to-maturity is known.
- Confirmed stages from "Look closer" override the estimate and feed the household calibration of GDD targets (SPEC §6.3).

**Bed state** is derived, not stored: `unworked → dug → amended → planted → growing → cleared → covered`, from the journal and plantings. Rotation history (families per bed per season) tints the soil edge so a gardener sees "brassicas were here last year".

**Sun and sky (new `engine/sun.py`)**: solar position from site latitude, longitude and the clock (NOAA algorithm, no dependency) drives light colour, shadow direction and length, sunrise and sunset, and moon phase. The same function later feeds the sun and shade model of the layout editor (SPEC §7.1).

**Weather now**: cloud cover, rain, wind speed and direction, temperature from the hourly forecast already fetched every 3 h. Nothing new is called.

## 7. Map builder (shared with the Garden plan)

The game does not get its own map. Building in the game and drawing in the Garden plan edit the same geometry, so the open layout-editor items in PLAN 8.3 (paths, structures, trees, ground, rotate, undo/redo) are built once and appear in both.

- Existing: `bed` (rectangles, rows, pots, cells, layouts).
- New `garden_feature` table: `kind` (path, ground, fence, wall, building, greenhouse, tunnel, tank, compost, tree, shrub, decor), geometry in metres (point, polyline or polygon), `props` JSON (height, canopy radius, material, label). Heights are what the shade model needs later.
- Ground types (lawn, bare soil, gravel, paving, bark, mulch) paint the space between beds.
- Building mode: pick a piece, drag to draw, snap to grid and edges, rotate, duplicate, undo/redo, templates ("four 1.2 × 2.4 m raised beds").

## 8. Look and feel

- **View**: top-down at a slight angle (high oblique) so plant height reads, with three zoom levels: whole garden, bed, plant. Pinch, drag, double-tap to focus a bed.
- **Art**: drawn in code, no bitmap assets, soft flat vector shapes in the app's palette (tokens from DESIGN.md). Plants are generated from a small set of growth habits (rosette, upright, bush, vine or climber, root with foliage, allium, grass-like, tree or shrub) with parameters from the catalog (height, spread) and presentational data (leaf, flower and fruit colour and shape) kept in `frontend/src/game/art/crops.json`, which is MIT code-side data, not catalog facts, so it needs no provenance.
- **Living garden**: light follows the real sun, shadows point away from it; clouds pass with real cover and wind; rain falls when it rains; frost rimes the ground on frosty mornings; plants sway with real wind; bees visit flowering plants on warm days; birds land on paths. Pests appear only under the honesty rule (§2.3).
- **Seasons**: ground and light shift through the year by date and hemisphere; bare winter beds look cared-for when covered or mulched.
- **Cards**: tap anything for a card in the app's style: crop, variety, sown on, estimated stage (with "estimate" badge and confidence), next job, last watered, last harvest, photo. "Open in app" deep-links to the planting.
- **Sound**: optional and off by default (rain, birds), never notifications.
- **Accessibility**: reduced motion stops particles and sway; every cue uses shape and label, not only colour; beds are reachable by keyboard; a screen-reader summary per bed; a "List" toggle shows the same cues as text.

## 9. Ideas pool (not committed, pick from after the core works)

- **Season timelapse**: replay this season from the journal in 20 s; save as a short clip or image to share.
- **Almanac**: a book per season: what grew, first-harvest dates, kg per crop, best and worst varieties, frosts, rainfall; year-on-year comparison.
- **Milestones** from real outcomes only (first harvest, 10 kg of tomatoes, a three-year rotation kept, no bare soil all winter); each can unlock a decor piece (bird bath, scarecrow, bench). No points.
- **Household presence**: footprints and a line such as "Anna watered Bed 2 at 07:10"; each member's actions in their own colour.
- **Rain gauge** in the garden showing the real millimetres of the last 24 h and 7 days.
- **Compost heap** that fills as beds are cleared and empties when compost is spread.
- **Seed tin** from the seed vault (Phase 10): sowing takes from it and shows what is running low.
- **Home Assistant**: soil-moisture probes drawn in their real beds with live readings; the sprinkler animates when a valve opens.
- **Animals** (Phase 9): hens in their run, a hive with bees flying from it, from the animal records.
- **Frost cloth and shade cloth** drawn over beds when a Protect job is marked done.
- **Peek ahead**: ghosted plants a few weeks on, from the expected path, clearly marked estimate.
- **Visit a garden**: a read-only share link to show a friend the garden (privacy review first).
- **Weekly postcard**: an image of the garden that week for the household.

## 10. Architecture

```
React app (existing PWA)
  └─ /garden/view  lazy-loaded route chunk
       ├─ game/state.ts     fetch /api/v1/game/state, poll every 10 min, queue actions offline
       ├─ game/renderer.ts  Canvas 2D (decided in G0), camera, layers, hit testing
       ├─ game/art/*        plant habits, ground, sky, particles (pure draw functions)
       └─ game/ui/*         tool belt, sheets and cards from the UI kit
FastAPI (existing)
  ├─ GET  /api/v1/game/state?at=      site, sun, weather now, beds, features, plantings + growth, cues, recent journal
  ├─ POST /api/v1/journal             dig, amend, water, mulch, weed, stake, prune, cover, finding, stage, photo
  ├─ CRUD /api/v1/features            paths, ground, structures, trees, decor (shared with the plan)
  ├─ POST /api/v1/practice/simulate   layout + plantings + analog year → daily states (practice plot)
  └─ engine/growth.py, engine/sun.py  pure, unit-tested
SQLite: journal_entry, garden_feature, practice_plot (new); bed, planting, task, harvest (existing)
```

Rules:
- The backend owns all rules; the client never decides a growth stage or a flag.
- `game/state` is one call per open and per poll, cached per household for 10 min and invalidated by any write.
- Writes go through the normal APIs, so jobs regenerate exactly as they do from the app.
- No new runtime dependency in the first version; a WebGL renderer is only added if the G0 spike shows Canvas 2D cannot hold the budget.
- Performance budget: 60 fps on an iPhone 12-class phone with 300 plants and rain; at most 30 fps when nothing is interacting; rendering stops when the tab is hidden; game chunk ≤ 150 KB gzipped; `game/state` ≤ 300 ms on a Raspberry Pi 4 class server.

Rendering options compared for the G0 spike:

| Option | For | Against |
|---|---|---|
| **Canvas 2D** (default) | No dependency, same style as the dependency-free charts, simple hit testing | Must batch carefully; no shaders |
| PixiJS (WebGL/WebGPU, MIT) | Fast sprites and particles, filters | Adds a large dependency and its own scene graph |
| SVG (like the plan) | Already used, accessible DOM | Slows with hundreds of animated nodes |
| Game engine web export | Full engine | Big download, second toolchain, separate auth and UI kit |

## 11. Data model additions

| Table | Fields |
|---|---|
| `journal_entry` (the SPEC §10 journal) | id, household_id, bed_id?, planting_id?, kind (dig, amend, water, mulch, weed, stake, prune, cover, finding, stage, photo, note), on (date), at (datetime), value JSON (litres, product and amount, organism and severity, stage, photo path), created_by |
| `garden_feature` | id, household_id, kind, geometry JSON (metres), props JSON, layout, created_at |
| `practice_plot` | id, household_id, name, layout JSON, plantings JSON, analog_year, created_at, updated_at |

Photos are stored under `<data>/photos/` with the same backup rules as the database (PLAN 14).

## 12. Risks and guards

| Risk | Guard |
|---|---|
| The game becomes a second app with its own truth | Pillar 1; no game-only state except decor; writes through existing APIs; one shared map |
| Growth looks wrong because catalog data is thin | `rough` flag and confidence on every estimate; "Look closer" corrections; days-to-maturity fallback |
| Pretty but slow on phones, drains battery | G0 budget gate; 30 fps idle cap; stop when hidden; reduced-motion mode |
| Scope creep in art | Eight growth habits cover most crops; everything else is an ideas-pool item |
| Practice confused with reality | Permanent frame and label; separate table; explicit diff before anything reaches the real garden |
| Nagging mechanics creep in | Pillar 4 is a review checklist item for every game PR |

## 13. Acceptance (whole feature)

- The owner opens Garden view on the iPhone and recognises the real garden: beds where they are, the crops in their cells, light and weather matching outside.
- A full day of real jobs can be done from the game alone, and Today shows them done.
- A stage confirmed in the game changes that planting's next estimates.
- A practice season of a full year plays in under 10 minutes and can be applied as planned plantings.
- Every cue in the game is also visible in the normal app; the axe check and a keyboard pass are clean.

## 14. Open questions for the owner (defaults used until answered)

1. Name: "Garden view" (default) or something else?
2. Art style: soft flat vector drawn in code (default) or pixel art?
3. Where it lives: a "View" tab inside Garden (default) or its own item in the main navigation?
4. Decor unlocks from real milestones: yes (default) or no rewards at all?
5. Sound: off by default (default) or on?
