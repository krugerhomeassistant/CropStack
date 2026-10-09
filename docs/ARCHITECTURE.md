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

Planned optional services: weather API client (httpx), MQTT client for Home Assistant, Ollama (compose profile `ai`) or OpenAI-compatible API for the co-pilot. Postgres is an option only if multi-user scale demands it; SQLite is the default.

## Stack (pinned 2026-10-09)
| Layer | Tech |
|---|---|
| Backend | Python 3.14 (runtime, CI) / 3.13+ (dev), FastAPI 0.143.0, uvicorn 0.54.0, SQLModel 0.0.48, pydantic-settings 2.15.0, argon2-cffi 25.1.0, itsdangerous 2.2.0, httpx 0.28.1, tzdata 2026.5 |
| Frontend | React 19.3, Vite 8.3, TypeScript 7.0, Tailwind 4.3 (`@tailwindcss/vite`), vite-plugin-pwa 2.0, lucide-react 1.53, @fontsource-variable/nunito (self-hosted font) |
| Tooling | ruff (lint + format), pytest, GitHub Actions, Dependabot, GHCR |

## Backend modules (`backend/app/`)
| File | Role |
|---|---|
| `__init__.py` | `VERSION` (single source; `scripts/bump.py` keeps frontend in sync) |
| `config.py` | `Settings` (env `CROPSTACK_*`), secret auto-generation |
| `db.py` | engine (WAL + FK pragmas), `init_db`, `get_session` dependency |
| `models.py` | `User`, `Garden` |
| `deps.py` | `SessionDep`, `UserDep`, argon2 `hash_pw` / `verify_pw` |
| `routers/auth.py` | status, register, login (IP throttle), logout, me, password |
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

## DB schema (SQLite, `create_all`; no migrations yet)
- **user**: id, username (unique, lowercased), password_hash (argon2id), display_name, created_at
- **garden**: id, user_id → user (unique, CASCADE), name, latitude, longitude, postal_code, frost_probability (10–90, default 50), created_at, updated_at
- **climatecache**: garden_id (PK) → garden (CASCADE), latitude, longitude (location it was fetched for), summary JSON (`season_start`, `first_frost[]`, `last_frost[]`, `annual_min[]`, `monthly{tmin,tmax,soil}`, `elevation_m`, `timezone`, `period`), fetched_at. New *table* rather than new garden columns, so existing installs need no migration.

Planned: `plant` / `variety`, `bed`, `planting` (variety × bed × season), `task`. Adding columns to existing tables will need a migration tool (Alembic) before the first public release with data worth keeping.

## Invariants
- `/api/*` responses are `Cache-Control: no-store`; security headers on every response.
- Domain logic (climate, scheduling, rotation) lives in pure, tested modules; routers stay thin; outside calls only in `external.py`.
- Schema changes add tables, not columns, until a migration tool is in place.
- Container never runs the app as root.
- Versions in `backend/app/__init__.py` and `frontend/package.json` must match (CI enforces).
