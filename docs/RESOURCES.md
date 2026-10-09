# RESOURCES

## Key paths
| What | Path |
|---|---|
| Version | `backend/app/__init__.py` (+ `frontend/package.json`) |
| Settings/env | `backend/app/config.py`, `.env.example` |
| DB engine | `backend/app/db.py` |
| App factory, health, SPA fallback | `backend/app/main.py` |
| Climate engine | `backend/app/climate.py` |
| Outside services | `backend/app/external.py` |
| Climate card / place search | `frontend/src/components/{ClimateCard,PlaceSearch}.tsx` |
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
`GET health` · auth: `GET status`, `POST register`, `POST login`, `POST logout`, `GET me`, `POST password` · `GET|PUT garden` · `GET garden/climate` · `GET places?q=`

## Repos
- CropStack: https://github.com/krugerhomeassistant/CropStack
- Image: `ghcr.io/krugerhomeassistant/cropstack`
- Sister project / reference implementation: https://github.com/krugerhomeassistant/Bloomery

## External docs
- ZimaOS updating `:latest` apps (community): https://shop.zimaspace.com/pages/zimaos-1-7-app-update-registry-vs-store
- FastAPI https://fastapi.tiangolo.com · SQLModel https://sqlmodel.tiangolo.com · pydantic-settings https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- Vite https://vite.dev · Tailwind v4 https://tailwindcss.com/docs · vite-plugin-pwa https://vite-pwa-org.netlify.app · lucide https://lucide.dev
- Keep a Changelog https://keepachangelog.com/en/1.1.0/ · Semantic Versioning https://semver.org
- Open-Meteo historical API https://open-meteo.com/en/docs/historical-weather-api · terms/limits https://open-meteo.com/en/pricing · model ids in source `Sources/App/Controllers/ForecastapiController.swift` (`era5_seamless` → ERA5 + ERA5-Land) https://github.com/open-meteo/open-meteo
- Nominatim search API https://nominatim.org/release-docs/latest/api/Search/ · usage policy https://operations.osmfoundation.org/policies/nominatim/
- USDA zone definition (−60 °F start, 10 °F zones, 5 °F half-zones) https://planthardiness.ars.usda.gov
- Home Assistant developer docs https://developers.home-assistant.io

## Local
- Host folder: `E:\Projects\Personal\CropStack`
- Default URL: http://localhost:8430
