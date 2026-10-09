# RESOURCES

## Key paths
| What | Path |
|---|---|
| Product spec | `docs/SPEC.md` |
| Roadmap | `docs/PLAN.md` |
| Version | `backend/app/__init__.py` (+ `frontend/package.json`) |
| Settings/env | `backend/app/config.py`, `.env.example` |
| DB engine | `backend/app/db.py` |
| App factory, health, SPA fallback | `backend/app/main.py` |
| Climate engine | `backend/app/climate.py` |
| Outside services | `backend/app/external.py` |
| Climate card / place search | `frontend/src/components/{ClimateCard,PlaceSearch}.tsx` |
| Models | `backend/app/models.py` |
| Auth / household / garden API | `backend/app/routers/{auth,household,garden}.py` |
| Migrations | `backend/app/migrations/versions/` |
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
`GET health` · auth: `GET status`, `POST register`, `POST login`, `POST logout`, `GET me`, `POST password` · household: `GET|PUT household`, `PUT|DELETE household/members/{user_id}`, `GET|POST household/invites`, `DELETE household/invites/{id}`, public `GET invites/{token}` · `GET|PUT garden` · `GET garden/climate` · `GET places?q=`

## Repos
- CropStack: https://github.com/krugerhomeassistant/CropStack
- Image: `ghcr.io/krugerhomeassistant/cropstack`
- Sister project / reference implementation: https://github.com/krugerhomeassistant/Bloomery

## External docs
- Open-Meteo forecast (16 d, past_days ≤ 92, hourly soil moisture/temperature, ET0, RH) https://open-meteo.com/en/docs · seasonal (ECMWF EC46/SEAS5, ≤ 7 months, 51 members) https://open-meteo.com/en/docs/seasonal-forecast-api · climate projections (CMIP6 HighResMIP, 10 km, bias-corrected to ERA5-Land) https://open-meteo.com/en/docs/climate-api
- FAO ECOCROP (crop temperature/rain ranges; ~2,300 species; open access, reuse terms to verify) https://www.fao.org/land-water/resources/tools/databases/ecocrop/en · Wikipedia summary https://en.wikipedia.org/wiki/Ecocrop
- Plant data APIs survey (Trefle CC BY 4.0, Permapeople CC BY-SA non-commercial, Perenual paid, OpenFarm shut down Apr 2025) https://github.com/PflanzenDex/PflanzenDex/issues/599 · OpenFarm archive (CC0 data) https://github.com/openfarmcc/OpenFarm · Growstuff https://github.com/Growstuff/growstuff
- Livestock heat stress / THI background https://animalscience.tamu.edu/wp-content/uploads/sites/4/2023/08/heatstress3.pdf
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
