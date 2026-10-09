# RESOURCES

## Key paths
| What | Path |
|---|---|
| Version | `backend/app/__init__.py` (+ `frontend/package.json`) |
| Settings/env | `backend/app/config.py`, `.env.example` |
| DB engine | `backend/app/db.py` |
| App factory, health, SPA fallback | `backend/app/main.py` |
| Tests | `backend/tests/` |
| Theme tokens | `frontend/src/index.css` |
| App shell | `frontend/src/App.tsx` |
| PWA config | `frontend/vite.config.ts` |
| Release script | `scripts/bump.py` |
| CI + release | `.github/workflows/ci.yml` |
| Data (runtime) | `./data/cropstack.db`, `./data/secret.key` |

## Endpoints (under `/api`, docs at `/api/docs`)
`GET health`

## Repos
- CropStack: https://github.com/krugerhomeassistant/CropStack (to be created)
- Image: `ghcr.io/krugerhomeassistant/cropstack`
- Sister project / reference implementation: https://github.com/krugerhomeassistant/Bloomery

## External docs
- FastAPI https://fastapi.tiangolo.com · SQLModel https://sqlmodel.tiangolo.com · pydantic-settings https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Vite https://vite.dev · Tailwind v4 https://tailwindcss.com/docs · vite-plugin-pwa https://vite-pwa-org.netlify.app · lucide https://lucide.dev
- Keep a Changelog https://keepachangelog.com/en/1.1.0/ · Semantic Versioning https://semver.org
- Candidate climate data (Phase 2, to verify): USDA Plant Hardiness Zone Map https://planthardiness.ars.usda.gov · Open-Meteo https://open-meteo.com · NOAA climate normals https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals
- Home Assistant developer docs https://developers.home-assistant.io

## Local
- Host folder: `E:\Projects\Personal\CropStack`
- Default URL: http://localhost:8430
