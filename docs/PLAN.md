# PLAN

Roadmap implementing [`SPEC.md`](SPEC.md). Every task is atomic and resumable in a fresh session: it names the files, the behaviour and how it is verified. Section numbers like §6.4 refer to SPEC.md.

**Versions** are assigned when a phase (or part of one) ships; see CHANGELOG.md.

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

## Open follow-ups (carry-over, check first)
Items left open by earlier releases. Close them before or alongside the phase they belong to.
- [x] v0.9.0: rerun the browser flows after the redesign (sign up, garden setup and edit, household rename, invite link, role change, remove member, settings switches, log out) and commit them as an E2E script.
- [x] v0.9.0: run `npm run screenshots` in CI against a seeded server and upload the images as artifacts (PLAN 6.9).
- [ ] v0.9.0: Sheet/Dialog, Tabs, Toast, Select in the UI kit with the first screen that needs them (PLAN 6.9).
- [x] v0.9.0: unchecked radio in dark mode renders as a filled grey dot (browser `accent-color`); style the radio to match the tokens.
- [x] (2026-10-09, owner: "pulling into zima perfectly") Owner: confirm real climate and forecast values from the ZimaOS install (first real Open-Meteo call; the sandbox gets 429/proxy errors).
- [ ] Climate page is the v0.4 card restyled; charts come with the climate explorer (Phase 11).

---

## Phase 3 — Platform for growth (v0.5.0)
Goal: the foundations everything else needs, before data volume makes changes expensive.

**3.1 Migrations**
- [x] Alembic 1.20 in `backend/app/migrations/` (inside the package so the image ships it), dev CLI config `backend/alembic.ini`, batch mode for SQLite, constraint naming convention on `SQLModel.metadata`.
- [x] Baseline `0001` = v0.4.0 schema; creates only missing tables so v0.1–v0.4 installs (no Alembic history; v0.2 without `climatecache`) converge without special cases.
- [x] `init_db()` runs `upgrade head` on every start (app lifespan, not entrypoint: same path in tests and image), with `PRAGMA foreign_keys=OFF` during migrations.
- [x] Tests: fresh DB + model/migration drift check (`compare_metadata`), upgrades from real v0.2.0 / v0.4.0 schemas keep data, foreign keys back on, table rebuild does not cascade-delete (regression proven to fail without the guard).
- [x] LESSON + WIKI + CONTRIBUTING: every schema change = Alembic revision.

**3.2 Households, roles, sites**
- [x] Tables `household`, `membership(role)` (one household per user for now), `invite`; migration 0002 makes each existing user the owner of their own household (household.id = user.id).
- [x] `garden` → `site` owned by the household (same ids; one site per household for now); climate cache rebuilt empty (refetches). `elevation`/`boundary` deferred to Phase 4 / Phase 8 when used.
- [x] API moved to `/api/v1` in 3.3 (`/sites/current`).
- [x] Role checks (`MemberDep`, `OwnerDep`, `EditorDep`, `require_role`); garden location = owner only.
- [x] Invites: owner creates a link (role, 7 days, single use, SHA-256 hash stored); public `GET /api/invites/{token}`; registration with invite works when sign-up is closed.
- [x] Household page: rename, people with role change and remove (removes their login; last-owner and self guards), invite link with copy (secure context) or select, open invites with cancel. Members without a garden see a waiting screen; edit button only for owners.
- [x] Tests: 6 API tests (ownership, invite join, single use + hashing, expiry/revoke, roles/removal, cross-household isolation) + migration tests for 0002 + Playwright two-browser invite E2E.

**3.3 API & app shell**
- [x] API under `/api/v1` (`/api/health` unversioned); garden → `/api/v1/sites/current` (+ `/climate`); no aliases (pre-1.0, PWA auto-updates).
- [x] React Router 8 (declarative) + bottom nav **Today · Garden · More** (Calendar/Animals tabs join when they have content); More → Climate, Household, Settings, Log out, version.
- [x] Per-user prefs (`user.prefs` JSON, migration 0003): start screen (today/garden/climate) and units; Settings page with optimistic radios. Hidden-sections setting dropped: analysis already lives under More, so nobody sees it unless they open it.
- [x] v0.4 climate card moved off Home to More → Climate (until Phase 11 charts); Today placeholder explains what arrives.
- [x] i18n layer: every UI string through `t()` / `N_()` (`src/i18n.ts`); locale files + CI missing-string checker added with the first translation (Phase 14).
- [x] Units helpers (`src/units.ts`: °C/°F, mm/in, m/ft); climate card converts; storage stays SI.
- [x] → done in 4.2: background scheduler; Settings → Data sources.

