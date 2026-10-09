# ARCHITECTURE

## Topology
```
Browser/PWA ──HTTP──▶ cropstack container :8000 (host :8430)
                        ├─ FastAPI  /api/*            (session-cookie auth, planned)
                        ├─ static SPA /*              (Vite build, service worker precache)
                        └─ SQLite  /data/cropstack.db (WAL, foreign keys on)
```
Single image, multi-stage: `node:24-alpine` builds the SPA → `python:3.14-slim` runtime. `entrypoint.sh` starts as root, chowns `$CROPSTACK_DATA_DIR`, then drops to uid 10001 via `setpriv`. One uvicorn worker, access log off, `--proxy-headers` for reverse proxies.

Planned optional services: weather API client (httpx), MQTT client for Home Assistant, Ollama (compose profile `ai`) or OpenAI-compatible API for the co-pilot. Postgres is an option only if multi-user scale demands it; SQLite is the default.

## Stack (pinned 2026-10-09)
| Layer | Tech |
|---|---|
| Backend | Python 3.14 (runtime, CI) / 3.13+ (dev), FastAPI 0.143.0, uvicorn 0.54.0, SQLModel 0.0.48, pydantic-settings 2.15.0, itsdangerous 2.2.0, httpx 0.28.1, tzdata 2026.5 |
| Frontend | React 19.3, Vite 8.3, TypeScript 7.0, Tailwind 4.3 (`@tailwindcss/vite`), vite-plugin-pwa 2.0, lucide-react 1.53, @fontsource-variable/nunito (self-hosted font) |
| Tooling | ruff (lint + format), pytest, GitHub Actions, Dependabot, GHCR |

## Backend modules (`backend/app/`)
| File | Role |
|---|---|
| `__init__.py` | `VERSION` (single source; `scripts/bump.py` keeps frontend in sync) |
| `config.py` | `Settings` (env `CROPSTACK_*`), secret auto-generation |
| `db.py` | engine (WAL + FK pragmas), `init_db`, `get_session` dependency |
| `main.py` | app factory, session + security-header middleware, `/api/health`, SPA fallback |

## Frontend (`frontend/`)
| File | Role |
|---|---|
| `src/main.tsx` | entry, service-worker registration |
| `src/App.tsx` | app shell (status screen for now) |
| `src/index.css` | Tailwind theme tokens (canvas, ink, muted, leaf, sprout, soil, card) + dark mode |
| `vite.config.ts` | PWA manifest, `/api` dev proxy → :8000 |

## Environment variables (no secrets in repo)
| Key | Default | Notes |
|---|---|---|
| `CROPSTACK_DATA_DIR` | `./data` (`/data` in image) | SQLite + secret key |
| `CROPSTACK_STATIC_DIR` | `./static` (`/app/static` in image) | built SPA; SPA route disabled if missing |
| `CROPSTACK_SECRET_KEY` | auto | session signing |
| `CROPSTACK_SECURE_COOKIES` | `false` | HTTPS-only cookies |
| `CROPSTACK_PORT` | `8430` | compose host port only |

## DB schema
None yet (v0.1.0). Planned first tables: `user`, `garden` (location, zone, frost dates, frost probability), `plant` / `variety` (encyclopedia), `bed`, `planting` (variety × bed × season), `task`.

## Invariants
- `/api/*` responses are `Cache-Control: no-store`; security headers on every response.
- Domain logic (climate, scheduling, rotation) lives in pure, tested modules; routers stay thin.
- Container never runs the app as root.
- Versions in `backend/app/__init__.py` and `frontend/package.json` must match (CI enforces).
