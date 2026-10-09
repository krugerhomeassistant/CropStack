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
| Dependabot | `.github/dependabot.yml` | weekly grouped pip / npm / docker / actions updates |

## Claude session tooling used
- npm/pip registries: version verification (2026-10-09)
- git (anonymous read): Bloomery as the reference layout
- Remote device bridge: deliver files to `E:\Projects\Personal\CropStack`
- No MCP servers required by the app itself.

## Candidate integrations (not yet added)
- Open-Meteo (forecast, historical, geocoding) · MQTT client (aiomqtt) for Home Assistant · Ollama for the co-pilot · Playwright for README screenshots (Bloomery pattern)
