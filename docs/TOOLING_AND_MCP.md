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
| `backend/tests/e2e_server.py` | `python -m tests.e2e_server --port 8512`: the app with Open-Meteo and Nominatim stubbed (synthetic climate from `tests/test_climate.synthetic`) | E2E and screenshots with no network or quota |
| `npm run e2e` | `frontend/scripts/e2e.mjs`, Playwright, fresh data folder | main flows in a real browser, also in CI |
| Alembic 1.20 | schema migrations; `cd backend && alembic revision --autogenerate -m "…"` | standard for SQLAlchemy; batch mode handles SQLite ALTER limits |
| React Router 8 | client routing (declarative mode, import from `react-router`) | standard; v8 removed `react-router-dom` |
| PyYAML 6.0.3 | read catalog YAML (`safe_load`) | standard; schema validation stays in Pydantic (no jsonschema dependency) |
| `scripts/catalog_schema.py` | regenerate `catalog/schema/*.json`; `--check` in CI test | schemas follow the models automatically |
| `npm run screenshots` | `CROPSTACK_URL=… CHROMIUM_PATH=/opt/pw-browsers/chromium npm run screenshots` (Playwright 1.64 dev dependency) | visual check of every page × light/dark × phone/desktop before a release (DESIGN.md) |
| Fonts | `@fontsource-variable/bricolage-grotesque`, `@fontsource-variable/atkinson-hyperlegible-next` | self-hosted (offline PWA, no Google Fonts call) |
| pyreadr + pandas (maintainers) | `backend/.venv/bin/pip install pyreadr pandas` | read Recocrop's `ecocrop.rds` (R serialisation); run ingest from the backend venv (httpx, PyYAML) |
| `python scripts/coverage.py [--check]` | list missing/estimated catalog values | feeds docs/COVERAGE.md; CI fails when stale |
| `python scripts/ingest fetch|merge|check` | catalog ingestion (maintainers) | API-first, snapshot-locked, reviewable YAML diffs (SPEC §16.1) |
| GBIF species API | `check`: accepted name + family per crop | CC BY 4.0, reachable from the sandbox; Wikidata SPARQL is not |
| Dependabot | `.github/dependabot.yml` | weekly grouped pip / npm / docker / actions updates |

## Claude session tooling used
- npm/pip registries: version verification (2026-10-09)
- git (anonymous read): Bloomery as the reference layout
- Remote device bridge: deliver files to `E:\Projects\Personal\CropStack`
- No MCP servers required by the app itself.

## Catalog ingestion (planned, Phase 5; versions checked 2026-10-09)
| Tool | Use | Why |
|---|---|---|
| httpx | fetchers; Wikidata SPARQL as a plain GET | already a dependency; SPARQLWrapper (last release 2022) not needed |
| Protego 0.7.0 | robots.txt parsing | RFC 9309 compliant |
| hishel 1.4.0 | HTTP caching / conditional requests | polite refetches |
| selectolax 1.0.0 | HTML extraction (last resort) | fast, small |
| pygbif 0.7.0 | GBIF names/occurrence media | official client |
| frictionless 5.20.0 | Data Package metadata + `frictionless validate` | per-resource licences |
| jsonschema 4.26.0 / pydantic 2.14.0 | catalog schema validation | CI gate |
Raw snapshots live outside git (may be copyrighted); `snapshots.lock` records hashes.

## Candidate integrations (not yet added)
- Planned by SPEC/PLAN: Hypothesis (property tests, Phase 4) · numpy: not needed (analog-year engine in plain Python, ~0.3 s for a 365-day curve; revisit if window search for many crops is slow) · OR-Tools CP-SAT (only if greedy plan fitting is insufficient, Phase 8) · canvas library for the layout editor (Konva vs plain SVG spike, Phase 8) · axe-core (accessibility CI, Phase 14)
- Open-Meteo (forecast, historical, geocoding) · MQTT client (aiomqtt) for Home Assistant · Ollama for the assistant · Playwright for README screenshots (Bloomery pattern)

## Project scripts (v0.38)
- `scripts/bump.py X.Y.Z` version everywhere · `scripts/coverage.py [--check]` catalog coverage · `scripts/ingest fetch|merge|check` catalog build · `ruff format . && ruff check .` before every push · `npm run e2e` (restart the server first; a dirty DB fails it) · `npm run screenshots`.
- Deferred/not adopted: Mealie (not running yet), OR-Tools (greedy year plan suffices).
