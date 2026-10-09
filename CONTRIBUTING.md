# Contributing

Thanks for helping! Issues and pull requests are welcome. Please follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Develop

```bash
# backend (Python 3.13+)
cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt pytest
CROPSTACK_DATA_DIR=./data uvicorn app.main:app --reload --port 8000
# frontend (Node 24), proxies /api to :8000
cd frontend && npm ci && npm run dev
```

On Windows, activate the venv with `.venv\Scripts\activate` and set variables with `$env:CROPSTACK_DATA_DIR="./data"`.

## Code standards

- **Python**: ruff for lint and format (config in `pyproject.toml`), type hints on public functions, docstrings on modules. Keep domain logic (climate, scheduling, rotation) in pure functions with tests.
- **TypeScript**: `strict` mode, function components, Tailwind theme tokens from `frontend/src/index.css` instead of raw colours.
- **UI**: build screens from `frontend/src/components/ui/` and follow [docs/DESIGN.md](docs/DESIGN.md). Before a release look at the `npm run screenshots` images (see E2E and screenshots below) for every changed page in light and dark, phone and desktop.
- **Commits**: small and focused, imperative subject ("Add frost-date lookup").
- **Docs**: update `README.md` and `docs/WIKI.md` in the same PR as any user-facing change, and add a line under `[Unreleased]` in `CHANGELOG.md`.

## Database changes

Every change to `backend/app/models.py` needs a migration:

```bash
cd backend && alembic revision --autogenerate -m "add planting table"
```

Review the generated file in `app/migrations/versions/` (autogenerate misses renames and data moves), then run the tests: `test_migrations.py` fails if models and migrations differ. The app applies migrations automatically on start.

## Catalog changes

Catalog data lives in `catalog/` (CC BY-SA 4.0); see [`catalog/README.md`](catalog/README.md) for the format and rules. Every value cites a source registered in `catalog/sources.yaml`; write descriptions in your own words. After changing the models in `backend/app/catalog.py`, run `python scripts/catalog_schema.py`. The app (and the tests) refuse to start on an invalid catalog.

Values that come from open or factual sources are imported, not typed: `python scripts/ingest fetch` (run it from the backend venv; ECOCROP also needs `pip install pyreadr pandas`; downloads into `.ingest-cache/`, records `scripts/ingest/snapshots.lock`), then `python scripts/ingest merge` and review `git diff catalog/`. Hand-written values always win over imported ones. To add a crop, write its curated base file (names, scientific name, family, rotation group, life cycle, description) in `catalog/crops/`, add its row names to `scripts/ingest/crosswalk.yaml`, run `merge`, and run `python scripts/ingest check` against GBIF.

## Checks (same as CI)

```bash
pip install ruff && ruff check . && ruff format --check .
python -m pytest
cd frontend && npm run build
```

### E2E and screenshots

Browser tests run against a server whose outside services (Open-Meteo, Nominatim) are stubbed, so they need no network. Start it on an empty data folder, then run the flows and the screenshots:

```bash
cd frontend && npm run build
(cd ../backend && CROPSTACK_DATA_DIR=/tmp/cs-e2e CROPSTACK_STATIC_DIR=../frontend/dist CROPSTACK_SCHEDULER=false python -m tests.e2e_server --port 8512 &)
npx playwright install chromium   # once
CROPSTACK_URL=http://127.0.0.1:8512 npm run e2e
CROPSTACK_URL=http://127.0.0.1:8512 CROPSTACK_USER=jan CROPSTACK_PASSWORD=garden123 npm run screenshots
```

`npm run e2e` expects a fresh data folder (it signs up the first account). CI runs both and uploads the screenshots as the `screenshots` artifact.

## Releasing (maintainers)

1. Note changes under `## [Unreleased]` in `CHANGELOG.md` as you go, and reread `README.md` and `docs/WIKI.md` so they match the release.
2. `python scripts/bump.py X.Y.Z` (updates backend and frontend versions and the changelog).
3. `git commit -am "Release vX.Y.Z" && git push`

When a version that has no release yet reaches `main`, CI runs every check, publishes `ghcr.io/krugerhomeassistant/cropstack:X.Y.Z` (+ `X.Y`), then creates the `vX.Y.Z` tag and GitHub release with notes from the changelog.
