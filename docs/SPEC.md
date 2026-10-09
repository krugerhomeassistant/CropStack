# CropStack — Product & Technical Specification

Status: **v1 draft, 2026-10-09** · Owner: krugerhomeassistant · Applies from v0.5.0 onward.
This document is the source of truth for *what* CropStack does and *how* its engines decide. `PLAN.md` breaks it into tasks; `WIKI.md` describes what is already built; `ARCHITECTURE.md` describes the code as it is.

Keywords **MUST / SHOULD / MAY** follow RFC 2119.

---

## 0. Contents

1. Vision & scope
2. Core principles (the "no presets" rule)
3. Users, households, guided setup & goals
4. Environment model (climate, weather, soil, sensors, observations)
5. Requirement profiles (the shared language of crops and animals)
6. Crops: catalog, varieties, phenology, scheduling
7. Garden: layout editor, beds, plantings, rotation, companions
8. Animals: catalog, breeds, groups, lifecycle, care, environment, production
9. Planning: needs-based plan generator, calendar & task engine
10. Records: harvests, pantry & preservation, seed vault, inputs, health
11. App experience: Today, scouting guide, climate explorer, navigation
12. Integrations: Home Assistant, iCalendar, notifications, AI co-pilot
13. Data model
14. API
15. Non-functional requirements
16. Data sources, licences & attribution
17. Testing strategy & acceptance criteria
18. Superseded behaviour (v0.3/v0.4 heuristics to remove)
19. Open questions

---

## 1. Vision & scope

CropStack is a self-hosted homestead manager that tells you **what to do, when, and why** for every crop and animal you keep, anywhere on Earth, and keeps re-deciding as conditions change.

In scope:
- Food crops: vegetables, herbs, fruit (annual, biennial, perennial, trees, vines, berries), grains, cover crops.
- Animals: poultry (chickens, ducks, geese, turkeys, quail), small ruminants (goats, sheep), cattle, pigs, rabbits, honeybees; extensible to any species.
- Planning, calendars, tasks, records, inventory, alerts, integrations.

Out of scope (for now): commercial farm accounting, payroll, marketplace, regulatory reporting, ornamentals-only gardening.

## 2. Core principles

**P1 — No presets, no modes, no toggles for climate.** The app MUST NOT contain climate types, regional presets, location rules, "frost mode", "hot mode" or global hazard thresholds that switch behaviour. There is exactly one code path for every location.

**P2 — Requirements × environment.** Every recommendation, date, alert and warning MUST be the result of comparing a *subject's requirement profile* (a crop variety, an animal breed, a task) with the *environment's data* (distributions, observations, forecasts). If something is irrelevant for a place, it scores ~0 and disappears; if it becomes relevant (the climate shifts, a cold year arrives), it appears on its own.

**P3 — Probabilistic, not binary.** The environment is represented as probability distributions per day of year, not single "dates". Users choose a **risk tolerance** (one global setting, overridable per crop/animal/task), never a climate category.

**P4 — Continuously re-evaluated.** Climatology refreshes itself (rolling window, recency-weighted, trend-aware), recent weather and forecasts override climatology for the near term, and local sensors and user observations calibrate the grid data. Plans recompute automatically (nightly and on new data) and explain what moved and why.

**P5 — Fully customisable.** Every catalog value (crop, variety, breed, care template, threshold) MUST be overridable by the user, and users MUST be able to create entirely custom crops, varieties, species, breeds and task templates. Catalog defaults are a starting point with sources, not rules.

**P6 — Explainable.** Every task, date and alert MUST carry a machine-readable *reason trace* (inputs, rule, numbers) and a human sentence ("Sow 12 Mar–2 Apr: soil reaches 10 °C on 80% of years by 12 Mar; harvest before days ≥ 30 °C become likely in Nov").

**P7 — Local-first and private.** Works offline in the field (PWA); data in one SQLite file; outbound calls limited to declared data services, each listed in the UI with what is sent.

**P9 — Action first.** The default experience is "what should I do today, and how". Analysis supports decisions; it is never the front page unless the user chooses it.

**P8 — Honest uncertainty.** Show confidence; never present grid estimates as facts. Prefer "likely / unlikely" with numbers over absolute claims.

## 3. Users, households, guided setup & goals

- **Household**: the tenant. Owns sites, crops, animals, records. One installation MAY host several households.
- **Roles** per household: `owner` (everything), `member` (plan, log, complete tasks), `viewer` (read-only, e.g. a partner or house-sitter). Task assignment to members.
- **Accounts**: username + password (argon2id), optional passkeys (WebAuthn) later; registration modes `auto|true|false` (existing).
- **Preferences** per user: language, units (metric/imperial), week start, notification channels, quiet hours. Per household: default risk tolerance, timezone (auto from site).

### 3.1 Guided setup interview
A conversational, skippable, resumable wizard on first run (and re-runnable any time from Settings → "Re-plan"). Every answer is stored as editable household **profile** data; nothing is a mode switch. Questions adapt to earlier answers (e.g. skip pasture questions if no grazing animals are wanted). Each question explains why it is asked and what it changes.

| Topic | Questions (examples) | Feeds |
|---|---|---|
| Location | Find your place (search / map pin / GPS); is the garden somewhere else than home? | sites, environment |
| Space | Total growing area (m² or draw it), existing beds/containers/structures, balcony/rooftop/indoor, slope, trees and buildings that cast shade | layout, capacity |
| Sun | Sun hours per area (simple choice or guided sun-mapping: morning/afternoon/all day), or computed from drawn obstacles and sun path | crop placement |
| Water | Source(s) (mains, borehole, rainwater tanks with capacity, greywater), restrictions (litres/day, allowed days/times), irrigation available (drip, sprinkler, hand) | water budget, crop choice |
| Soil | Type by feel test (guided), drainage (puddle test), known pH/test results, raised beds or in-ground | bed soil, amendments |
| People & diet | Household size (adults/children), what you eat and how much (vegetable/fruit preferences, dislikes, staples), dietary needs (vegetarian, allergies), how much you want to grow yourself (a few herbs → % of produce → near self-sufficiency) | needs model |
| Animals | Interest in eggs, milk, meat, honey, fibre, manure; space for coops/pens/pasture; local rules you know of (e.g. no roosters), predators present | animal plan |
| Time & skill | Hours per week in season, available days, experience level (first garden → experienced), physical constraints (accessible beds) | plan size, task load |
| Budget & tools | Start-up budget, recurring budget, tools/structures owned, willingness to build (beds, tunnel, coop) | plan options |
| Preservation & storage | Freezer space, canning/dehydrating gear, cool storage | harvest timing, crop mix |
| Preferences | Organic only, perennials vs annuals, heirloom/open-pollinated seeds, seed saving interest | catalog filters |
| Risk | How much risk you accept (plain-language slider: "play it safe" ↔ "push the season") | risk_tolerance |

