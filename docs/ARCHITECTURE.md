# ARCHITECTURE

## Topology
```
Browser/PWA ──HTTP──▶ cropstack container :8000 (host :8430)
                        ├─ FastAPI  /api/*            (session-cookie auth)
                        ├─ static SPA /*              (Vite build, service worker precache)
                        ├─ SQLite  /data/cropstack.db (WAL, foreign keys on)
                        ├─ scheduler (asyncio, 1 worker) ──▶ forecast refresh every 30 min
                        └─ httpx ──▶ archive-api / api.open-meteo.com (climate, forecast) · nominatim.openstreetmap.org (place search)
```
Single image, multi-stage: `node:24-alpine` builds the SPA → `python:3.14-slim` runtime. `entrypoint.sh` starts as root, chowns `$CROPSTACK_DATA_DIR`, then drops to uid 10001 via `setpriv`. One uvicorn worker, access log off, `--proxy-headers` for reverse proxies.

Target architecture (engines, data model, API) is specified in `docs/SPEC.md` §13–15. Planned optional services: weather API client (httpx), MQTT client for Home Assistant, Ollama (compose profile `ai`) or OpenAI-compatible API for the co-pilot. Postgres is an option only if multi-user scale demands it; SQLite is the default.

## Stack (pinned 2026-10-09)
| Layer | Tech |
|---|---|
| Backend | Python 3.14 (runtime, CI) / 3.13+ (dev), FastAPI 0.143.0, uvicorn 0.54.0, SQLModel 0.0.48, pydantic-settings 2.15.0, PyYAML 6.0.3, alembic 1.20.0, argon2-cffi 25.1.0, itsdangerous 2.2.0, httpx 0.28.1, tzdata 2026.5 |
| Frontend | React 19.3, React Router 8.4 (declarative, `react-router` package), Vite 8.3, TypeScript 7.0, Tailwind 4.3 (`@tailwindcss/vite`), vite-plugin-pwa 2.0, lucide-react 1.53, @fontsource-variable/bricolage-grotesque + atkinson-hyperlegible-next 5.3 (self-hosted fonts); Playwright 1.64 (dev: `npm run screenshots`) |
| Tooling | ruff (lint + format), pytest, GitHub Actions, Dependabot, GHCR |

## Backend modules (`backend/app/`)
| File | Role |
|---|---|
| `__init__.py` | `VERSION` (single source; `scripts/bump.py` keeps frontend in sync) |
| `config.py` | `Settings` (env `CROPSTACK_*`), secret auto-generation |
| `db.py` | engine (WAL + FK pragmas), `init_db` (Alembic `upgrade head`, foreign keys off while migrating), `get_session` dependency |
| `migrations/` | Alembic env + revisions (`0001_baseline` = v0.4.0 schema, creates only missing tables) |
| `catalog.py` | catalog models (value + provenance, requirement profile, item kinds, sources), loader with licence gate, private pack, `effective()`, override checks |
| `routers/catalog.py` | catalog status/reload, list, item (effective + sources), household overrides |
| `models.py` | `User`, `Household`, `Membership` (PK user_id → one household per user), `Invite` (hashed token), `Site` (one per household), `ClimateCache` |
| `deps.py` | `SessionDep`, `UserDep`, `MemberDep`, `OwnerDep`, `EditorDep` (`require_role`), argon2 `hash_pw` / `verify_pw` |
| `routers/household.py` | household name, settings (data-source switches), data-sources list, members (role, remove), invites (create, list, revoke), public invite info |
| `routers/auth.py` | status, register (new household or via invite), login (IP throttle), logout, me (with role + household), password |
| `environment.py` | **pure** environment engine v2: analog-year `Climatology` (build, recency weights, trend), window probabilities, daily curves/bands, GDD, days-to-GDD, water deficit |
| `weather.py` | **pure** forecast rows, past/future split, last-30-days anomaly |
| `scheduler.py` | background job registry + runner (thread per run), status for `/api/health` |
| `routers/weather.py` | forecast refresh (3 h), `forecast` job, `GET /api/v1/sites/current/weather` |
| `climate.py` | **pure** climate card description: season stats, frost dates at a risk, zone, daylight, monthly means, rain season, extremes, `summarize`, `report` |
| `external.py` | Open-Meteo archive fetch (`ARCHIVE_VARIABLES`), Nominatim search, `ExternalError` |
| `routers/garden.py` | site `GET`/`PUT /api/v1/sites/current`, climate archive refresh + in-process climatology cache, `…/climate`, `…/climate/probability`, `…/climate/bands`, `/places` |
| `main.py` | app factory, session + security-header middleware, `/api/health`, SPA fallback |

