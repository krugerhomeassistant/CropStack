# WIKI — CropStack

> The full target behaviour is specified in [`SPEC.md`](SPEC.md). This wiki documents what is **built today**; where they differ, SPEC is the goal and this page is the current state.

## Purpose
Self-hosted, Docker-based garden and homestead planner. It turns a location (coordinates or postal code) into local climate facts (hardiness zone, frost dates, soil temperature, daylight) and combines them with plant data to produce a rolling task calendar, from indoor sowing to harvest. Local-first: one SQLite file, optional integrations (weather, Home Assistant, AI) are opt-in.

## Users & principles
- **Core rule (SPEC §2)**: no climate presets, modes or location rules. Every recommendation = a subject's requirement profile (crop variety, animal breed, task) × the site's environment data (distributions, observations, forecasts). Enforced by `tests/test_no_presets.py` (fails on code that branches on hemisphere, latitude sign, country, climate types or global hot/cold constants).
- **Action first (SPEC P9)**: the home screen will be *Today* (what to plant, water, feed, harvest, check); analysis such as the climate explorer lives on its own page.
- Home gardeners and homesteaders running their own server (NAS, Pi, home lab).
- Works offline in the field (PWA); nothing leaves the server unless an integration is enabled.
- Plans are explainable: every task shows the rule and dates it came from.

## Glossary
| Term | Meaning |
|---|---|
| Hardiness zone | USDA zone (1a–13b) from average annual extreme minimum temperature |
| Last spring frost (LSF) | Date after which frost risk drops below the chosen probability; anchor for spring tasks |
| First fall frost (FFF) | Date the fall frost risk rises above the chosen probability; end of the outdoor season for tender crops |
| Growing season | Days between LSF and FFF |
| Days to maturity (DTM) | Seed or transplant to first harvest, per variety |
| Hardening off | Gradual outdoor exposure of indoor seedlings before transplanting |
| Succession interval | Days between repeated sowings of the same crop for a continuous harvest |
| Companion matrix | Beneficial / antagonistic pairings between plants |
| Crop family | Botanical family used for rotation (e.g. Solanaceae, Brassicaceae) |
| Rotation conflict | Same crop family in the same bed within the configured number of seasons |
| Plot / bed | Physical growing area on the garden map (raised bed, row, container, guild) |
| Frost probability | Chance that frost still occurs after the computed spring date (or before the fall date). Lower = safer, later planting |
| Task | A dated action generated from plant timing + climate (sow, transplant, harden off, feed, prune, harvest) |

## Climate (v0.6.0)
- **Data**: Open-Meteo archive, `models=era5_seamless` (ERA5-Land ~11 km, ERA5 ~25 km where Land has no data), last 30 complete years, `timezone=auto`, daily `temperature_2m_min/max`, `soil_temperature_0_to_7cm_mean`, `precipitation_sum`, `et0_fao_evapotranspiration`, `relative_humidity_2m_mean`, `wind_speed_10m_max`. One request ≈ 800 of the 10,000 free daily calls. Stored raw per site in `climatearchive`.
- **Refresh** (on access, no scheduler): site moved, a newer complete year exists, or `ARCHIVE_VERSION` changed. If the refresh fails and the site hasn't moved, the existing record is used.
- **Engine** (`environment.py`, SPEC §4.2): analog years: each of the ~30 years is a possible future; answers = weighted share of years. 365-day years (29 Feb dropped); recency weights (half-life 10 y); significant temperature trends removed by shifting past years to today's level. Weighted quantile = inverse CDF, averaging only on exact boundaries. Built climatologies are cached in-process per site and fetch time.
- **Endpoints**: `GET sites/current/climate` (card), `…/climate/probability?var&op&x` (365 daily chances, e.g. `tmin le 0`), `…/climate/bands?var` (q10/q50/q90 per day + trend per decade). `var` ∈ tmin, tmax, soil_t, precip, et0, rh, wind.
- **Card** (`climate.py` + `ClimateCard.tsx`): describes, never classifies: rain per year and the 6-month stretch that gets most of it, hottest day and coldest night of a typical year, frost dates whenever frost occurs at the person's risk level (otherwise how often frost happens), significant trend per decade, daylight, elevation, monthly highs/lows/soil/rain/frost nights. Frost = 0 °C used only as a description; crop decisions will use each crop's own lethal temperature.
- **Frost dates at risk p** (season-year anchored at the warmest day, so each season holds one whole cold period anywhere): with k = floor(p·n), spring date = the value with k seasons later; autumn date = the value with k seasons earlier; seasons without frost count as ±∞.
- **Hardiness zone**: mean of each season's minimum → °F → USDA scale (1a from −60 °F, 5 °F half-zones); a comparable number worldwide.
- **Daylight**: astronomical day length on the 15th of each month (−0.833° incl. refraction).

