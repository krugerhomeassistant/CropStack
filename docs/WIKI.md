# WIKI — CropStack

> The full target behaviour is specified in [`SPEC.md`](SPEC.md). This wiki documents what is **built today**; where they differ, SPEC is the goal and this page is the current state.

## Purpose
Self-hosted, Docker-based garden and homestead planner. It turns a location (coordinates or postal code) into local climate facts (hardiness zone, frost dates, soil temperature, daylight) and combines them with plant data to produce a rolling task calendar, from indoor sowing to harvest. Local-first: one SQLite file, optional integrations (weather, Home Assistant, AI) are opt-in.

## Users & principles
- **Core rule (SPEC §2)**: no climate presets, modes or location rules. Every recommendation = a subject's requirement profile (crop variety, animal breed, task) × the site's environment data (distributions, observations, forecasts). The v0.3/v0.4 climate card still contains fixed heuristics (`HOT_C`, the 50 % frost-headline rule, rainfall-regime labels); they are scheduled for removal in PLAN Phase 4 (SPEC §18).
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

## Climate engine (`backend/app/climate.py`, v0.3.0)
- **Data**: Open-Meteo archive, `models=era5_seamless` (ERA5-Land ~11 km, ERA5 ~25 km where Land has no data), daily `temperature_2m_min`, `temperature_2m_max`, `soil_temperature_0_to_7cm_mean`, last 30 complete years, `timezone=auto`. One request ≈ 800 of the 10,000 free daily calls → fetched once per garden location and stored condensed in `climatecache`.
- **Season-year**: starts on the climatologically warmest day (31-day smoothed mean daily minimum), so each season holds one whole cold period in either hemisphere. Partial seasons (<360 days) at the ends are dropped (→ 29 seasons).
- **Frost day**: daily minimum air temperature at 2 m ≤ 0 °C.
- **Frost dates at risk p**: per season, first frost (autumn) and last frost (spring) offsets; seasons without frost count as ±∞. With k = floor(p·n): spring date = the value with k seasons later than it; autumn date = the value with k seasons earlier. `None` (shown as "Rare") when frost is rarer than the risk. Frost-free season = autumn − spring + 365 (autumn is in the next season); 365 when either is `None`.
- **Hardiness zone**: mean of each season's minimum → °F → USDA scale (zone 1a from −60 °F, 5 °F half-zones, clamped 1a–13b). Applied worldwide as a comparable number; gridded data underestimates cold in valleys.
- **Daylight**: astronomical day length on the 15th of each month (sun centre −0.833°, includes refraction).
- **Rain**: `precipitation_sum` → average mm per calendar month (`monthly_totals`: total ÷ number of years with that month). **Rainfall regime**: share of annual rain in the 6 coldest months (by mean daily minimum, so hemisphere-independent): ≥ 60 % winter, ≤ 40 % summer, else year-round; 0 mm = dry.
- **Hot days**: days with maximum ≥ 30 °C (`HOT_C`), average per month and per year. Most cool-season crops bolt or stall and fruit set suffers above this.
- **Frost relevance**: the app headlines frost dates only when frost occurs in ≥ 50 % of seasons; otherwise one line ("No frost" / "Frost is rare (x % of years)"). Rationale: in Mediterranean climates (Western Cape) the limits are summer heat and drought and the winter-rain season, not frost.
- **Cache versioning**: `summary.version` = `climate.SUMMARY_VERSION` (now 2). A cache with another version is refetched once.
- **Report** (`GET /api/garden/climate`): computed on every request from the cache + the garden's current `frost_probability`, so changing risk needs no refetch; moving the garden refetches. Errors from Open-Meteo → 502 with the service's reason.

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
- **App shell** (`App.tsx`): loading → `auth` (no session) → `setup` (no garden) → `home`; any network failure shows a retry screen.
- **Home**: garden card + `ClimateCard` (loads `/api/garden/climate`; reloads when location or frost risk changes; error card with retry).
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

## Release process
`python scripts/bump.py X.Y.Z` → commit → push to `main`. CI publishes `ghcr.io/krugerhomeassistant/cropstack:X.Y.Z` and creates the GitHub release from `CHANGELOG.md`.
