# WIKI — CropStack

How CropStack works **today** (v0.11). The target product is specified in [`SPEC.md`](SPEC.md) and scheduled in [`PLAN.md`](PLAN.md); where this page and SPEC differ, SPEC is the goal and this page is the current state. Structure and modules: [`ARCHITECTURE.md`](ARCHITECTURE.md). Visual system: [`DESIGN.md`](DESIGN.md).

## Purpose
A self-hosted garden and homestead planner that tells a household what to do today (plant, water, feed, harvest, check, care for animals) and how. It decides from two things only: what each crop, animal or task needs (its **requirement profile**) and what the site's environment does (30 years of daily weather, this season's weather, the forecast, later the household's own sensors and observations). One container, one SQLite file, nothing sent anywhere the household hasn't been shown.

## Principles
- **No presets (SPEC §2, P1).** No climate types, modes, hemispheres, regions or global "hot/cold" constants. Every recommendation = requirement profile × environment data. Enforced by `backend/tests/test_no_presets.py`, which fails on code that branches on hemisphere, latitude sign, country, climate type or fixed thresholds. If the climate changes, the advice changes by itself.
- **Action first (P9).** The home screen is *Today*. Analysis (the climate page, later the explorer) lives on its own page.
- **Explainable.** Every number on screen can be traced to its data; catalog values carry a source and evidence level.
- **Visible privacy (P7).** Settings lists every outside service, what it sends and when; owners can switch off the optional ones.
- **Professional quality (SPEC §15).** Every changed screen is checked in light and dark, phone and desktop, before a release (`npm run screenshots`).

## Glossary
| Term | Meaning |
|---|---|
| Household | The people who share one garden. Every account belongs to exactly one. |
| Role | `owner` (everything, incl. location and people), `member` (daily work), `viewer` (read only) |
| Site | The household's garden location (coordinates, optional postal code, name, frost-risk preference). One per household. |
| Requirement profile | What a crop, variety, animal or task needs: temperature ranges, water, daylight, humidity, timing |
| Analog years | The engine's model of the future: each year on record is one possible version of the coming year, weighted by recency |
| Window probability | Share of (weighted) years in which a condition holds on a day or across a window, e.g. "soil ≥ 10 °C" |
| Frost risk (`frost_probability`) | The household's tolerance: Cautious 10 %, Typical 50 %, Bold 90 %. Used to place frost dates when frost occurs at all. |
| Hardiness zone | USDA scale from the average yearly minimum; shown as a comparable number, never used to switch behaviour |
| GDD | Growing degree days: heat accumulated above a crop's base temperature, used for development timing |
| Water deficit | Evaporation (ET₀) minus rain over a period; the basis for watering advice |
| Catalog | The data on crops, varieties, organisms, animals and tasks (`catalog/`, CC BY-SA 4.0) |
| Private pack | Extra catalog data on the owner's server only (`<data>/catalog-private/`), never committed |
| Evidence level | How strong a catalog value is: peer-reviewed, government, extension service, model, grower-reported, traditional |

