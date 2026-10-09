# PLAN

Roadmap implementing [`SPEC.md`](SPEC.md). Every task is atomic and resumable in a fresh session: it names the files, the behaviour and how it is verified. Section numbers like §6.4 refer to SPEC.md.

**Order rationale**: get to a useful **Today** screen (what to plant, water, feed, harvest, check) as early as possible, then deepen: layout and planning, animals, analysis, integrations.

**Definition of done (every task)**: code + tests (unit; API; E2E for UI) pass in CI, ruff clean, `npm run build` clean, docs updated (WIKI for behaviour, ARCHITECTURE for structure, CHANGELOG `[Unreleased]` for user-facing), no new P1 violations (§2).

---

## Done

### Phase 0 — Foundation (v0.1.0) ✅
- [x] Repo layout mirroring Bloomery; FastAPI + SQLite + React/Vite/Tailwind PWA; non-root multi-arch Docker; CI (lint, tests, build, GHCR, auto-release); Dependabot; templates; living docs.
- [x] GitHub repo + GHCR image public; ZimaOS compose + install/update guide.

### Phase 1 — Accounts & garden profile (v0.2.0) ✅
- [x] Users (argon2id, IP throttle, registration modes), garden profile (location, frost risk), setup/home screens, tests + E2E.

### Phase 2 — Climate v1 (v0.3.0–v0.4.0) ✅ (superseded by Phase 4, §18)
- [x] Open-Meteo archive (`era5_seamless`, 30 y), climate cache, frost dates at risk, zone, daylight, monthly normals, rain + regime, hot days; place search (Nominatim); card on Home.
- [ ] User: confirm real values on ZimaOS install (rain regime, rain/yr, hot days look right for the Western Cape).

---

## Phase 3 — Platform for growth (v0.5.0)
Goal: the foundations everything else needs, before data volume makes changes expensive.

**3.1 Migrations**
- [ ] Add Alembic (`backend/alembic/`, `alembic.ini`), baseline revision matching current tables (`user`, `garden`, `climatecache`).
- [ ] Run `alembic upgrade head` in `entrypoint.sh` before uvicorn; replace `create_all` in `init_db` with migration check (tests use `upgrade head` on a temp DB).
- [ ] Migration test: upgrade from a v0.4.0 DB fixture keeps users/gardens.
- [ ] LESSON + WIKI: "every schema change = Alembic revision".

**3.2 Households, roles, sites**
- [ ] Tables `household`, `membership(role)`; migrate each existing user into their own household (owner).
- [ ] Rename `garden` → `site` (keep data; add `household_id`, `elevation`, `boundary`); API alias `/api/garden` → `/api/v1/sites/current` for one release.
- [ ] Role checks dependency (`require_role`); tests for owner/member/viewer permissions.
- [ ] Invite flow: owner creates an invite link (token, role, expiry) → registration via invite even when registration is closed.
- [ ] Settings UI: household name, members list, invite, change role, remove.

**3.3 API & app shell**
- [ ] Version API under `/api/v1` (keep `/api/health` unversioned); update frontend client.
- [ ] Router + navigation per §11.1 (Today · Calendar · Garden · Animals · More); per-user start screen and visible sections stored in user preferences.
- [ ] Move the v0.4 climate card off Home into More → Climate (temporary until Phase 11 charts).
- [ ] i18n layer from day one: `t()` / `_()` (Bloomery pattern), English strings extracted, CI missing-string checker.
- [ ] Units preference (metric/imperial) with formatting helpers; store SI.
- [ ] Background scheduler task (asyncio, single worker) with job registry, last-run status in `/api/health`.
- [ ] Settings → Data sources page (§16): services, what is sent, enable/disable switches.

**3.4 Catalog infrastructure**
- [ ] JSON Schemas: `data/schema/{requirement_profile,crop,variety,species,breed,organism,task_template}.json` (§5, §6.1, §8.1, §11.3).
- [ ] Loader: validate `data/**/*.yaml` at startup and in CI; upsert into DB with `catalog_version`; never overwrite user overrides.
- [ ] Override mechanism (`override` table, JSON-path per field) + merged view helper `effective(entity, household)`; tests for override/reset.
- [ ] Source tracking: every numeric field may carry `source` (citation id) → `data/sources.yaml`.