Output of the interview: a **household profile** (persisted, versioned), a first **site layout** (if drawn), and a **proposed plan** (9.1) the user reviews before anything is scheduled.

### 3.2 Needs model
- **Consumption targets** per crop group derived from household size × diet answers × self-sufficiency target, using per-person reference intakes (e.g. WHO/FAO fruit & vegetable guidance) and the user's own preference weights; editable as a table ("tomatoes: 1.2 kg/week in season").
- **Animal product targets** (eggs/week, milk/day, meat/year, honey/year) from answers, editable.
- **Constraints**: area by sun class, water budget by month, labour hours by week, budget, structures.

## 4. Environment model

### 4.1 Sites
A household has 1..n **sites** (home garden, allotment, paddock). Each site: name, point location (lat/lon), optional boundary polygon, elevation (auto, overridable), aspect/slope (optional), timezone (auto). All environment data is per site.

### 4.2 Climatology (long-term expectation)
Source: Open-Meteo archive (`era5_seamless`), daily, **rolling last 30 complete years**.

Stored per site as the **raw daily record** (`climatearchive`): `tmin`, `tmax`, `soil_t` (0–7 cm), `precip`, `et0` (FAO reference evapotranspiration), `rh` (mean relative humidity), `wind` (max). `daylight` is computed astronomically.