## Screens and navigation
- **Phone** (< 1024 px): bottom bar with Today, Garden, More. More holds Crops, Climate, Household, Settings, Log out and the version.
- **Desktop** (≥ 1024 px): left rail with Today, Garden, Crops, Climate, Household, Settings, Log out and the version.
- `/` and unknown paths open each person's start screen (Settings → Open the app on).
- **Today**: greeting with the date and garden; weather (today, next 7 days, last 30 days against normal); the daily jobs section (placeholder until the crop engine, PLAN 6–7). Desktop shows jobs and weather side by side.
- **Garden**: garden name and location (owners can edit); beds section (placeholder until the layout editor, PLAN 8).
- **Crops**: the catalog, searchable by English or Afrikaans name, scientific name or family. A crop page says in plain words when it germinates (soil temperature, days to emergence), how it uses water (crop coefficient as a share of a lawn's use, root depth, when to water), its size and spacing, and FAO-56 growth-stage lengths from field trials; each value has a numbered source listed at the end, and grower-reported values are marked as rough guides. **Where the crop data comes from** (`/crop-data`) lists every source with its licence, grouped by how it may be used.
- **Climate**: the description card, then charts (v0.11): temperature through the year (p50 line of the daily high and low with the p10–p90 band), rain per month (columns), soil temperature (same style), day length (twelve mid-month values joined linearly) and, only when any day has more than a 1 % chance of a night at or below 0 °C, the chance of a freezing night per day (0–100 %). Today is marked. Values come from `climate/bands` and `climate/probability`, converted to the person's units. Hover, touch or arrow keys (PageUp/PageDown jump 30 days) read a day; each chart has a table view. Charts are dependency-free SVG sized to their container (`components/charts.tsx`), series colours are the validated `chart-warm` and `chart-cool` tokens (the dark values differ from the text tokens because dark charts need their own lightness band).
- **Household**: name, people and roles, invites (owners).
- **Settings**: start screen, units (per person), data sources (switches for owners).
- **App start** (`App.tsx`): loading → sign in / sign up (or invite) → garden setup (owner, no site yet) or "waiting for the owner" (member) → app. A failed load shows a retry screen.
- **Stale app after an update**: if a request fails, the app checks `/api/health`; when the server version differs from the build it reloads once per version. Any change that breaks old clients (API paths, response shapes) needs a version bump.

## Accounts and households
- **Sign up**: without an invite, a new household ("<name>'s homestead") is created with you as owner. `CROPSTACK_ALLOW_REGISTRATION`: `auto` (default, open until the first account exists), `true`, `false`. Invite links work even when sign-up is closed.
- **Invites**: owner → Household → Invite someone → role → link `/invite/<token>`; single use, 7 days, only a SHA-256 hash is stored. Removing a person deletes their login. A household always keeps at least one owner.
- **Log in**: usernames lowercased; argon2id passwords (min 8); 10 failures per 15 min per IP; signed session cookie `cropstack_session`, 30 days.
- **Personal settings**: `PUT /api/v1/auth/prefs` `{start: today|garden|climate, units: metric|imperial}`. Values are stored in SI units and converted for display (`frontend/src/units.ts`).

## Garden setup
Name; place search (town, address or postal code via Nominatim, on submit only, ≤ 1 request per second); "Use my current location" (browsers allow this only over HTTPS or localhost, so on a LAN `http://` install enter coordinates by hand); latitude and longitude; optional postal code; frost risk. `PUT /api/v1/sites/current` creates or updates the household's site (owners only).

## Climate
- **Data**: Open-Meteo archive, `models=era5_seamless` (ERA5-Land ~11 km, ERA5 ~25 km where Land has no data), the last 30 complete years, `timezone=auto`, 7 daily variables: min/max air temperature, soil temperature 0–7 cm, precipitation, ET₀, mean relative humidity, max wind. Stored raw per site (`climatearchive`).
- **Refresh** (on access): when the site moves, a newer complete year exists, or the archive format version changes. If a refresh fails and the site hasn't moved, the stored record is used.
- **Contributing data**: anyone can add or correct catalog values by pull request or issue form (docs/CONTRIBUTING-CATALOG.md). `docs/COVERAGE.md` lists what is still missing; a monthly workflow re-runs the importers and opens a reviewable PR; crop pages link to the correction form.
- **Jobs and Today**: the task engine turns each planting into jobs (sow; set out for transplants; start harvesting) with a reason, a window (3 days early to 7 days late) and an ideal day. Harvest dates come from the sowing-to-harvest estimate for that start day in your climate, or the catalogued cycle length when there is no climate record yet. Regeneration is keyed (`planting:<id>:<job>`), so a changed planting moves its open jobs and logs why; done and skipped jobs stay as they are. Finishing a job moves its planting forward, never back. Today lists jobs whose window has opened, grouped Protect, Plant, Water, Feed, Harvest, Animals, Check, Maintain (only the groups that have jobs), and the next 14 days under Coming up.
- **Protect jobs**: for a planting that is outdoors (sown direct, or a transplant that has been set out), the first day in the next 7 whose forecast low is at or below the crop's `lethal_min` gets a frost job, and the first whose high is at or above `stress_max` gets a heat job. One job per planting and kind, so the job moves with the forecast; if the risk clears the engine skips it, and it reopens if the risk returns, but a job a person skipped stays skipped. Recomputed whenever Today is opened and every 12 hours.
- **Watering** (`engine/water.py`): FAO-56 in simplified form. Each day the crop uses Kc × ET0 (Kc rises from `kc_initial` to `kc_mid` through the development stage and falls to `kc_late` at the end; stage lengths are the median of the catalog's regions, or a 15/25/40/20 % split of the cycle); 80 % of rain is counted; roots grow in a straight line from 0.2 m to the middle of the catalog's root-depth range over the first two stages; total available water = the soil's water-holding capacity × root depth (sandy 90, silty or loamy 170, clay 120 mm per metre from FAO-56 Example 36 / Table 19; 120 when the household has not said; set by the Soil question in garden setup), and the crop is stressed after using the catalog's depletion fraction of it. The soil counts as full at sowing, at set-out, or when someone last marked a Water job done. A Water job appears when the dry point falls within the next 3 days, naming the millimetres to give (1 mm = 1 litre per square metre). The job's key includes the last-watered date, so each watering starts a fresh job.
- **How-to steps**: each job kind (sow, set out, harvest, water, frost, heat) has a catalog task template (`catalog/task-templates/how-to-*.yaml`, kind `task_template`, with `task_kind` and `steps`) written in plain words; Today shows the steps under a "How to do it" fold on each job. Crop-specific steps are not there yet.
- **Update not showing?** An installed app caches its screens. From v0.26.1 it refreshes itself when the server is newer. If an older copy still shows old screens, close it fully and reopen it, or clear the site data for the address in the browser settings.
- **Beds**: a rectangle (or round container) on the garden plan, in metres. A planting can sit in one bed; a bed is "too full" when the live plantings' footprints (crop spread × row spacing, from the catalog) add up to more than its area. Crops with no catalogued spread are not counted.
- **Plantings**: a record of what the household has planted or plans to (crop, method, dates, quantity, place, status). Status only moves forward (planned → sown → up → set out → harvesting → finished) or to failed; only transplants are "set out"; a mistaken entry is deleted. **Check** jobs come weekly for every planting in the ground and list the catalogued pests, diseases and helpers with keep/remove advice (filtered by the organism's `hosts`; empty means any crop). **Harvests** are logged against a planting (quantity, unit, date) once it is up; the Garden page totals them per planting. Owners and members edit; viewers read.
- **Sowing windows** (`engine/`): for each possible sowing day and each year on record, the crop succeeds if seeds germinate, it reaches its heat-sum target (base = lowest growing temperature; target = longest-cycle days × (20 − base) °C, Recocrop style) within twice its longest cycle, and meets no killing frost or 5 days of heat above its limit. The share of years that succeed is the day's score; days at or above a threshold set by the household's frost-risk setting (0.9 / 0.8 / 0.6) form windows. Transplants (v0.15.0): a seedling raised indoors for `transplant_age_days` skips germination, is credited a head start of up to 35 % of the heat-sum target, and is exposed to frost and heat from the set-out day; the window is given as set-out dates. Protected growing is not modelled yet.
- **Engine** (`environment.py`): analog years with 365-day years (29 Feb dropped); recency weights `0.5^((last − year) / 10)`; significant temperature trends removed by shifting past years to today's level; weighted quantiles by inverse CDF; window probabilities that wrap across the year end; GDD and days-to-GDD; water deficit. Built climatologies are cached in memory per site.
- **Description card** (`climate.py`): describes, never classifies. Rain per year and the 6-month stretch that gets most of it; hottest day and coldest night of a typical year; frost dates when frost occurs at the household's risk level, otherwise how often frost happens at all; significant trend per decade; daylight range; elevation; monthly highs, lows, soil temperature, rain and frost nights. 0 °C appears only as a description; crop decisions will use each crop's own limits.
- **Frost dates at risk p**: seasons are anchored at the warmest day so each holds one whole cold period anywhere on Earth; with k = floor(p·n), the spring date is the value with k seasons later, the autumn date the value with k seasons earlier; frost-free seasons count as ±∞.
- **Endpoints**: `GET /api/v1/sites/current/climate` (card), `…/climate/probability?var&op&x` (365 daily chances, e.g. `tmin le 0`), `…/climate/bands?var` (10th/50th/90th percentile per day and trend per decade). `var` ∈ tmin, tmax, soil_t, precip, et0, rh, wind.

## Weather
- **Forecast**: Open-Meteo forecast, `past_days=92`, `forecast_days=16`, the archive's 7 variables plus rain probability and weather code. Stored per site (`forecast`); refreshed when older than 3 hours on request and by the background job every 30 minutes; a failed refresh keeps the old copy and marks it `stale`. "Today" is the site's local date.
- **Engine**: `environment.with_forecast` writes the forecast into every analog year, so near-term questions use the forecast and later days the climate.
- **Last 30 days vs normal** (`weather.anomaly`): temperature difference against the same days in the site's climate; rain total and its percentile among past years. Wording: "close to normal" between the 30th and 70th percentile, "wetter/drier than n in 10 years" beyond, "almost every year on record" beyond 95/5.
- **Icons**: WMO weather codes map to an icon and label for display only.
- `GET /api/v1/sites/current/weather` answers 409 when the household switched the forecast off; Today then hides the weather.

## Background jobs
`app/scheduler.py`: `@job(name, every)` registry, one asyncio worker ticking every 60 s, first run 60 s after start. Failures are recorded and never stop the app. `/api/health` → `jobs` shows each job's last run, success and error. `CROPSTACK_SCHEDULER=false` turns jobs off (tests).

## Data sources
`GET /api/v1/household/data-sources` lists each outside service with what it sends, when, its licence and whether it can be switched off. Owners change the switches with `PUT /api/v1/household/settings` (`forecast`, `place_search`). A switched-off source is never called: its endpoints answer 409 and the screens hide the feature.

## Catalog
- **Format**: Pydantic models in `backend/app/catalog.py`; JSON Schemas generated into `catalog/schema/` (`python scripts/catalog_schema.py`; CI checks they are current). Kinds: crops, varieties, organisms, species, breeds, task templates. Every value is a fact with provenance: `sources`, `evidence`, or `estimate: true`. Varieties and breeds inherit `requirements` and `params` from their parent. Format reference: [`catalog/README.md`](../catalog/README.md).
- **Layers**: bundled `catalog/` → private pack `<data>/catalog-private/` (loaded after bundled, wins field by field; errors are shown to the owner and never stop the app) → household overrides in the database (`catalogoverride`, one row per field path, validated against the schema). Held in memory; `POST /api/v1/catalog/reload` re-reads it.
- **Licence gate** (bundled data, at load and in CI): schema valid, unique slugs, parents exist, every value cites a source in `catalog/sources.yaml` or is marked an estimate, `bundle` sources have an open licence, nothing cites a `link-only` source.
- **Policy** (SPEC §16, §16.1): bundled only CC0, public domain, CC BY, CC BY-SA 4.0. Non-commercial or no-derivatives sources are read to check facts and linked, never copied. Withdrawal periods are never bundled (the user enters the label's days). Research and the source table: [`research/catalog-data-sources.md`](research/catalog-data-sources.md).
- **Content** (v0.10.0): 29 core vegetables in `catalog/crops/`. The curated part (names in English and Afrikaans, accepted scientific name, APG IV family, rotation group, life cycle, a description written for CropStack) is hand-written; the values come from the ingestion pipeline:

  | Field | Source | Evidence |
  |---|---|---|
  | `requirements.soil_temperature.germination` (min/opt/max °C), `params.days_to_emergence` (per soil temperature) | Harrington tables via OSU Extension (°F converted) | extension service |
  | `requirements.water.kc_initial/mid/late`, `params.height_max` | FAO-56 Table 12 via pyfao56 | official guideline |
  | `requirements.water.root_depth` (m), `depletion_fraction` | FAO-56 Table 22 via pyfao56 | official guideline |
  | `params.stage_days_initial/development/mid/late` (per trial region and planting month) | FAO-56 Table 11 via pyfao56 | official guideline |
  | `requirements.temperature.stress_min` / `optimal` (min, max) / `stress_max` (°C), `requirements.soil.ph` (min, opt_min, opt_max, max), `params.cycle_days` (min, max), `params.annual_rainfall` (mm per year; a range to compare with, not a rule) | FAO ECOCROP via the Recocrop R package (CC BY 4.0 + FAO terms) | official guideline |
  | `params.row_spacing`, `plant_spread`, `height` (cm), `sun` | OpenFarm rescue (CC0) | grower-reported, low confidence |
- **Ingestion** (`scripts/ingest/`, maintainers only; self-hosted servers never fetch): `fetch` downloads each source politely (identifying User-Agent without personal data, robots.txt, ≥ 2 s per host) into `.ingest-cache/<sha256>` (git-ignored) and records URL, hash and date in `scripts/ingest/snapshots.lock`; `merge` runs pure extractors on the locked snapshots and writes proposals into the crop files where the field is empty or was written by the same source before; anything else is hand-curated and never overwritten; `check` compares scientific names and families with the GBIF Backbone (pea is a documented exception: GBIF follows *Lathyrus oleraceus*, gardeners say *Pisum sativum*). `crosswalk.yaml` maps each crop to each source's row name or code (ECOCROP by `CODE`, so name changes such as *Lycopersicon* → *Solanum* cannot mismatch). ECOCROP: the table ships inside the Recocrop package (`inst/parameters/ecocrop.rds`), read with pyreadr and pandas (maintainers: `pip install pyreadr pandas`); ranges that are unknown (0 or blank) or out of order are skipped; KTMP (killing temperature) is not imported because 0 is ambiguous. A range value (`Range`) has `min`, `opt_min`, `opt`, `opt_max`, `max`, in that order. Review `git diff catalog/` like any change.

## Design system
Tokens in `frontend/src/index.css`, components in `frontend/src/components/ui/` (`Button`, `IconButton`, `PageHeader`, `Section`, `Field`, `RadioCards`, `Switch`, `Badge`, `ErrorMessage`, `ErrorState`, `EmptyState`, `Skeleton`). Pages use these rather than ad-hoc classes. Rules and the reasons behind them: [`DESIGN.md`](DESIGN.md).

## Data, backups and migrations
- `data/cropstack.db` (SQLite, WAL) and `data/secret.key` (generated, mode 600); the private catalog pack lives in `data/catalog-private/`. Back up the whole `data/` folder.
- Alembic migrations in `backend/app/migrations/versions/` run on every start. Every model change needs a revision (`alembic revision --autogenerate -m "…"`, then review it); CI fails when models and migrations differ.
- Migrations run with SQLite foreign keys off: batch mode rebuilds tables, and a cascade on drop would delete child rows. Upgrades from older versions are tested with stored fixtures.

## Routing
`/api/v1/*` is the API (everything except `/api/health`); unknown API paths return JSON 404. Every other path serves a built file if one exists, otherwise `index.html` for client-side routing.

## Release process
`python scripts/bump.py X.Y.Z` → update `CHANGELOG.md` → commit → push to `main`. CI tags the release, publishes `ghcr.io/krugerhomeassistant/cropstack:X.Y.Z` and `latest` (amd64, arm64) and creates the GitHub release from the changelog. README and this wiki are reviewed on every release.
