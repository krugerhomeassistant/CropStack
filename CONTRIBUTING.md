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
- **Commits**: small and focused, imperative subject ("Add frost-date lookup").
- **Docs**: update `README.md` and `docs/WIKI.md` in the same PR as any user-facing change, and add a line under `[Unreleased]` in `CHANGELOG.md`.

## Checks (same as CI)

```bash
pip install ruff && ruff check . && ruff format --check .
python -m pytest
cd frontend && npm run build
```

## Releasing (maintainers)

1. Note changes under `## [Unreleased]` in `CHANGELOG.md` as you go.
2. `python scripts/bump.py X.Y.Z` (updates backend and frontend versions and the changelog).
3. `git commit -am "Release vX.Y.Z" && git push`

When a version that has no release yet reaches `main`, CI runs every check, publishes `ghcr.io/krugerhomeassistant/cropstack:X.Y.Z` (+ `X.Y`), then creates the `vX.Y.Z` tag and GitHub release with notes from the changelog.