## Frontend (`frontend/`)
| File | Role |
|---|---|
| `src/main.tsx` | entry, service-worker registration |
| `src/api.ts` | typed fetch client, `ApiError` |
| `src/App.tsx` | bootstrap state (loading → auth/invite → owner setup or member waiting → app) + routes |
| `src/state.tsx` | `AppContext` / `useApp()`: user, garden, setGarden, reload, logout |
| `src/i18n.ts` | `t()` / `N_()` translation layer (English only for now) |
| `src/units.ts` | SI → metric/imperial display helpers |
| `src/components/Layout.tsx` | page frame: bottom nav < 1024 px (`--nav-h` incl. safe area), left rail ≥ 1024 px; content max 960 px |
| `src/components/ui/index.tsx` | UI kit (DESIGN.md): Button, IconButton, PageHeader, Section, Field, RadioCards, Switch, Badge, ErrorMessage, ErrorState, EmptyState, Skeleton |
| `src/pages/` | `Auth` (incl. invite), `GardenSetup`, `Today`, `Garden`, `More`, `Climate`, `Household`, `Settings` |
| `src/components/` | `PlaceSearch` (not a form: nested in the garden form), `ClimateCard`, `WeatherCard`, `DataSources` |
| `src/index.css` | Tailwind `@theme` tokens (canvas, surface, sunken, line, ink, muted, leaf, on-leaf, marigold, water, feed, harvest, check, animals, danger; radii; fonts), dark values via `prefers-color-scheme`, primitives (`card`, `field`, `input`, `btn*`, `switch`, `radio`) |
| `scripts/screenshots.mjs` | every page × light/dark × phone/desktop → `frontend/screenshots/` (git-ignored) |
| `vite.config.ts` | PWA manifest, `/api` dev proxy → :8000 |

## Environment variables (no secrets in repo)
| Key | Default | Notes |
|---|---|---|
| `CROPSTACK_DATA_DIR` | `./data` (`/data` in image) | SQLite + secret key |
| `CROPSTACK_STATIC_DIR` | `./static` (`/app/static` in image) | built SPA; SPA route disabled if missing |
| `CROPSTACK_SECRET_KEY` | auto | session signing |
| `CROPSTACK_ALLOW_REGISTRATION` | `auto` | `auto` / `true` / `false` |
| `CROPSTACK_SECURE_COOKIES` | `false` | HTTPS-only cookies |
| `CROPSTACK_CATALOG_DIR` | repo `catalog/` (`/app/catalog` in image) | bundled catalog; private pack is `<data>/catalog-private/` |
| `CROPSTACK_SCHEDULER` | `true` | background jobs (forecast refresh) |
| `CROPSTACK_PORT` | `8430` | compose host port only |

## DB schema (SQLite, Alembic migrations; head 0006)
- **user**: id, username (unique, lowercased), password_hash (argon2id), display_name, created_at, prefs JSON (start, units)
- **household**: id, name, created_at, settings JSON (forecast, place_search)
- **membership**: user_id (PK → user, CASCADE), household_id (→ household, CASCADE, indexed), role (owner|member|viewer), created_at
- **invite**: token_hash (PK, SHA-256), household_id (→ household, CASCADE), role, created_by (→ user, SET NULL), created_at, expires_at, used_at
- **site**: id, household_id (→ household, unique, CASCADE), name, latitude, longitude, postal_code, frost_probability (10–90), created_at, updated_at
- **forecast**: site_id (PK → site, CASCADE), latitude, longitude, raw JSON (Open-Meteo forecast response), fetched_at
- **catalogoverride**: (household_id → household CASCADE, kind, slug, path) PK, value JSON (a cited `Value`), updated_at
- **climatearchive**: site_id (PK → site, CASCADE), latitude, longitude (where it was fetched), version (`ARCHIVE_VERSION`), last_year, raw JSON (Open-Meteo daily response, ~0.5 MB), fetched_at

Planned: `plant` / `variety`, `bed`, `planting` (variety × bed × season), `task`. Adding columns to existing tables will need a migration tool (Alembic) before the first public release with data worth keeping.

## Invariants
- **No presets (SPEC P1)**: no code branches on country, hemisphere, climate type or region; decisions come from requirement profiles × environment data. CI banned-pattern check planned (PLAN 4.4).
- `/api/*` responses are `Cache-Control: no-store`; security headers on every response.
- Domain logic (climate, scheduling, rotation) lives in pure, tested modules; routers stay thin; outside calls only in `external.py`.
- Every schema change is an Alembic revision; CI checks models and migrations match.
- Container never runs the app as root.
- Versions in `backend/app/__init__.py` and `frontend/package.json` must match (CI enforces).
