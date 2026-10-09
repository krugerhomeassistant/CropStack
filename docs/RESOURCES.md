# RESOURCES

## Key paths
| What | Path |
|---|---|
| Version | `backend/app/__init__.py` (+ `frontend/package.json`) |
| Settings/env | `backend/app/config.py`, `.env.example` |
| DB engine | `backend/app/db.py` |
| App factory, health, SPA fallback | `backend/app/main.py` |
| Models | `backend/app/models.py` |
| Auth / garden API | `backend/app/routers/{auth,garden}.py` |
| API client | `frontend/src/api.ts` |
| Screens | `frontend/src/pages/*.tsx` |
| ZimaOS install | `docker-compose.zimaos.yml` |
| Tests | `backend/tests/` |
| Theme tokens | `frontend/src/index.css` |
| App shell | `frontend/src/App.tsx` |
| PWA config | `frontend/vite.config.ts` |
| Release script | `scripts/bump.py` |
| CI + release | `.github/workflows/ci.yml` |
| Data (runtime) | `./data/cropstack.db`, `./data/secret.key` |

## Endpoints (under `/api`, docs at `/api/docs`)
`GET health` · auth: `GET status`, `POST register`, `POST login`, `POST logout`, `GET me`, `POST password` · `GET|PUT garden`

## Repos
- CropStack: https://github.com/krugerhomeassistant/CropStack
- Image: `ghcr.io/krugerhomeassistant/cropstack`
- Sister project / reference implementation: https://github.com/krugerhomeassistant/Bloomery

## External docs
- ZimaOS updating `:latest` apps (community): https://shop.zimaspace.com/pages/zimaos-1-7-app-update-registry-vs-store
- FastAPI https://fastapi.tiangolo.com · SQLModel https://sqlmodel.tiangolo.com · pydantic-settings https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Vite https://vite.dev · Tailwind v4 https://tailwindcss.com/docs · vite-plugin-pwa https://vite-pwa-org.netlify.app · lucide https://lucide.dev
- Keep a Changelog https://keepachangelog.com/en/1.1.0/ · Semantic Versioning https://semver.org
- Candidate climate data (Phase 2, to verify): USDA Plant Hardiness Zone Map https://planthardiness.ars.usda.gov · Open-Meteo https://open-meteo.com · NOAA climate normals https://www.ncei.noaa.gov/products/land-based-station/us-climate-normals
- Home Assistant developer docs https://developers.home-assistant.io

## Local
- Host folder: `E:\Projects\Personal\CropStack`
- Default URL: http://localhost:8430