**3.4 Catalog infrastructure**
> ✅ Sourcing research done (2026-10-09): [`research/catalog-data-sources.md`](research/catalog-data-sources.md); storage = YAML in `catalog/` (CC BY-SA 4.0) per SPEC §16.1.
- [x] Models in `backend/app/catalog.py` (Pydantic: `Value` with provenance, `Range`, requirement profile §5, `Crop`, `Variety`, `Species`, `Breed`, `Organism`, `TaskTemplate`, `Source`); JSON Schemas generated into `catalog/schema/` by `scripts/catalog_schema.py` (CI test checks they're current). Kind-specific fields live in `params` until their engines need typed fields.
- [x] Loader: bundled catalog validated at start (any problem stops start-up; tests run the same check in CI); held in memory, not copied to the DB (read-only data; deviation from the original "upsert into DB" idea).
- [x] Overrides: `catalogoverride` table (migration 0005), dotted field paths, validated against the schema; `effective()` = parent → item → private → household overrides; API `GET/PUT/DELETE /api/v1/catalog/{kind}/{slug}[/overrides]`, editors only.
- [x] Provenance per value (SPEC §16.1) + `catalog/sources.yaml` (26 sources from the research, with `use: bundle | facts-only | link-only`).
- [x] `catalog/LICENSE` (CC BY-SA 4.0, SPDX text) + `catalog/NOTICE` + `catalog/README.md`; README states MIT doesn't cover `catalog/`.
- [x] Licence gate: `bundle` needs an open licence; values may not cite unknown or `link-only` sources.
- [x] Private pack: `<data>/catalog-private/` loaded after bundled, errors collected for the owner, `origin` = private / bundled+private; `POST /api/v1/catalog/reload`.
- [x] Tests: 16 (real catalog loads, inheritance, private pack, 7 invalid-content cases, licence gate, parents, browse, override/reset/validation, roles + household isolation).
- [x] → Phase 5: catalog browser UI with numbered sources and the credits page (v0.10.0).

**Acceptance**: v0.4.0 DB upgrades cleanly; a second member (e.g. the user's wife) can be invited, chooses Today as start screen and never sees the climate page unless she opens it; catalog YAML with a schema error fails CI.

## Phase 4 — Environment engine v2 (v0.6.0) §4
Goal: probabilistic, self-updating environment; remove v1 heuristics (§18).

**4.1 Climatology** ✅ (v0.6.0; design changed from DOY bins to analog years, SPEC §4.2)
- [x] `environment.py`: analog-year `Climatology` from the raw record (365-day years), recency weights (half-life 10 y), significant temperature trend removed (shift past years to today's level).
- [x] Queries: `prob_any` (windows incl. year-end wrap), `daily_prob`, `daily_quantiles`, `gdd_totals`, `days_to_gdd` (∞ = doesn't mature), `water_deficit`; weighted inverse-CDF quantiles.
- [x] Storage `climatearchive` (raw daily record, 7 variables, migration 0004 drops `climatecache`); refresh on access when moved / new complete year / format change; stale record kept if refresh fails.
- [x] Endpoints `…/climate/probability`, `…/climate/bands`; in-process climatology cache.
- [x] Tests (AC-P2 cold tail, AC-P3 hemisphere mirror, recency, trend vs noise, year-end wrap, GDD, water) — 13 engine + 6 API/description tests.
- [ ] → PLAN 6.1: chill accumulation (needs perennial phenology).

**4.2 Recent weather & forecast** ✅ (v0.8.0)
- [x] `external.fetch_forecast`: Open-Meteo forecast, 16 days ahead + 92 days back, 9 daily variables (incl. precipitation probability, WMO weather code); ~8 weighted calls per refresh.
- [x] `forecast` table (one row per site, migration 0006); refresh when missing, moved or older than 3 h; stale copy served if a refresh fails.
- [x] `environment.with_forecast`: forecast written into every analog year (certain for 16 days, then climatology). Shortcut noted: no lead-time spread, no 17–46-day blend yet.
- [x] Season anomaly (`weather.anomaly`): last 30 days vs the same days in the site's climate (temperature difference, rain total and its percentile among past years).
- [x] Background scheduler (`app/scheduler.py`): `@job` registry, sync jobs in a thread, first run 60 s after start, errors recorded per job; `forecast` job every 30 min refreshes stale sites of households with the forecast on; status in `/api/health` (`jobs`); `CROPSTACK_SCHEDULER=false` in tests.
- [x] Household switches (`household.settings`: forecast, place search; owner only) and Settings → Data sources (what is sent, when, licence; switches for optional sources). Place search hidden and refused when off.
- [x] Today: weather card (today, 7 days with icons and rain chance, last-30-days line), hidden when the forecast is off; light/dark checked.
- [x] Tests: 8 (conditioning incl. year wrap, anomaly, rows/split, scheduler, API fresh/stale/switches/roles).

**4.3 Calibration hooks**
- [ ] `sensor`, `sensor_reading`, `calibration` tables; manual sensor entry API; bias fit after ≥ 14 overlapping days (robust linear fit); apply to forecasts/climatology per target.
- [ ] `observation` table + API (frost seen, first flower, first harvest, laying stopped…).

**4.4 Remove v1 heuristics** ✅ (v0.6.0)
- [x] `HOT_C`, the 50 % frost-headline rule and rainfall-regime labels removed; card describes data (rain season share, annual extremes, frost nights, frost dates at the person's risk, trend).
- [x] `tests/test_no_presets.py` (AC-P1): fails on hemisphere/latitude-sign/country/climate-type branches or global HOT/COLD constants.

**Acceptance**: AC-P1, AC-P2 (cold tail appears/disappears), AC-P3 pass on the environment layer; forecast refresh stays within quota budget in a 24 h simulated run.

## Phase 5 — Crop & organism catalog content (v0.10.0 = 5a) §6.1, §11.3
- [x] `catalog/sources.yaml` from `docs/research/catalog-data-sources.md` (licence, extra terms, `tos_reviewed`, access per source).
- [x] Ingestion package `scripts/ingest/` (SPEC §16.1): fetcher with identifying User-Agent, robots.txt check, 2 s/host throttle; raw snapshots by SHA-256 in `.ingest-cache/` (git-ignored) + committed `snapshots.lock`; pure extractors with synthetic-fixture tests; merge where hand-curated values win (v0.10.0).
- [x] Fetchers v1: pyfao56 tables (FAO-56 Tables 11/12/22: stage days, Kc, height, root depth, p), Harrington germination via OSU (°F→°C, days to emergence), OpenFarm rescue (spacing, height, sun; grower-reported, low confidence), GBIF species match (`check`: accepted name + family).
- [x] Fetcher v2a (v0.12.0): ECOCROP via the Recocrop table on CRAN (temperature, pH, cycle, annual rain; all 29 crops spot-checked; KTMP skipped, 0 is ambiguous).
- [ ] Fetchers v2b: DSSAT species files (cardinal temperatures, model), Wikidata (Afrikaans labels: the API answers with an identifying UA; SPARQL endpoint blocked from the sandbox), WFO snapshot, USDA PLANTS JSON (cover crops), EPPO Codes, Wikipedia companion list (pinned revision).
- [ ] Monthly GitHub Actions job: run fetchers, open a PR with the YAML diff for review.
- [ ] Prose-similarity CI check (catalog text vs snapshot text) to prevent copied expression.
- [x] 29 core vegetables (v0.10.0): curated base (names en/af, accepted name, APG IV family, rotation group, life cycle, fresh description) + pipeline values.
- [ ] Write 60 vegetable & herb crops (`catalog/crops/*.yaml`): profile (§5), phenology GDD targets or DTM, spacing, depth, germination curve, family, nutrient demand per stage, Kc, companions (default `evidence: traditional` + mechanism tag; promote only with a pair-specific study), harvest ripeness cues, storage/preservation, yield/m², how-to text for each task type.
- [ ] Varieties: ≥ 2 per crop (e.g. heat-tolerant vs standard), sourced.
- [ ] 20 fruit species (trees, vines, berries) with chill requirements, bloom frost sensitivity, pruning windows.
- [ ] 5 cover crops.
- [ ] Organism catalog v1 (`catalog/organisms/*.yaml`): 40 common pests/diseases/beneficials/weeds/deficiencies with identification, look-alikes, verdict-with-context rules (keep / remove / tolerate below threshold), least-harm actions, safety notes, risk model (degree-day or weather rule) re-implemented from published rules (Hutton, Smith, Gubler-Thomas; US degree-day models flagged `US-calibrated`); photos only CC0/CC BY/CC BY-SA, licence + author stored per image.
- [x] Catalog browser UI: Crops list with search (en/af/scientific/family), crop detail in plain words with numbered sources, credits page "Where the crop data comes from" (v0.10.0).
- [ ] Override editor + "create custom crop/variety/organism" (clone or blank).
- [x] (v0.14.0; fetchers v2b and prose-similarity check still open above) **Contribution and perpetual collection** (owner request 2026-10-09): `docs/CONTRIBUTING-CATALOG.md` (YAML schema, evidence levels, source and licence rules, worked example); issue forms "Request a species" and "Report or correct a value"; `catalog-contribution` PR template; `scripts/coverage.py` (per crop/animal: which requirement fields are empty or estimates) published as `docs/COVERAGE.md` and used to label issues "needs data"; CI validates contributions (schema, sources, prose similarity, `catalog/NOTICE` licences); monthly ingest job (above) keeps running forever; in-app "Suggest a correction" link on each crop that opens a pre-filled issue.

- [x] CI: schema validation, every numeric field has a source or `estimate: true`, no duplicate slugs, crop file name = slug.

**Acceptance**: catalog loads in < 1 s; overriding a variety's `lethal_min` changes its windows (AC-P5 for crops).

## Phase 6 — Crop engine: phenology, windows, tasks §6.3–6.6, §9.2
**6.1 Phenology**
- [x] (v0.13.0, GDD only; photoperiod/vernalization/perennials still open) `engine/phenology.py`: emergence from soil-temperature thermal time; stage progression by GDD (base, cutoff); photoperiod & vernalization triggers; perennial dormancy/chill/budbreak; expected + p10/p90 paths using environment distributions.
- [x] Tests with synthetic climates (hand-computed GDD sums still open; GDD itself is tested in test_environment).

**6.2 Window finder**
- [x] (v0.13.0 direct sowing; v0.15.0 indoor start + set-out; protected growing and hardening-off steps open) `engine/windows.py`: daily candidate starts over 18 months × methods; success-probability factors; quality score; viable windows at risk tolerance; best sub-window; protected-growing rerun with structure modifiers.
- [x] "Can I grow X here?" verdict + blockers; API `GET /api/v1/crops/{slug}/windows` (varieties later) and crop-page section.
- [ ] Performance benchmark: 50 varieties ≤ 2 s on CI runner (scaled target for Pi documented).

**6.3 Plantings**
- [x] (v0.16.0; actual stage dates, successions link and per-bed placement open) `planting` table + API (CRUD, status transitions).
- [x] (v0.16.0; list per bed and timeline open) UI: add planting from a window ("Plant this"), plantings list on the Garden page.

**6.4 Task engine core**
- [x] (v0.17.0; user-locked dates have no UI yet, and the change log has no UI) `task`, `task_change` tables; generator interface (`generate(household, horizon) -> [TaskSpec]`) keyed by `generator_key` for idempotent regeneration; user-locked handling; change log with reasons.
- [x] (v0.17.0: sow, set out, first harvest; harden-off steps, successions and ripeness cues open) Crop schedule generator (sow indoors, harden-off steps, transplant, direct sow, successions, harvest window with ripeness cues).
- [~] (v0.18.0: protect from forecast frost and heat; thin, stake, mulch, prune/pinch open) Crop care generator (thin, stake, mulch, prune/pinch, protect from forecast lethal/stress events).
- [~] Recompute job: on planting edits and every 12 h (v0.17.0); on forecast/observation open; AC-P6 test open.

**6.5 Water** §6.6
- [~] (v0.19.0: per-planting FAO-56 balance with one standard soil, Water jobs in mm and litres per m², reset by "Watered"; per-bed, best time of day, sensor override, water budget open; v0.20.0: soil class from the setup Soil question) Soil-water balance (FAO-56 simplified), soil water-holding capacity from texture, root depth by stage; irrigation tasks with litres and best time of day; sensor override; water budget tracking vs household budget.

**6.6 Feeding** §6.5.1
- [ ] Inputs inventory minimal (product, N-P-K, form) so feed tasks can name what to use.
- [ ] Nutrient demand per stage → feed tasks with dose per plant/m² from N-P-K; fallback suggestion when no input; cautions.

**6.7 Scouting** §11.3
- [ ] Organism risk evaluation per planting × stage × weather; weekly "what to look for" tasks with photos and keep/remove verdicts; sightings API; local timing calibration.
- [ ] "Weed or seedling?" comparison for recent sowings.

**Acceptance**: for a synthetic Mediterranean and a synthetic frosty climate, the same tomato and lettuce varieties get different, sensible windows without configuration (AC-P2/P3); all tasks have reason traces (AC-P4).

## Phase 6.9 — Design system (v0.9.0) §15 "Professional quality"
- [x] `docs/DESIGN.md`: brand basics, colour tokens (light/dark, contrast-checked), type scale, spacing/radius/elevation, iconography (lucide sizes/strokes), motion, voice & tone for copy.
- [x] Component kit in `frontend/src/components/ui/`: Button, IconButton, PageHeader, Section, Field, Radio cards, Switch, Badge, Empty state, Skeleton, Error state; ad-hoc classes replaced in all pages (v0.9.0).
- [ ] Sheet/Dialog, Tabs, Toast, Select: add with the first screen that needs them (Phase 7 task card, Phase 8 setup).
- [x] Desktop layout (side nav ≥ 1024 px) alongside the mobile bottom nav.
- [x] Playwright screenshots of every page in light/dark × phone/desktop: `npm run screenshots` (v0.9.0), reviewed before each release.
- [x] Run it in CI against the stubbed server (`tests/e2e_server.py`) and upload the images as artifacts.
- [x] Replace placeholder copy (Today, Garden) with designed empty states.

## Phase 7 — Today screen & calendar §11.2, §9.2
- [~] (v0.17.0: grouped jobs and next 14 days; weather advice, load vs time open) `GET /api/v1/today`: grouped actions (Protect, Plant, Water, Feed, Harvest, Animals, Check, Maintain), weather header with plain-language advice, load vs available time, next-7-days strip.
- [~] (v0.17.0: why-now, Done, Skip; v0.21.0: how-to steps from catalog task templates) Task card component: how-to steps, why-now, minutes, Done (with quantity/photo), Skip, Snooze, Not possible today; optimistic UI.
- [ ] Load balancing: overflow low-priority tasks to the next suitable day.
- [ ] Offline: cache today/week + how-tos; queued completions with idempotency keys; sync banner.
- [ ] Calendar views: week agenda, month, year wheel, per-subject timeline.
- [ ] iCalendar feeds (household/member/category tokens).
- [ ] Notifications v1: daily digest + urgent alerts via ntfy / Gotify / HA webhook / Discord / Web Push (Bloomery pattern).
- [ ] E2E: Today shows tasks for a seeded household; completing a harvest logs quantity; offline completion syncs.

**Acceptance**: AC-P7 (with a manually created plan until Phase 8); hallway test with a non-technical household member (the user's wife): can she tell in 10 seconds what to do today and how? Feedback goes into this plan.

## Phase 8 — Guided setup, layout editor, plan generator §3.1–3.2, §7.1, §9.1
**8.1 Setup interview**
- [ ] Question graph (`backend/app/interview.yaml`): topics (§3.1 table), questions, input types, conditions, "why we ask", mapping to profile fields.
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

## Phase 9 — Animals §8
**9.1 Catalog & records**
- [ ] Species/breed YAML for chicken, duck, goose, turkey, quail, goat, sheep, cattle, pig, rabbit, honeybee (profiles, housing space, water & feed models, lifecycle, production, care templates), sourced. Breeds from FAO DAD-IS (CC BY 4.0, structured fields only) matched to Wikidata by name+species+country. No bundled withdrawal periods: user enters label days, app computes the safe date.
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

## Phase 10 — Harvest, pantry, seeds, inputs §10
- [ ] Harvest log with yields vs expected; feeds yield estimates for the plan generator.
- [ ] Pantry & preservation inventory with batches, methods, best-before defaults, expiry tasks.
- [ ] Seed vault: lots, germination tests, viability by species longevity, reorder reminders from planned sowings.
- [ ] Inputs inventory full (fertiliser, feed, medication, bedding) with usage linked to tasks.
- [ ] Journal with photos and tags.

## Phase 11 — Climate explorer & insights §11.4–11.5
- [x] Chart palette validated for light and dark (tokens `chart-warm`, `chart-cool`); chart rules in WIKI. Still to add to `docs/DESIGN.md`.
- [x] Charts v1 (v0.11.0): temperature bands (day/night), soil, rain per month, daylight, freezing-night chance (only where it occurs); today marker; hover, touch and keyboard readout; table view.
- [ ] Charts v2: ET0, threshold probability curves (user-picked), trend, this-season overlay (forecast and recent weather over the bands), sensor overlay; generated takeaway sentence; attribution line under the charts.
- [ ] "What matters here, now" ranking (probability × impact × soonness) from the household's crops/animals; reference basket before any plantings.
- [ ] Dashboards: yields, production, water use, task completion; season comparison.

## Phase 12 — Home Assistant §12.1
- [ ] MQTT discovery publisher (tasks, alerts, bed water deficit, THI, laying forecast) and subscriber for configured sensors.
- [ ] HACS custom integration (config flow, calendar + todo entities, services: complete task, log harvest, log observation), Platinum-quality patterns from Bloomery.
- [ ] Irrigation request events per bed/zone (litres/minutes) for HA automations.

## Phase 13 — AI co-pilot §12.4
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
