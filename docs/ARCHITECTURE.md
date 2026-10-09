# ARCHITECTURE

## Topology
```
Browser/PWA ──HTTP──▶ cropstack container :8000 (host :8430)
                        ├─ FastAPI  /api/*            (session-cookie auth, planned)
                        ├─ static SPA /*              (Vite build, service worker precache)
                        ├─ SQLite  /data/cropstack.db (WAL, foreign keys on)
                        └─ httpx ──▶ archive-api.open-meteo.com (climate) · nominatim.openstreetmap.org (place search)
```
Single image, multi-stage: `node:24-alpine` builds the SPA → `python:3.14-slim` runtime. `entrypoint.sh` starts as root, chowns `$CROPSTACK_DATA_DIR`, then drops to uid 10001 via `setpriv`. One uvicorn worker, access log off, `--proxy-headers` for reverse proxies.

Target architecture (engines, data model, API) is specified in `docs/SPEC.md` §13–15. Planned optional services: weather API client (httpx), MQTT client for Home Assistant, Ollama (compose profile `ai`) or OpenAI-compatible API for the co-pilot. Postgres is an option only if multi-user scale demands it; SQLite is the default.

## Stack (pinned 2026-10-09)
| Layer | Tech |
|---|---|
| Backend | Python 3.14 (runtime, CI) / 3.13+ (dev), FastAPI 0.143.0, uvicorn 0.54.0, SQLModel 0.0.48, pydantic-settings 2.15.0, alembic 1.20.0, argon2-cffi 25.1.0, itsdangerous 2.2.0, httpx 0.28.1, tzdata 2026.5 |
| Frontend | React 19.3, Vite 8.3, TypeScript 7.0, Tailwind 4.3 (`@tailwindcss/vite`), vite-plugin-pwa 2.0, lucide-react 1.53, @fontsource-variable/nunito (self-hosted font) |
| Tooling | ruff (lint + format), pytest, GitHub Actions, Dependabot, GHCR |

## Backend modules (`backend/app/`)
| File | Role |
|---|---|
| `__init__.py` | `VERSION` (single source; `scripts/bump.py` keeps frontend in sync) |
| `config.py` | `Settings` (env `CROPSTACK_*`), secret auto-generation |
| `db.py` | engine (WAL + FK pragmas), `init_db` (Alembic `upgrade head`, foreign keys off while migrating), `get_session` dependency |
| `migrations/` | Alembic env + revisions (`0001_baseline` = v0.4.0 schema, creates only missing tables) |
| `models.py` | `User`, `Household`, `Membership` (PK user_id → one household per user), `Invite` (hashed token), `Site` (one per household), `ClimateCache` |
| `deps.py` | `SessionDep`, `UserDep`, `MemberDep`, `OwnerDep`, `EditorDep` (`require_role`), argon2 `hash_pw` / `verify_pw` |
| `routers/household.py` | household name, members (role, remove), invites (create, list, revoke), public invite info |
| `routers/auth.py` | status, register (new household or via invite), login (IP throttle), logout, me (with role + household), password |
| `climate.py` | **pure** climate engine: season stats, frost dates at a risk, zone, daylight, monthly means, `summarize`, `report` |
| `external.py` | Open-Meteo archive fetch, Nominatim search, `ExternalError` |
| `routers/garden.py` | `GET` / `PUT /api/garden`, `GET /api/garden/climate` (cached), `GET /api/places` |
| `main.py` | app factory, session + security-header middleware, `/api/health`, SPA fallback |

## Frontend (`frontend/`)
| File | Role |
|---|---|
| `src/main.tsx` | entry, service-worker registration |
| `src/api.ts` | typed fetch client, `ApiError` |
| `src/App.tsx` | screen state machine: loading → auth → garden setup → home |
| `src/pages/` | `Auth`, `GardenSetup`, `Home` |
| `src/components/` | `PlaceSearch` (not a form: nested in the garden form), `ClimateCard` |
| `src/index.css` | Tailwind theme tokens (canvas, ink, muted, leaf, sprout, soil, card) + dark mode |
| `vite.config.ts` | PWA manifest, `/api` dev proxy → :8000 |

## Environment variables (no secrets in repo)
| Key | Default | Notes |
|---|---|---|
| `CROPSTACK_DATA_DIR` | `./data` (`/data` in image) | SQLite + secret key |
| `CROPSTACK_STATIC_DIR` | `./static` (`/app/static` in image) | built SPA; SPA route disabled if missing |
| `CROPSTACK_SECRET_KEY` | auto | session signing |
| `CROPSTACK_ALLOW_REGISTRATION` | `auto` | `auto` / `true` / `false` |
| `CROPSTACK_SECURE_COOKIES` | `false` | HTTPS-only cookies |
| `CROPSTACK_PORT` | `8430` | compose host port only |

## DB schema (SQLite, Alembic migrations; head 0002)
- **user**: id, username (unique, lowercased), password_hash (argon2id), display_name, created_at
- **household**: id, name, created_at
- **membership**: user_id (PK → user, CASCADE), household_id (→ household, CASCADE, indexed), role (owner|member|viewer), created_at
- **invite**: token_hash (PK, SHA-256), household_id (→ household, CASCADE), role, created_by (→ user, SET NULL), created_at, expires_at, used_at
- **site**: id, household_id (→ household, unique, CASCADE), name, latitude, longitude, postal_code, frost_probability (10–90), created_at, updated_at
- **climatecache**: site_id (PK → site, CASCADE), latitude, longitude (location it was fetched for), summary JSON (`version`, `season_start`, `first_frost[]`, `last_frost[]`, `annual_min[]`, `monthly{tmin,tmax,soil,rain,hot_days}`, `elevation_m`, `timezone`, `period`), fetched_at

Planned: `plant` / `variety`, `bed`, `planting` (variety × bed × season), `task`. Adding columns to existing tables will need a migration tool (Alembic) before the first public release with data worth keeping.

## Invariants
- **No presets (SPEC P1)**: no code branches on country, hemisphere, climate type or region; decisions come from requirement profiles × environment data. CI banned-pattern check planned (PLAN 4.4).
- `/api/*` responses are `Cache-Control: no-store`; security headers on every response.
- Domain logic (climate, scheduling, rotation) lives in pure, tested modules; routers stay thin; outside calls only in `external.py`.
- Every schema change is an Alembic revision; CI checks models and migrations match.
- Container never runs the app as root.
- Versions in `backend/app/__init__.py` and `frontend/package.json` must match (CI enforces).