## Weather (v0.8.0)
- **Forecast**: Open-Meteo forecast API, `past_days=92`, `forecast_days=16`, `timezone=auto`, 9 daily variables (the archive's seven + `precipitation_probability_max`, `weather_code`). Stored per site in `forecast`; refreshed on request when older than 3 h and by the background job every 30 min; a failed refresh keeps the old copy (`stale: true`). "Today" is the site's local date (`utc_offset_seconds`).
- **Engine**: `environment.with_forecast` writes the forecast into every analog year, so near-term questions use the forecast and later days the climate.
- **Last 30 days vs normal** (`weather.anomaly`): mean temperature difference against the same 30 days in the site's climate, rain total and its percentile among past years; wording: "close to normal" between the 30th and 70th percentile, "wetter/drier than n in 10 years" beyond, "almost every year on record" beyond 95/5.
- **Weather icons**: WMO weather codes mapped to icons/labels for display only.
- **Background jobs** (`app/scheduler.py`): `@job(name, every)`; ticks every 60 s; first run 60 s after start; failures recorded, never fatal; `/api/health` → `jobs`. Disabled with `CROPSTACK_SCHEDULER=false`.
- **Data sources** (Settings): lists climate (required), forecast and place search with what is sent and when; owners switch forecast and place search off (`PUT /api/v1/household/settings`); turned-off sources are never called (endpoints answer 409, Today hides the weather card, setup hides place search).

## Place search
`GET /api/places?q=` → Nominatim `/search` (free text: town, address or postal code; postcodes work in South Africa where Open-Meteo's geocoder found none). Search on submit only (Nominatim policy ≤ 1 req/s, identifying User-Agent `CropStack/<version> (+repo URL)`).

## Planned scheduling rules (to be confirmed during implementation)
**Principle (user feedback 2026-10-09):** the calendar must not be frost-centric. Each crop gets temperature windows (germination soil temperature, ideal / max air temperature, heat and frost tolerance); sowing and transplant windows are the months whose climate normals fit, with frost dates as an extra constraint only where frost matters, and rain season as a watering signal. In a winter-rainfall climate this naturally gives autumn/winter sowing of cool-season crops and spring planting of warm-season crops before the heat.
- Indoor sowing = LSF − (variety weeks before LSF).
- Hardening off starts 7–10 days before transplant.
- Transplant / direct sow = LSF + variety offset, gated on minimum soil temperature when known.
- Harvest window = sow or transplant date + DTM (± variety spread).
- Last viable sowing = FFF − DTM − buffer (fall planting).
- Weather overrides shift or flag tasks (frost alert → protect or delay tender transplants; heat → extra watering; heavy rain → skip watering).

## Workflows
- **Households**: every account belongs to exactly one household with a role: `owner` (everything, incl. garden location and people), `member` (daily work), `viewer` (read-only). Signing up without an invite creates a new household ("<name>'s homestead") with you as owner. The garden (`site`) belongs to the household, so everyone in it sees the same garden.
- **Invites**: owner → Household → Invite someone → role → link `/invite/<token>` (single use, 7 days; only a SHA-256 hash is stored). Opening it signed-out shows "You're invited to join …" and a sign-up form that works even when public sign-up is closed. Removing a person deletes their login. A household always keeps at least one owner.
- **Sign up / log in**: `GET /api/auth/status` tells the app whether to show sign-up. Registration modes (`CROPSTACK_ALLOW_REGISTRATION`): `auto` (default) = open until the first account exists, `true`, `false`. Usernames are stored lowercased. Passwords: argon2id, min 8 chars. Login failures are throttled per client IP (10 per 15 min, in memory). Session = signed cookie `cropstack_session`, 30 days.
- **Garden setup**: after login, if `GET /api/garden` is 404 the app shows setup: name, place search (fills coordinates and postal code), latitude/longitude (browser geolocation works only over HTTPS or localhost; on a LAN `http://` install enter coordinates by hand), optional postal code, frost risk (Cautious 10 % · Typical 50 % · Bold 90 %, stored as `frost_probability`). `PUT /api/garden` creates or updates; one garden per user.
- **Health check**: `GET /api/health` → `{status, version}`; also runs `SELECT 1` against SQLite. Used by the Docker `HEALTHCHECK`.
- **Navigation** (v0.5): bottom tabs Today · Garden · More. More holds Climate, Household, Settings and Log out. `/` opens each person's own start screen (Settings → "Open the app on"). Members don't see edit controls for the garden location.
- **Personal settings**: `PUT /api/v1/auth/prefs` `{start: today|garden|climate, units: metric|imperial}`; returned in `/auth/me` as `prefs` with defaults. Values are stored SI and converted for display (`src/units.ts`).
- **API**: everything under `/api/v1` except `/api/health`.
- **Stale app after an update**: the PWA can run the previous build from its cache for a few seconds after a server update. When a request fails, the app checks `/api/health`; if the server version differs from the build's `__APP_VERSION__` it reloads once per server version (sessionStorage guard), otherwise it shows the real error ("Cannot reach…" only when health is unreachable). Any change that breaks old clients (API paths, response shapes) must come with a version bump.
- **App shell** (`App.tsx`): loading → `auth` (no session) → `setup` (no garden) → `home`; any network failure shows a retry screen.
- **Climate page** (More → Climate): `ClimateCard` (loads `/api/v1/sites/current/climate`; reloads when location or frost risk changes; error card with retry).
- **Routing**: `/api/*` = API (404 JSON for unknown routes); every other path serves a built file if it exists inside the build dir, else `index.html` (client-side routing; traversal attempts fall back to `index.html`).

## Configuration
See `README.md` → Configuration. All env vars use the `CROPSTACK_` prefix (`backend/app/config.py`).

## Database migrations
- Alembic, scripts in `backend/app/migrations/versions/`. The app upgrades the database to the latest revision on every start (`app/db.py: init_db`).
- Every model change needs a revision: `cd backend && alembic revision --autogenerate -m "what changed"`, then review it. CI fails if models and migrations differ (`tests/test_migrations.py`).
- Migrations run with SQLite foreign keys **off**: batch mode rebuilds tables (copy, drop, rename) and a cascade on drop would delete child rows.
- Baseline `0001` = v0.4.0 schema; older installs are upgraded in place (missing tables created, data kept).

## Data
- `./data/cropstack.db` (SQLite, WAL) and `./data/secret.key` (auto-generated session key, mode 600).
- Back up the whole `data/` folder.

## Catalog data & licensing
- Catalog values (crops, varieties, organisms, species, breeds, task templates) live in `catalog/` under **CC BY-SA 4.0** (`LICENSE`, `NOTICE` with FAO/EPPO terms); the code is MIT. Format: [`catalog/README.md`](../catalog/README.md); models in `backend/app/catalog.py`; JSON Schemas generated into `catalog/schema/` (`python scripts/catalog_schema.py`, CI checks they're current). No crop content yet (Phase 5).
- **Layers** (v0.7.0): bundled `catalog/` → private pack `<data>/catalog-private/` (owner's server only, never committed; any source; loaded after bundled and wins field by field; errors shown to the owner, never stop the app) → household overrides in the DB (`catalogoverride`, one row per field path, validated against the schema). Varieties/breeds inherit `requirements` and `params` from their parent. The catalog is held in memory (read-only, loaded at start; `POST /api/v1/catalog/reload` re-reads it).
- **Gate** (bundled only, at load and in CI): schema valid; unique slugs; parents exist; every value cites a source in `sources.yaml` or says `estimate: true`; `bundle` sources need an open licence; nothing may cite a `link-only` source.
- Every value is a **cited fact** with an **evidence level**: `peer-reviewed`, `government`, `extension-service`, `model` (crop-model calibration), `grower-reported` (e.g. OpenFarm), `traditional` (folk knowledge, e.g. most companion pairs). The UI shows sources per field and a generated *Data sources & licences* page.
- Labels for honest limits: `commercial benchmark` (yields converted from t/ha; 1 t/ha = 0.1 kg/m²), `US-calibrated` (pest degree-day models), `estimate`.
- Bundled only: CC0, public domain, CC BY, CC BY-SA 4.0. Non-commercial or no-derivatives sources (PFAF, Permapeople, PPDB, Feedipedia, CABI, UC IPM text/photos) are read to check facts and linked, never copied.
- Rotation: family groups (APG IV) with a 3-year default, overridden by disease links that cross families (clubroot 7 y, Sclerotinia ≥ 5 y, Verticillium 4–5 y, Fusarium 4–7 y, onion white rot: rotation ineffective).
- Withdrawal periods are never bundled: the user enters the label's days; CropStack computes the safe date.
- Research and source list: [`docs/research/catalog-data-sources.md`](research/catalog-data-sources.md). Policy: SPEC §16.1.

## Release process
`python scripts/bump.py X.Y.Z` → commit → push to `main`. CI publishes `ghcr.io/krugerhomeassistant/cropstack:X.Y.Z` and creates the GitHub release from `CHANGELOG.md`.