**Analog years** (implemented v0.6.0, `backend/app/environment.py`): each historical year is treated as one plausible future and every question is answered by running it through each year and taking the weighted share of years in which it happens. This keeps day-to-day sequences intact, so window questions are exact rather than combined from daily averages:
- `P(any day with var op x within [d, d+n))` (e.g. a night ≤ a crop's `lethal_min` during its exposed stage), crossing 31 December into the following year
- per-day curves `P(var op x on DOY d)` and quantile bands (q10/q50/q90), pooled over a 15-day window
- days needed to reach a GDD target from a start date (distribution; years that never reach it show as "doesn't mature")
- GDD totals and water deficit (`ET0 × Kc − rain`) over any window
- Chill accumulation is added with the perennial phenology (PLAN 6.1).

**Recency weighting & trend**: each year has weight `w = 0.5^((Y_last − y)/H)` with half-life `H` (default 10 years). For temperature variables a linear trend of annual means is fitted; if significant (two-sided 5 %), every past year is shifted to the current level (`value + slope × (as_of − year)`). The UI shows the trend per decade when significant, nothing otherwise.

**Refresh**: on access, when the site moved, a newer complete year exists (each January), or the stored format changed; if the refresh fails and the site hasn't moved, the existing record keeps answering.

**Projection (optional, off by default)**: Open-Meteo Climate API (CMIP6 HighResMIP, bias-corrected to ERA5-Land) can be enabled per site to view 2030/2040 shifts for perennial planting decisions (trees live 30+ years).

### 4.3 Recent observations (this season so far)
Last 92 days of actual daily weather (Forecast API `past_days`), refreshed daily. Used to compute **season anomalies** (GDD ahead/behind normal, rainfall deficit/surplus) that shift predicted crop development and pasture growth.

### 4.4 Forecasts
- **Short-range**: Open-Meteo forecast, 16 days, hourly where needed (tmin, tmax, precip, precip probability, ET0, RH, wind, soil temperature/moisture). Refreshed every 3 hours (configurable; respects quota).
- **Seasonal (optional)**: ECMWF seasonal via Open-Meteo, up to 7 months, ensemble mean + spread; used only to tilt probabilities (e.g. "warmer than normal spring likely") with explicit labelling.
- **Blending rule**: for any future date *d*: days 0–16 use forecast (with forecast uncertainty widening by lead time), days 17–46 blend forecast/seasonal anomaly with climatology, beyond that climatology (+ seasonal tilt if enabled).

### 4.5 Soil
- Defaults from ISRIC SoilGrids (pH, texture, organic carbon) at the site location — optional fetch, CC BY 4.0.
- Per bed overrides from user soil tests (pH, EC, N-P-K, organic matter, texture, drainage) with date; history kept.

### 4.6 Local sensors & observations (calibration)
- Sensors (Home Assistant / MQTT / manual entry): air temp, RH, soil moisture, soil temp, rain gauge, light, greenhouse/coop temperature. Each sensor is attached to a site or a bed/structure.
- **Bias learning**: when ≥ 14 days of overlapping data exist, fit per-variable offset/scale between sensor and grid (e.g. frost pocket runs 2.1 °C colder at night). Apply to forecasts and climatology for that location; show the learned offset and allow reset.
- **User observations**: "frost on the lawn this morning", "first ripe tomato", "hens stopped laying" — timestamped events that feed calibration (phenology model residuals, local frost frequency) and records.

### 4.7 Microclimates
Structures (greenhouse, polytunnel, shade house, cold frame, coop, barn) modify the environment for things inside them via a **modifier profile**: additive °C at night/day, rain exclusion, wind reduction, light reduction %. Defaults per structure type, learned from sensors when available.

## 5. Requirement profiles

A single schema describes what any subject (crop variety, animal breed, task) needs. All numeric values are optional; missing values mean "no constraint". Each value carries `source` and may be overridden by the user.

```yaml
temperature:
  lethal_min: -2.0        # °C, damage/death below (frost tolerance)
  stress_min: 7.0         # growth stops / chilling injury
  optimal: [18, 27]       # range for best growth
  stress_max: 32.0        # heat stress (bolting, flower drop, reduced lay)
  lethal_max: 40.0
  base: 10.0              # GDD base temperature
  upper_cutoff: 30.0      # GDD upper cutoff
soil_temperature:
  germination_min: 10
  germination_optimal: [20, 30]
  germination_max: 35
photoperiod:
  response: short_day | long_day | neutral
  critical_hours: 12.5    # e.g. bolting trigger for long-day crops, laying decline for hens
vernalization:
  required: false
  hours_below: 7.0        # °C
  hours_needed: 0
chill:                     # perennials
  model: dynamic | utah | hours_below_7
  required: 400
water:
  kc: {initial: 0.6, mid: 1.15, late: 0.8}   # FAO-56 crop coefficients
  drought_tolerance: low | medium | high
  waterlogging_tolerance: low | medium | high
humidity:
  disease_risk_rh: 90      # sustained RH above this raises fungal pressure
  thi_alert: 72            # animals: temperature-humidity index thresholds
  thi_danger: 79
wind:
  max_sustained: 50        # km/h
light:
  min_sun_hours: 6
soil:
  ph: [6.0, 7.0]
  drainage: well | moderate | tolerant
```

**Rule**: the engines compute, for any date and location, the probability that each constraint is violated; nothing else decides relevance.

## 6. Crops

### 6.1 Catalog
- **Crop** (species-level): names (scientific, common in each language), family (rotation group), life cycle (annual/biennial/perennial), edible parts, requirement profile, phenology model (6.3), propagation methods (direct sow, transplant, cutting, division, graft, tuber), spacing (in-row, between-row, square-foot count), depth, days to germination (as function of soil temperature), companion/antagonist links (with evidence level), common pests/diseases (with degree-day or weather risk models where known), nutrient demand class, yield per m² range, storage life, preservation methods.
- **Variety** (cultivar): inherits from crop, overrides any field (e.g. "bolt-resistant", days to maturity, heat tolerance, chill requirement for fruit trees, determinate/indeterminate, seed source).
- **Initial content**: ≥ 60 vegetables & herbs, ≥ 20 fruit species, ≥ 5 cover crops, each with ≥ 2 varieties, every value sourced and evidence-labelled per §16.1. Stored in repo as `catalog/crops/<slug>.yaml` (not `data/`, which is the runtime volume) validated by JSON Schema; loaded into DB on start (catalog version tracked; user overrides survive updates).
- **Custom**: users create crops/varieties from scratch or by cloning; per-field override with "reset to default".
- **Seed content**: names and multilingual labels from Wikidata (CC0) and World Flora Online (CC0); climate envelopes from FAO ECOCROP (CC BY 4.0); FAO-56 Kc values as cited facts; crop slugs and sowing basics from the CC0 OpenFarm rescue set (340 records, `evidence: grower-reported` until checked). Details: [`research/catalog-data-sources.md`](research/catalog-data-sources.md).
- **Not bundled**: Permapeople (CC BY-SA 2.0, no free commercial API), PFAF (non-commercial), Trefle per-record third-party licences; link out only.

### 6.2 Plantings
A **planting** = variety × location (bed/area/container/structure) × method × start date × quantity, with status (planned → sown → germinated → transplanted → flowering → harvesting → finished/failed), actual dates, notes, photos. Successions are linked plantings.

### 6.3 Phenology model
Development stages: `sow → emergence → transplant-ready → transplant → vegetative → flowering → fruit set → harvest start → harvest end` (stages not applicable to a crop are skipped).
- Emergence time from soil temperature (thermal time above germination base; days-to-germination curve).
- Stage progression by **growing degree days** with base and upper cutoff from the profile (catalog provides stage GDD targets; when only "days to maturity" is known, GDD targets are derived from the climate at the reference location given in the source, else from a standard 20 °C mean).
- Photoperiod & vernalization triggers (bolting, bulbing, flowering) from the profile.
- Perennials: dormancy, chill accumulation, budbreak (GDD after chill satisfied), bloom, harvest; frost risk at bloom.
- **Calibration**: actual stage dates logged by users adjust variety GDD targets for that household (Bayesian update with prior from catalog).

### 6.4 Scheduling (window finding)
For each variety the engine evaluates every candidate start date in the next 18 months (daily) and method (direct sow / transplant):
1. Simulate stage dates using blended environment (4.4) — expected and 10th/90th percentile paths.
2. Compute **success probability** = P(no lethal event during exposed stages) × P(germination conditions met) × P(no stress-triggered failure: bolting, flower drop, sunscald) — using DOY distributions; expose each factor.
3. Compute **quality score** = fraction of growing days within optimal range, water balance deficit (mm irrigation needed), disease pressure days.
4. A date is *viable* if success ≥ the user's risk tolerance (default 80%). Consecutive viable days form **windows**; the best sub-window is highlighted. Multiple windows per year are normal (e.g. spring and autumn crops; all-year in mild climates).
5. **Successions**: for continuous harvest, schedule repeated sowings so harvest windows tile the season (interval derived from the harvest window length, not a fixed number of days).
6. **Indoor start**: if the outdoor window is short, compute indoor sow date = transplant date − transplant-ready age; propose hardening off over 7–14 days with daily exposure steps checked against forecast.
7. **Protected growing**: re-run with structure modifiers to show what a greenhouse/tunnel/shade cloth would unlock.
Output: windows with reasons, plus a per-crop "can I grow this here?" verdict (and what blocks it).

### 6.5 Crop care tasks
Generated from stage dates and conditions, all explainable: thin, pot up, harden off, transplant, stake/trellis, mulch, side-dress (by nutrient demand and stage), prune/pinch, pollinate (indoor), scout pests (when pest degree-day or weather-risk model says risk window opens), protect (forecast lethal_min breach → cover; forecast stress_max breach → shade/water), water (6.6), harvest (window + daily ripeness reminders), succession sow, clear & cover crop, rotation follow-up. Perennials: winter prune, chill check, bloom protection, thinning, harvest, post-harvest prune.

### 6.5.1 Feeding (nutrients)
- Each crop has a nutrient demand profile per stage (N, P, K, Ca, Mg, micronutrients as low/medium/high + timing, e.g. "side-dress N at first fruit set"), sourced and overridable.
- Bed soil tests (when present) and logged amendments adjust need; otherwise defaults from crop demand and soil type.
- Feed tasks state **what, how much, where, how**: product from the household's inputs inventory (compost, manure, worm tea, organic or mineral fertiliser with its N-P-K), dose per plant or per m² converted from the product's analysis, application method (side-dress, foliar, drench, top-dress), and cautions (don't feed nitrogen to fruiting tomatoes late; wash leafy greens). If the household has no suitable input, suggest the simplest one to get.
- Deficiency symptoms link to the scouting guide (11.3).

### 6.6 Water
Per bed daily soil-water balance (FAO-56 simplified): `deficit_t = deficit_{t-1} + ET0 × Kc(stage) × area_factor − effective_rain − irrigation_logged`, bounded by soil water-holding capacity (from texture). Irrigation task when deficit exceeds the readily available water for the crop's root depth; sensor soil moisture overrides the model when present. Outputs litres per bed. Home Assistant can execute (12.1).

## 7. Garden

### 7.1 Layout editor
- **Canvas** per site in real-world units: draw the property boundary, beds (rectangle, polygon, circle, keyhole), containers (by size), rows, structures (greenhouse, tunnel, shade house, cold frame, coop, run, barn, hive stand, water tanks, compost), paths, fences, trees (with canopy radius and height), buildings/walls (with height). Snap grid, rulers, dimension labels, rotate, duplicate, group, layers (infrastructure / beds / plantings / animals / irrigation), undo/redo, zoom/pan, touch gestures; mobile-first with a desktop power mode.
- **Start options**: draw from scratch, start from a template shape list (e.g. "four 1.2 × 2.4 m raised beds"), or trace over an optional map/satellite background (user-supplied image or OSM tiles, attribution shown).
- **Sun & shade model**: from site latitude, sun path (computed per day) and drawn obstacles' heights, estimate direct-sun hours per grid cell per month; show a heat-map overlay; user can override per area. Feeds crop placement (light requirements) and microclimate.
- **Planting layer**: place plantings into beds (square-foot cells, rows, or free placement) with real spacing footprints; drag plants between beds; time slider to see the layout on any date (beds change through the season with successions).
- **Irrigation layer** (optional): zones, lines, emitters with flow; links beds to irrigation zones for water tasks and Home Assistant.
- **Animal layer**: housing footprints with space-per-head checks, runs/paddocks with area for rotation planning.
- **Auto-layout** (from the plan generator, 9.1): proposes bed assignments and placements honouring sun needs, spacing, rotation history, companions (soft), access paths and plant height (tall plants on the shadow side), with a diff the user accepts, edits or rejects.
- **Validation hints**: overcrowding, too little sun for the crop, rotation conflict, height shading neighbours, path width for wheelbarrow/wheelchair (if accessibility selected).
- **Persistence**: geometry stored as GeoJSON-like local coordinates (metres) per site; export PNG/SVG/PDF of the plan; print-friendly bed sheets.

### 7.2 Beds & areas
- **Map**: per site, beds/areas as rectangles, polygons or containers with real dimensions; structures; paths; trees. Drag-and-drop, snap grid, square-foot overlay, zoom/pan, mobile-friendly (implemented by 7.1).
- **Spacing**: planting footprint from spacing; overlap warnings; plant count suggestions.
- **Rotation**: per bed per season history by crop family; conflicts scored from family-specific minimum gap years (catalog values, overridable) and soil-borne disease links; suggestions for next season.
- **Companions**: links with evidence level (`traditional`, `observational`, `peer-reviewed`); shown as hints, never as hard rules.
- **Bed state**: current plantings, soil tests, amendments log, water balance, sensor readings.

## 8. Animals

### 8.1 Catalog
- **Species**: names, requirement profile (thermal comfort via THI or temperature thresholds, wind/rain shelter needs), housing space per head (indoor/outdoor), water need as function of temperature and production, feed requirement model (dry-matter intake % body weight by class), lifecycle parameters (gestation/incubation length, oestrous cycle length, breeding seasonality: photoperiod response), production (eggs, milk, meat, fibre, honey, offspring), common health issues with seasonal/weather risk models (e.g. parasite pressure from warm + wet periods), routine care templates.
- **Breed**: overrides (heat/cold hardiness, laying rate and photoperiod sensitivity, size, seasonality).
- **Initial content**: chicken, duck, goose, turkey, quail, goat, sheep, cattle, pig, rabbit, honeybee; ≥ 3 breeds each where meaningful. Sourced from extension services and literature; user-overridable; custom species/breeds supported.

### 8.2 Groups & individuals
Animals are managed as **groups** (flock, herd, colony) and optionally as **individuals** (tag/name, sex, birth date, breed, parents, weight history, status). Movements between groups and housing/paddocks are logged.

### 8.3 Lifecycle & breeding planner
- Births/hatches are planned **backwards from a target window** chosen by the engine: the window in which newborn requirement profiles (usually narrower than adults') are best met (lowest P(violation)), plus pasture availability for grazers. The engine proposes mating/insemination/egg-setting dates = target − gestation/incubation, respecting the species' breeding seasonality (photoperiod-driven where applicable).
- Tracks heat cycles, pregnancies, due dates, weaning, culling decisions (user-driven).

### 8.4 Care schedule
Routine tasks from templates with intervals **and/or conditions**: health checks, hoof/claw trimming, shearing (timed to weather windows), deworming (condition-based, e.g. after warm-wet periods, plus faecal-egg-count logging; no fixed calendar dogma), vaccinations (user enters the protocol from their vet; templates are editable examples), mite/lice checks, coop/bedding cleaning, hive inspections (only when forecast temperature/wind allow), swarm-season watch (from GDD/forage flow), feeding & mineral restock, water system checks.

### 8.5 Environment & alerts
- **THI** (temperature-humidity index) from forecast hourly temperature + RH; species/breed thresholds from profile → heat-stress alerts with actions (shade, water, ventilation, adjust handling times).
- Cold, wind-chill, wet-cold (lethal for neonates) alerts from profile thresholds.
- Housing microclimate from coop/barn sensors when present.
- Pasture: growth estimate from GDD + water balance; grazing rotation suggestions and feed-gap forecasts (when pasture growth < herd demand).

### 8.6 Production
- Laying forecast for poultry: function of daylight hours (computed per site per day), age, breed, temperature stress; explains seasonal declines and when supplemental light would matter (only if the user wants it).
- Milk, eggs, meat, honey, fibre logging; per-animal or per-group; feed conversion where feed is logged.
- **Withdrawal periods**: medications logged with withdrawal days → products from that animal/group flagged until clear.

## 9. Planning, calendar & task engine

### 9.1 Needs-based plan generator
Turns the household profile (3.1, 3.2), the environment (4) and the catalog into a **season plan** proposal:
1. **Candidate crops**: catalog filtered by preferences and by *feasibility here* (6.4 windows exist in open ground, or in an owned/plannable structure).
2. **Quantities**: for each crop, planting area/plant count = target yield ÷ expected yield per m² (catalog estimate, adjusted by quality score for this site and later by the household's own harvest history), spread into successions so harvests match weekly consumption plus preservation targets.
3. **Fit to constraints** (optimisation): maximise met demand (weighted by preference) subject to area per sun class, monthly water budget (6.6 water need vs. tank/mains budget), weekly labour hours (task duration estimates), budget, rotation and spacing. Solver: greedy with local improvement first (fast, explainable); MAY move to an ILP solver (e.g. OR-Tools CP-SAT) if needed.
4. **Animals**: size flocks/herds/colonies from product targets and per-head production for this environment (8.6), check housing/space/pasture/feed/water feasibility, add start-up items (coop size, fencing) to the budget.
5. **Report**: what is covered (% of each target per month), what is not and why (space, water, season, time), and the single most effective change (e.g. "a 3 × 6 m tunnel would add 9 weeks of tomatoes", "+1 000 L rain tank covers the January deficit").
6. **Accept → schedule**: accepted plan items become plantings/animal plans; the task engine (9.2) takes over. Re-planning compares with current plan and proposes a diff.

### 9.2 Calendar & task engine

- **Task** = what, subject (planting/animal/group/bed/structure/site), window (earliest, ideal, latest), priority, duration estimate, assignee, status (open/done/skipped/missed), reason trace, generator id (so regenerated tasks update instead of duplicating), user-locked flag.
- **Generators**: crop schedule, crop care, water, animal care, animal lifecycle, alerts (weather-triggered), inventory (expiry, seed viability), custom recurring (RRULE) and one-off tasks.
- **Recompute**: nightly, on new forecast, on new observation/sensor data, on edits. Changes to open tasks produce a **change log** entry ("moved 5 days later: forecast frost 14 Sep"); user-locked tasks never move, but get a warning if conditions turn against them.
- **Completion feedback**: completing a task records actual dates/quantities → calibrates models (6.3, 4.6).
- **Views**: Today (prioritised, weather-aware), Week agenda, Month calendar, Year wheel (crop and animal seasons at a glance), per-subject timeline, Gantt of plantings.
- **Export**: iCalendar feeds (per household, per member, per category) with tokenised read-only URLs; Home Assistant calendar entity.

## 10. Records & inventory

- **Harvest log**: planting, date, quantity (weight/count), quality, photos → yield per m² and per plant vs catalog estimate.
- **Pantry & preservation**: items (fresh, canned, frozen, dried, fermented, cellared) with batch, method, date, quantity, location, best-before (from method defaults, editable) → expiry reminders, stock levels; links back to harvest.
- **Seed vault**: packets/lots per variety: source, year, quantity, germination tests (date, n, germinated) → viability estimate by species longevity; reorder reminders when planned sowings exceed stock.
- **Inputs**: fertilisers, amendments, feed, medications, bedding — purchases, stock, usage (linked to tasks).
- **Animal health records**: events, treatments, weights, body condition, FAMACHA, faecal egg counts.
- **Journal**: free notes with photos, tags, linked subjects.

## 11. App experience

Design rule: **the app helps you act.** The first thing anyone sees is what to do today, in plain language, with the how and the why one tap away. Analysis (climate, statistics) is available but never in the way.

### 11.1 Navigation
Bottom navigation (mobile) / sidebar (desktop): **Today · Calendar · Garden** (layout + beds + plantings) **· Animals · More** (Climate, Harvest & Pantry, Seeds, Records, Plan, Settings). Each user chooses their own start screen (default: Today) and which sections they see, so a household member who only wants tasks never has to see charts.

### 11.2 Today (home screen)
- **Header**: date, a one-line weather summary for the site with anything unusual ("Hot day, 34 °C: water early, shade lettuce"; "Frost possible tonight, 2 °C: cover beans").
- **Action groups**, in this order and only when non-empty: **Protect** (urgent weather actions), **Plant** (sow / transplant / harden off), **Water** (which beds, how many litres or minutes, best time), **Feed** (which plants get what nutrient, how much, from the inputs you have), **Harvest** (what is ready or close, with ripeness cues), **Animals** (feeding, water, eggs, care, alerts), **Check** (scouting: what to look for this week, 11.3), **Maintain** (prune, stake, weed, clean).
- **Task card**: verb + subject + where ("Sow carrots, Bed 3, 2 rows"), quantity, a short how-to (steps, depth, spacing, amounts), *why now* (reason trace in plain words), estimated minutes, Done / Skip / Snooze / "Not possible today". Done can capture a quick quantity (harvest kg, eggs, litres) and a photo.
- **Today's load**: total estimated time vs the household's available time; lower-priority items flow to the next suitable day automatically.
- **Coming up**: next 7 days in one compact strip so nothing surprises.
- **Works offline** (PWA): today's and this week's tasks and how-tos are cached.

### 11.3 Scouting & "keep or remove" guide
- **Organism catalog** (part of the catalog, same override rules): pests, diseases, beneficial insects and animals, pollinators, weeds, volunteer seedlings, nutrient deficiency patterns. Each entry: how to recognise it (key features, look-alikes, where on the plant, photos with licence), life cycle, which crops it affects or helps, **verdict with context** (keep / remove / tolerate below a threshold: e.g. "a few aphids with ladybird larvae present: keep, the larvae will clear them"), actions ranked least-harm first (hand-pick, water spray, barrier, encourage predators, organic product, conventional product, only shown per the household's preference), and safety notes (pets, bees, withholding periods).
- **Weekly "what to look for"**: per planting, the organisms whose risk is high now: pest degree-day models and weather-driven disease models (e.g. warm + humid hours for fungal disease) × crop stage. Shown in Today under **Check** with photos.
- **Weed or seedling?**: for beds with recent sowings, show what the sown seedlings look like at their current age next to common weeds for that season.
- **Identify**: browse by symptom (holes in leaves, yellowing between veins, white powder, wilting) or, with the AI co-pilot enabled, by photo (12.4), always ending in a verdict + actions + "check again in N days" task.
- **Logging**: sightings are recorded (observation) and feed local risk calibration ("aphids appear here ~10 days earlier than the model").

### 11.4 Climate explorer (secondary page)
Charts, not tables: day-of-year bands (q10–q90 and median) for day and night temperature, soil temperature, rain and ET0, daylight curve, probability curves for a threshold the user picks, trend over the years, this season's actual weather overlaid on normal, sensor overlay. Every chart has a one-sentence takeaway generated from the data, an accessible data table toggle, and source attribution. Charts follow the dataviz rules in `docs/DESIGN.md` (to be written: palette, light/dark, no colour-only meaning).

### 11.5 Insight panels
- **"What matters here, now"** (replaces the static climate card): a ranked list of conditions computed from the user's actual crops and animals (and, before any exist, from a reference basket of common crops), e.g. "Heat during tomato flowering likely in Dec–Jan (68% of years)", "Lettuce bolts if sown after Sep", "Frost risk for citrus bloom 3% — negligible". Ranking = probability × impact × how soon. Nothing is shown because of a preset; everything is shown because of a number.
- **Site climate explorer**: DOY charts (bands q10–q90) for temperature, soil temperature, rain, ET0, daylight; probability-of-threshold curves where the user picks the threshold (e.g. "chance of tmin ≤ 2 °C by date"); trend; recent anomaly overlay; sensor overlay.
- **Crop explorer**: "Can I grow X here?" with windows, success probability and blockers; what a structure would unlock.
- **Dashboards**: yields, production, feed, water use, task completion; season comparison.

## 12. Integrations

### 12.1 Home Assistant
- MQTT discovery: CropStack publishes sensors (next tasks, alerts, water deficit per bed, THI per animal house, laying forecast) and subscribes to configured HA sensors (4.6).
- REST + HACS custom integration (Bloomery pattern): calendar entity, todo entity (tasks), services (complete task, log harvest, log observation).
- Automations out: irrigation requests per bed (litres or minutes), ventilation/heating suggestions for structures; HA decides and executes, CropStack never actuates directly.

### 12.2 Notifications
Channels: Web Push (HTTPS installs), ntfy, Gotify, Home Assistant, Discord, email (SMTP). Daily digest at chosen time + urgent alerts (lethal-threshold forecasts within 48 h). Quiet hours. Per-category opt-in.

### 12.3 iCalendar
See 9.

### 12.4 AI co-pilot (optional)
Providers: Ollama (local), OpenAI-compatible, Anthropic (Bloomery `ai.py` pattern). The co-pilot is **grounded**: it receives the household's structured context (site environment summary, plantings, animals, open tasks, recent records) and can call read-only tools (query catalog, query environment probabilities). Uses: natural-language questions, photo diagnosis (vision models) of pests/deficiencies/disease with confidence and "verify by" steps, preservation recipes from current pantry/harvest, drafting custom crop/breed profiles for user review. The AI never changes data without user confirmation.

## 13. Data model (target)

Core tables (SQLite, managed with Alembic migrations from v0.5.0):

| Table | Key fields |
|---|---|
| household | id, name, timezone, risk_tolerance |
| membership | household_id, user_id, role |
| user | id, username, password_hash, display_name, lang, units |
| site | id, household_id, name, lat, lon, elevation, boundary (GeoJSON), aspect, slope |
| env_climatology | site_id, version, period, weights_half_life, doy_stats (JSON/blob), trend (JSON), fetched_at |
| env_daily | site_id, date, source (observed/forecast/seasonal/sensor), tmin, tmax, tmean, precip, et0, rh, wind, soil_t, soil_m, fetched_at |
| sensor | id, site_id, target (bed/structure), kind, ha_entity_id/mqtt_topic, unit |
| sensor_reading | sensor_id, ts, value |
| calibration | site_id/target, variable, offset, scale, n, updated_at |
| observation | id, household_id, ts, kind, subject ref, payload JSON |
| structure | id, site_id, kind, geometry, modifier profile JSON |
| bed | id, site_id, name, geometry, area_m2, soil JSON, structure_id? |
| soil_test | bed_id, date, values JSON |
| crop | id, slug, catalog_version, data JSON (profile, phenology…), is_custom |
| variety | id, crop_id, slug, data JSON (overrides), is_custom |
| override | household_id, target (crop/variety/species/breed/template), path, value |
| planting | id, household_id, variety_id, bed_id/area/structure, method, quantity, status, planned JSON, actual JSON, succession_of |
| species / breed | like crop / variety |
| animal_group | id, household_id, species_id, breed_id?, name, housing_id, count |
| animal | id, group_id, tag, name, sex, birth_date, breed_id, dam_id, sire_id, status |
| animal_event | id, animal_id/group_id, ts, kind (weight, health, treatment, breeding, birth, death, move, production), payload |
| task | id, household_id, generator, generator_key, subject ref, title, window_start, ideal, window_end, priority, status, assignee, locked, reason JSON |
| task_change | task_id, ts, before JSON, after JSON, reason |
| harvest | id, planting_id, date, qty, unit, quality |
| pantry_item | id, household_id, name, method, batch, qty, unit, location, made_on, best_before, source_harvest_id |
| seed_lot | id, variety_id, source, year, qty, unit, germ_tests JSON |
| input_item / input_use | stock and usage of fertiliser, feed, medication… |
| household_profile | household_id, version, answers JSON (3.1), needs JSON (3.2), constraints JSON, created_at |
| plan / plan_item | proposed and accepted season plans, items (crop/animal, quantity, area, successions), coverage report JSON, status |
| layout_feature | id, site_id, layer, kind (bed, structure, path, tree, building, tank, fence, zone…), geometry (local metres), height, properties JSON |
| sun_map | site_id, month, grid JSON (direct-sun hours per cell), computed_at |
| organism | id, slug, kind (pest, disease, beneficial, pollinator, weed, deficiency), data JSON (identification, lifecycle, risk model, verdict rules, actions), is_custom |
| sighting | id, household_id, organism_id?, planting_id?, ts, severity, photo, notes |
| notification_channel / notification_log | per user |
| feed_token | ICS/HA read-only tokens |
| setting | key/value for app-wide settings |

## 14. API

REST under `/api/v1`, JSON, session cookie auth (+ API keys for integrations, scoped & revocable). OpenAPI at `/api/docs`. Resource groups: `auth`, `households`, `profile` (setup interview answers), `plans` (generate, diff, accept), `layout` (features, sun map), `today` (aggregated action view), `organisms` (+ sightings, identify), `sites`, `environment` (`/sites/{id}/climate`, `/probability?var=tmin&op=le&x=2&from&to`, `/forecast`, `/anomaly`), `catalog` (crops, varieties, species, breeds, templates; overrides), `beds`, `structures`, `plantings`, `windows` (`/varieties/{id}/windows?site&method`), `animals`, `groups`, `events`, `tasks` (list/filter, complete, skip, lock, changes), `records` (harvests, pantry, seeds, inputs), `observations`, `sensors`, `notifications`, `ical/{token}.ics`, `ha/*`, `ai/*`. Pagination by cursor; ETags on GET; idempotency keys on POST from the offline queue.

## 15. Non-functional requirements

- **Professional quality** (owner, 2026-10-09): personal, non-commercial use only changes licensing, never the bar. The app must look and feel like a polished product: a consistent design system (tokens, type scale, spacing, components, icons, motion), designed empty/loading/error states, no placeholder copy in releases, light and dark themes, responsive phone → desktop, and a visual check of every changed screen before release.
- **Footprint**: container idle RAM ≤ 150 MB, ≤ 256 MB under load; single uvicorn worker + background scheduler task; SQLite WAL.
- **Performance**: window search for 50 varieties × 1 site ≤ 2 s on a Raspberry Pi 4 class CPU (vectorised DOY arrays, cached per site/version).
- **Offline**: PWA caches app shell, today's/this week's tasks, catalog, and queues writes (task completion, logs, observations) with idempotency keys; sync on reconnect; conflict rule: last write wins per field with change log.
- **Quota safety**: Open-Meteo usage per site per day stays ≤ 5% of the free daily limit in steady state (forecast 8×/day small requests; climatology once per year); global request budget with backoff; no request storms on restart.
- **Security**: argon2id, throttled login, CSRF-safe cookie (SameSite=Lax) + JSON-only mutations, security headers, tokens hashed at rest, least-privilege roles, no secrets in logs, dependency updates (Dependabot), container non-root.
- **Privacy**: outbound data inventory shown in Settings; each external service can be disabled (features degrade gracefully, e.g. manual climate entry).
- **Accessibility**: WCAG 2.2 AA: keyboard navigation, labels, contrast in light/dark, no colour-only meaning, reduced motion.
- **i18n**: all strings through a translation layer from the start of v0.5; English first, Afrikaans next (Bloomery tooling: missing-string checker in CI).
- **Units**: stored SI; displayed per user preference.
- **Reliability**: nightly backups with retention, restore, export/import (JSON), migrations tested on a copy before apply.
- **Observability**: structured logs, `/api/health` with component status (db, scheduler, last data refresh per source).

## 16. Data sources, licences & attribution

| Source | Use | Licence / terms | Notes |
|---|---|---|---|
| Open-Meteo Historical (ERA5, ERA5-Land) | climatology, recent weather | CC BY 4.0; free non-commercial (10k calls/day, long ranges weighted) | `models=era5_seamless` |
| Open-Meteo Forecast | 16-day forecast, past 92 days | CC BY 4.0 | hourly RH for THI |
| Open-Meteo Seasonal (ECMWF EC46/SEAS5) | optional seasonal tilt | CC BY 4.0 | ensemble mean/spread |
| Open-Meteo Climate API (CMIP6 HighResMIP, 10 km, to 2050) | optional projections for perennials | CC BY 4.0 | bias-corrected to ERA5-Land |
| OpenStreetMap Nominatim | place / postal search | ODbL; ≤ 1 req/s, identifying UA | search on submit |
| ISRIC SoilGrids | soil defaults | CC BY 4.0 | verify API availability |
| FAO ECOCROP | crop temperature/rain/pH ranges, killing temp, season length | CC BY 4.0 (FAO Data Catalog record) + FAO DB terms: no commercial promotion, no implied endorsement | no official bulk download; Recocrop R package (1,710 taxa) as raw snapshot, spot-checked |
| FAO-56 (Allen et al. 1998) | Kc, stage lengths, root depth, depletion fraction | © FAO 1998; numbers stored as cited facts (via pyfao56, CC0) | never copy table layout or notes |
| Wikidata | names (incl. Afrikaans), cultivar/breed items, ID crosswalk | CC0 | SPARQL |
| World Flora Online | accepted scientific names | CC0 | pinned Zenodo snapshot |
| USDA PLANTS / GRIN | cover-crop characteristics, cultivar names | CC0 / US public domain | thin for vegetables |
| OpenFarm rescue (`thefullnacho/openfarm-crops-rescue`) | seed crop list, spacing, sowing method | CC0 | quality uneven; review every value |
| BBCH monograph (Meier 2018) | growth-stage codes | CC BY 4.0 | |
| DSSAT genotype files | cardinal temps, thermal time (tomato, pepper, cabbage, bean, potato) | BSD-3-Clause | label as model calibration |
| EPPO Codes | organism/crop codes | EPPO open data licence; notice + download date | host/distribution data not bundled |
| GloBI | host–pest, parasitoid, pollinator links | per source dataset | filter rows by licence |
| GBIF / iNaturalist / Wikimedia Commons | organism photos | per image: CC0, CC BY, CC BY-SA only | never NC/ND |
| Wikipedia "List of companion plants" | companion pairs | CC BY-SA 4.0 | pin revision; default `evidence: traditional` |
| FAO DAD-IS | breeds (8,800+) | CC BY 4.0 (FAO DB terms Annex 1) | web export only; structured fields only |
| Extension services, ARC, peer-reviewed literature | catalog values | facts cited per value | never copy prose, tables or images; ARC reproduction needs written permission |
| Permapeople, PFAF, PPDB, Feedipedia, FARAD, CABI, UC IPM text/photos | reference only | NC / ND / all rights reserved | link out, never bundle |

### 16.1 Catalog data policy
- **Licence**: `catalog/` is licensed CC BY-SA 4.0 (`catalog/LICENSE` + `catalog/NOTICE` with FAO terms, EPPO notice, citation strings); code stays MIT. Accepted inputs: CC0, public domain, CC BY, CC BY-SA 4.0. CI rejects NC, ND and unknown licences.
- **Facts, not copies**: single values (depth, spacing, temperatures, intervals) are extracted and cited; prose is written fresh; no source's whole list or structure is mirrored.
- **Provenance**: `catalog/sources.yaml` registry (title, author, url, licence, extra terms, `tos_reviewed`, access); every value carries `unit`, `qualifiers`, `evidence` (`peer-reviewed | government | extension-service | model | grower-reported | traditional`), `confidence`, `rank` (`preferred | normal | deprecated`) and `sources` (ref, retrieved, locator, snapshot hash). Conflicts are kept as ranges or qualified statements, never averaged.
- **Pipeline** (maintainer-side only; self-hosted instances never scrape): per-source fetcher (API/dump first, HTML last) → raw snapshot by SHA-256 outside git (`snapshots.lock`) → tested extractor → merge (hand-curated wins) → schema + licence gate + prose-similarity check → monthly PR for review. Scrapers obey robots.txt, identify themselves, throttle (≈1 req per 1–5 s per host), never log in or accept terms.
- **Private pack** (decided 2026-10-09: the maintainer runs CropStack for personal, non-commercial use, but the repo and image are public): a second catalog root on the server's data volume, `/data/catalog-private/`, same schema as `catalog/`, never committed and never in the image. It may hold values the owner looked up for their own use from any source (incl. ARC guides, NC sources). Loaded after the bundled catalog (private wins over bundled; household overrides win over both); excluded from the licence gate; values shown with a "private" badge.
- **No open source → no invented value**: gaps (home yield/m², seed longevity, frost-kill temps, vernalization, stage-wise nutrient uptake, SA remedy registers, withdrawal periods) are curated from cited facts, labelled (`commercial benchmark`, `US-calibrated`), or entered by the user (e.g. withdrawal days from the label).

The UI MUST show attribution wherever data from a source is displayed, and a Settings → Data sources page listing all of the above with what is sent.

## 17. Testing strategy & acceptance criteria

**Test layers**: pure-function unit tests (engines), property-based tests (Hypothesis) over synthetic environments, API tests, Playwright E2E with faked external services, migration tests, performance benchmarks.

**Global acceptance criteria**
- **AC-P1 (no presets)**: the code base contains no location/climate-type branches; a CI check greps for banned patterns (`hemisphere ==`, `country ==`, climate-type enums) outside of display formatting.
- **AC-P2 (climate shift)**: given synthetic environment E and a planting plan, adding a cold tail to E (frost in 30% of years) produces frost alerts/window changes for frost-sensitive crops *without any configuration change*; removing it removes them.
- **AC-P3 (symmetry)**: mirroring a synthetic climate by 182 days (hemisphere swap) shifts all windows by ~182 days and changes nothing else.
- **AC-P4 (explainability)**: every generated task has a non-empty reason trace that references the inputs used.
- **AC-P5 (customisation)**: any catalog field can be overridden per household, and the override changes engine output in the expected direction (tested per field family).
- **AC-P7 (action first)**: a new household that finishes the setup interview and accepts a plan sees a Today screen with at least one actionable task per applicable group within the season's windows; every task card shows how-to and why.
- **AC-P8 (setup drives plan)**: changing an interview answer (e.g. halving the area or the water budget) changes the proposed plan in the expected direction and the coverage report explains the difference.
- **AC-P6 (recompute)**: a new forecast with a lethal event inside an open task's window moves or flags that task within one recompute cycle and records a change-log entry.

Module-level acceptance criteria are listed with each phase in `PLAN.md`.

## 18. Superseded behaviour (to remove)

The v0.3/v0.4 climate card used fixed heuristics that violated P1/P2. **Done in v0.6.0** (kept here for history):
- `HOT_C = 30` global hot-day threshold → replaced by per-subject `stress_max` probabilities.
- "Show frost dates only if frost occurs in ≥ 50% of years" → replaced by relevance ranking (11).
- Rainfall regime labels (≥ 60% / ≤ 40% cold-half share) → kept only as a descriptive sentence generated from the distribution, never used for decisions.
- Single frost threshold 0 °C and frost-date quantiles → generalised to `P(tmin ≤ x)` for each subject's `lethal_min`.
- Cache-forever climate → rolling, recency-weighted, yearly refresh.

## 19. Open questions

1. Multi-site per household in v0.5 or later? (Spec supports it; UI can start with one.)
2. Seasonal forecast tilt: on by default once validated, or always opt-in?
3. Catalog contribution workflow: PRs to the repo only, or an in-app "share my custom crop" export?
4. Pasture model fidelity: simple GDD × water-balance index, or a published grass growth model?
5. Language order after English: Afrikaans first (as Bloomery)?
6. ~~ARC (South Africa) sowing guidelines: request written reuse permission from ARC-VOPI?~~ **Decided 2026-10-09**: not now. Personal use goes in the private pack (§16.1); ask ARC only if those values should become part of the public catalog.
7. ~~Catalog licence CC BY-SA 4.0?~~ **Decided 2026-10-09**: yes for the public `catalog/` (no commercial plans; keeps Wikipedia/BY-SA inputs usable).