**Acceptance**: v0.4.0 DB upgrades cleanly; a second member (e.g. the user's wife) can be invited, chooses Today as start screen and never sees the climate page unless she opens it; catalog YAML with a schema error fails CI.

## Phase 4 — Environment engine v2 (v0.6.0) §4
Goal: probabilistic, self-updating environment; remove v1 heuristics (§18).

**4.1 Climatology distributions**
- [ ] `environment/climatology.py`: build 366 DOY bins with ±7-day circular window; per bin weighted quantiles q05…q95, mean, sd for tmin/tmax/tmean/soil_t; precip mean, P(wet), dry-spell stats; et0; rh mean (fetch `relative_humidity_2m_mean`, `et0_fao_evapotranspiration`, `wind_speed_10m_max` daily).
- [ ] Recency weights (half-life H, default 10 y, setting) and per-DOY linear trend with significance; shift to current-year trend when p < 0.05.
- [ ] Storage `env_climatology` (compressed JSON/numpy blob), versioned; auto refresh each January + on site move ≥ 1 km (scheduler job).
- [ ] Query API: `prob(var, op, x, doy)`, `expected_gdd(start, end, base, cutoff)`, `chill(start, end, model)`, `water_balance(start, end, kc)`; vectorised (numpy) and unit-tested against synthetic data with known answers.
- [ ] Property tests (Hypothesis): monotonic CDF; hemisphere mirror (AC-P3); recency weighting moves stats toward recent years.

**4.2 Recent weather & forecast**
- [ ] `env_daily` table; jobs: forecast (16 d, every 3 h, small variable set) and past 92 days (daily); quota budget + backoff; dedupe on restart.
- [ ] Blending function per §4.4 with lead-time uncertainty; tests for each horizon band.
- [ ] Season anomaly (GDD and rain vs normal to date).

**4.3 Calibration hooks**
- [ ] `sensor`, `sensor_reading`, `calibration` tables; manual sensor entry API; bias fit after ≥ 14 overlapping days (robust linear fit); apply to forecasts/climatology per target.
- [ ] `observation` table + API (frost seen, first flower, first harvest, laying stopped…).

**4.4 Remove v1 heuristics**
- [ ] Delete `HOT_C`, frost-headline rule, regime-driven logic; keep descriptive sentence generator only (§18). CI banned-pattern check (AC-P1).

**Acceptance**: AC-P1, AC-P2 (cold tail appears/disappears), AC-P3 pass on the environment layer; forecast refresh stays within quota budget in a 24 h simulated run.

## Phase 5 — Crop & organism catalog content (v0.7.0) §6.1, §11.3
- [ ] Source list `data/sources.yaml`: extension services (university extension guides; ARC South Africa where reusable), FAO-56 Kc table, ECOCROP (verify terms), literature; licence notes per source.
- [ ] Verify ECOCROP reuse terms; if reusable, script `scripts/import_ecocrop.py` to seed temperature/rain ranges with citation.
- [ ] Write 60 vegetable & herb crops (`data/crops/*.yaml`): profile (§5), phenology GDD targets or DTM, spacing, depth, germination curve, family, nutrient demand per stage, Kc, companions (with evidence level), harvest ripeness cues, storage/preservation, yield/m², how-to text for each task type.
- [ ] Varieties: ≥ 2 per crop (e.g. heat-tolerant vs standard), sourced.
- [ ] 20 fruit species (trees, vines, berries) with chill requirements, bloom frost sensitivity, pruning windows.
- [ ] 5 cover crops.
- [ ] Organism catalog v1 (`data/organisms/*.yaml`): 40 common pests/diseases/beneficials/weeds/deficiencies with identification, look-alikes, verdict-with-context rules (keep / remove / tolerate below threshold), least-harm actions, safety notes, risk model (degree-day or weather rule) where published; photos with licences.
- [ ] Catalog browser UI (search, filter, detail with sources) + override editor + "create custom crop/variety/organism" (clone or blank).
- [ ] CI: schema validation, every numeric field has a source or `estimate: true`, no duplicate slugs.

**Acceptance**: catalog loads in < 1 s; overriding a variety's `lethal_min` changes its windows (AC-P5 for crops).

## Phase 6 — Crop engine: phenology, windows, tasks (v0.8.0) §6.3–6.6, §9.2
**6.1 Phenology**
- [ ] `engine/phenology.py`: emergence from soil-temperature thermal time; stage progression by GDD (base, cutoff); photoperiod & vernalization triggers; perennial dormancy/chill/budbreak; expected + p10/p90 paths using environment distributions.
- [ ] Tests with synthetic climates and hand-computed GDD sums.

**6.2 Window finder**
- [ ] `engine/windows.py`: daily candidate starts over 18 months × methods; success-probability factors; quality score; viable windows at risk tolerance; best sub-window; protected-growing rerun with structure modifiers.
- [ ] "Can I grow X here?" verdict + blockers; API `GET /api/v1/varieties/{id}/windows?site=…`.
- [ ] Performance benchmark: 50 varieties ≤ 2 s on CI runner (scaled target for Pi documented).

**6.3 Plantings**
- [ ] `planting` table + API (CRUD, status transitions, actual stage dates, successions link).
- [ ] UI: add planting from a window ("Plant this"), list per bed, planting timeline.

**6.4 Task engine core**
- [ ] `task`, `task_change` tables; generator interface (`generate(household, horizon) -> [TaskSpec]`) keyed by `generator_key` for idempotent regeneration; user-locked handling; change log with reasons.
- [ ] Crop schedule generator (sow indoors, harden-off steps, transplant, direct sow, successions, harvest window with ripeness cues).
- [ ] Crop care generator (thin, stake, mulch, prune/pinch, protect from forecast lethal/stress events).
- [ ] Recompute job (nightly + on forecast/observation/edit); AC-P6 test.

**6.5 Water** §6.6
- [ ] Per-bed soil-water balance (FAO-56 simplified), soil water-holding capacity from texture, root depth by stage; irrigation tasks with litres and best time of day; sensor override; water budget tracking vs household budget.

**6.6 Feeding** §6.5.1
- [ ] Inputs inventory minimal (product, N-P-K, form) so feed tasks can name what to use.
- [ ] Nutrient demand per stage → feed tasks with dose per plant/m² from N-P-K; fallback suggestion when no input; cautions.

**6.7 Scouting** §11.3
- [ ] Organism risk evaluation per planting × stage × weather; weekly "what to look for" tasks with photos and keep/remove verdicts; sightings API; local timing calibration.
- [ ] "Weed or seedling?" comparison for recent sowings.

**Acceptance**: for a synthetic Mediterranean and a synthetic frosty climate, the same tomato and lettuce varieties get different, sensible windows without configuration (AC-P2/P3); all tasks have reason traces (AC-P4).

## Phase 7 — Today screen & calendar (v0.9.0) §11.2, §9.2
- [ ] `GET /api/v1/today`: grouped actions (Protect, Plant, Water, Feed, Harvest, Animals, Check, Maintain), weather header with plain-language advice, load vs available time, next-7-days strip.
- [ ] Task card component: how-to steps, why-now, minutes, Done (with quantity/photo), Skip, Snooze, Not possible today; optimistic UI.
- [ ] Load balancing: overflow low-priority tasks to the next suitable day.
- [ ] Offline: cache today/week + how-tos; queued completions with idempotency keys; sync banner.
- [ ] Calendar views: week agenda, month, year wheel, per-subject timeline.
- [ ] iCalendar feeds (household/member/category tokens).
- [ ] Notifications v1: daily digest + urgent alerts via ntfy / Gotify / HA webhook / Discord / Web Push (Bloomery pattern).
- [ ] E2E: Today shows tasks for a seeded household; completing a harvest logs quantity; offline completion syncs.

**Acceptance**: AC-P7 (with a manually created plan until Phase 8); hallway test with a non-technical household member (the user's wife): can she tell in 10 seconds what to do today and how? Feedback goes into this plan.

## Phase 8 — Guided setup, layout editor, plan generator (v0.10.0) §3.1–3.2, §7.1, §9.1
**8.1 Setup interview**
- [ ] Question graph (`data/interview.yaml`): topics (§3.1 table), questions, input types, conditions, "why we ask", mapping to profile fields.
- [ ] Wizard UI: one question per screen on mobile, progress, skip, resume, edit later; accessible.
- [ ] `household_profile` versioned storage + API.

**8.2 Needs model**
- [ ] Consumption targets from household size × diet × self-sufficiency (cited reference intakes) → editable per-crop weekly targets table.
- [ ] Animal product targets.

**8.3 Layout editor**
- [ ] Canvas tech decision (SVG + pointer events vs a library such as Konva; criteria: touch, performance, bundle size, licence) — spike, record in TOOLING.
- [ ] Draw/edit features: boundary, beds (rect/polygon/circle/keyhole), containers, structures, paths, trees (canopy, height), buildings/walls (height), tanks, fences; snap, rulers, labels, layers, undo/redo, zoom/pan/touch.
- [ ] Template shapes ("4 raised beds 1.2 × 2.4 m"); optional background image tracing.
- [ ] Sun model: sun path per site/day, obstacle shadows → direct-sun hours grid per month; heat-map overlay; manual override.
- [ ] Planting layer with spacing footprints and date slider; drag between beds.
- [ ] Validation hints (overcrowding, sun mismatch, rotation conflict, height shading, path width).
- [ ] Export PNG/SVG/PDF, print bed sheets.

**8.4 Plan generator**
- [ ] Candidate filtering by feasibility (windows) and preferences.
- [ ] Quantities from targets ÷ expected yield; successions to match weekly demand + preservation.
- [ ] Constraint fit (area per sun class, monthly water, weekly labour, budget, rotation, spacing): greedy + local improvement; explain unmet demand; "single most effective change".
- [ ] Auto-layout into beds; diff view; accept → plantings + tasks.
- [ ] Re-plan diff when profile or conditions change (AC-P8).

## Phase 9 — Animals (v0.11.0–v0.12.0) §8
**9.1 Catalog & records**
- [ ] Species/breed YAML for chicken, duck, goose, turkey, quail, goat, sheep, cattle, pig, rabbit, honeybee (profiles, housing space, water & feed models, lifecycle, production, care templates), sourced.
- [ ] Tables `animal_group`, `animal`, `animal_event`; UI for groups, individuals, events (weights, health, treatments with withdrawal periods, breeding, births, deaths, moves, production).

**9.2 Care & environment**
- [ ] Care template generator (interval- and condition-based); hive inspections gated by forecast.
- [ ] THI from hourly forecast (T + RH) vs species/breed thresholds → heat alerts with actions; cold/wet/wind alerts for adults and neonates.
- [ ] Withdrawal-period flags on products.

**9.3 Lifecycle & production**
- [ ] Breeding planner: target birth window from newborn profile × environment × pasture; back-computed mating/egg-setting dates; seasonality.
- [ ] Laying forecast (daylight, age, breed, heat stress); egg/milk/honey logging dashboards.
- [ ] Pasture growth index (GDD × water balance) and feed-gap forecast; grazing rotation suggestions.

**Acceptance**: AC-P2 for animals (adding a hot humid tail creates THI alerts without configuration); animal tasks appear in Today under Animals.

## Phase 10 — Harvest, pantry, seeds, inputs (v0.13.0) §10
- [ ] Harvest log with yields vs expected; feeds yield estimates for the plan generator.
- [ ] Pantry & preservation inventory with batches, methods, best-before defaults, expiry tasks.
- [ ] Seed vault: lots, germination tests, viability by species longevity, reorder reminders from planned sowings.
- [ ] Inputs inventory full (fertiliser, feed, medication, bedding) with usage linked to tasks.
- [ ] Journal with photos and tags.

## Phase 11 — Climate explorer & insights (v0.14.0) §11.4–11.5
- [ ] `docs/DESIGN.md`: palette, chart rules (light/dark, accessible), typography.
- [ ] Charts: DOY bands (temperature day/night, soil, rain, ET0), daylight curve, threshold probability curves (user-picked), trend, this-season overlay, sensor overlay; data-table toggle; generated takeaway sentence; attribution.
- [ ] "What matters here, now" ranking (probability × impact × soonness) from the household's crops/animals; reference basket before any plantings.
- [ ] Dashboards: yields, production, water use, task completion; season comparison.

## Phase 12 — Home Assistant (v0.15.0) §12.1
- [ ] MQTT discovery publisher (tasks, alerts, bed water deficit, THI, laying forecast) and subscriber for configured sensors.
- [ ] HACS custom integration (config flow, calendar + todo entities, services: complete task, log harvest, log observation), Platinum-quality patterns from Bloomery.
- [ ] Irrigation request events per bed/zone (litres/minutes) for HA automations.

## Phase 13 — AI co-pilot (v0.16.0) §12.4
- [ ] Provider abstraction (port Bloomery `ai.py`), settings UI, key never returned.
- [ ] Grounded context builder + read-only tools (catalog, environment probabilities, plantings, tasks).
- [ ] Chat; photo diagnosis → organism candidates with confidence, verdict, actions, follow-up task; preservation recipes from pantry; draft custom profiles for review.

## Phase 14 — Quality & reach (v1.0.0)
- [ ] Afrikaans translation (+ CI completeness check).
- [ ] WCAG 2.2 AA audit (axe in CI + manual keyboard/screen-reader pass).
- [ ] Performance pass on Raspberry Pi class hardware; memory within budget (§15).
- [ ] Backups (nightly, retention, restore), JSON export/import.
- [ ] Optional seasonal forecast tilt and CMIP6 projections for perennials (§4.4, §4.2).
- [ ] Optional SoilGrids defaults.
- [ ] User guide with screenshots, README refresh, demo seed script.

## Later — Homestead suite extras
- [ ] Orchard depth (rootstocks, grafting records, thinning calculators)
- [ ] Multi-site UI (data model already supports it)
- [ ] Catalog sharing (export/import custom crops, community packs)
- [ ] Equipment & maintenance tracking
