# TOOLING & MCP

## Runtime tools
| Tool | Use | Why |
|---|---|---|
| Docker + Compose | build/run the single image | one-command self-hosting |
| uvicorn | ASGI server, `--proxy-headers` | correct client IPs behind a reverse proxy |

## Dev tools
| Tool | Command | Why |
|---|---|---|
| pytest | `python -m pytest` (config in `pyproject.toml`) | backend tests |
| ruff | `ruff check . && ruff format --check .` | one fast linter + formatter, CI `lint` job |
| tsc + Vite | `cd frontend && npm run build` | type check + production build |
| Vite dev server | `npm run dev` (proxies `/api` → :8000) | hot reload |
| `scripts/bump.py` | `python scripts/bump.py X.Y.Z` | version in all places + changelog section |
| GitHub Actions | `.github/workflows/ci.yml` | lint, tests, build, GHCR image, release |
| Playwright (Chromium) | E2E script: sign up → garden setup → reload → logout → bad login, 390×844 screenshots | real-browser check of each screen |
| Open-Meteo archive API | climate data (`external.fetch_climate_archive`) | free, global, ERA5-Land 11 km, CC BY 4.0, no key |
| Nominatim | place / postal-code search (`external.search_places`) | finds SA postal codes Open-Meteo geocoding missed |
| `fake_server.py` pattern | E2E: run the app with `external.*` monkeypatched to synthetic data (tests/test_climate.synthetic) | no network or quota needed |
| Alembic 1.20 | schema migrations; `cd backend && alembic revision --autogenerate -m "…"` | standard for SQLAlchemy; batch mode handles SQLite ALTER limits |
| React Router 8 | client routing (declarative mode, import from `react-router`) | standard; v8 removed `react-router-dom` |
| Dependabot | `.github/dependabot.yml` | weekly grouped pip / npm / docker / actions updates |

## Claude session tooling used
- npm/pip registries: version verification (2026-10-09)
- git (anonymous read): Bloomery as the reference layout
- Remote device bridge: deliver files to `E:\Projects\Personal\CropStack`
- No MCP servers required by the app itself.

## Candidate integrations (not yet added)
- Planned by SPEC/PLAN: Hypothesis (property tests, Phase 4) · numpy (vectorised environment engine, Phase 4; check arm64 wheel + RAM) · OR-Tools CP-SAT (only if greedy plan fitting is insufficient, Phase 8) · canvas library for the layout editor (Konva vs plain SVG spike, Phase 8) · axe-core (accessibility CI, Phase 14)
- Open-Meteo (forecast, historical, geocoding) · MQTT client (aiomqtt) for Home Assistant · Ollama for the co-pilot · Playwright for README screenshots (Bloomery pattern)
