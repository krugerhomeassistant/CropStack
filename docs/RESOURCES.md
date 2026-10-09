# RESOURCES

## Key paths
| What | Path |
|---|---|
| Product spec | `docs/SPEC.md` |
| Catalog data-source research (licences, gaps, pipeline) | `docs/research/catalog-data-sources.md` |
| Catalog (planned, CC BY-SA 4.0) | `catalog/` (`sources.yaml`, `crops/`, `organisms/`, `species/`, `schema/`) |
| Roadmap | `docs/PLAN.md` |
| Version | `backend/app/__init__.py` (+ `frontend/package.json`) |
| Settings/env | `backend/app/config.py`, `.env.example` |
| DB engine | `backend/app/db.py` |
| App factory, health, SPA fallback | `backend/app/main.py` |
| Environment engine | `backend/app/environment.py` |
| Climate card description | `backend/app/climate.py` |
| No-presets check | `backend/tests/test_no_presets.py` |
| Outside services | `backend/app/external.py` |
| Climate card / place search | `frontend/src/components/{ClimateCard,PlaceSearch}.tsx` |
| Catalog (data, licence, sources, schema) | `catalog/` (`README.md`, `sources.yaml`, `NOTICE`, `LICENSE`, `schema/`) |
| Catalog code / API | `backend/app/catalog.py`, `backend/app/routers/catalog.py`, `scripts/catalog_schema.py` |
| Private pack (runtime) | `<data>/catalog-private/` |
| Models | `backend/app/models.py` |
| Auth / household / garden API | `backend/app/routers/{auth,household,garden}.py` |
| Migrations | `backend/app/migrations/versions/` |
| API client | `frontend/src/api.ts` |
| Screens | `frontend/src/pages/*.tsx` |
| ZimaOS install | `docker-compose.zimaos.yml` |
| Tests | `backend/tests/` |
| Theme tokens | `frontend/src/index.css` |
| App shell + routes | `frontend/src/App.tsx`, `src/components/Layout.tsx`, `src/state.tsx` |
| Translations / units | `frontend/src/i18n.ts`, `src/units.ts` |
| PWA config | `frontend/vite.config.ts` |
| Release script | `scripts/bump.py` |
| CI + release | `.github/workflows/ci.yml` |
| Data (runtime) | `./data/cropstack.db`, `./data/secret.key` |

## Endpoints (docs at `/api/docs`)
`GET /api/health` · everything else under `/api/v1`: auth `GET status`, `POST register` (optional `invite`), `POST login`, `POST logout`, `GET me`, `PUT prefs`, `POST password` · household `GET|PUT household`, `PUT|DELETE household/members/{user_id}`, `GET|POST household/invites`, `DELETE household/invites/{id}`, public `GET invites/{token}` · site `GET|PUT sites/current`, `GET sites/current/climate`, `GET sites/current/climate/probability?var&op&x`, `GET sites/current/climate/bands?var` · `GET places?q=` · catalog `GET catalog`, `POST catalog/reload`, `GET catalog/{kind}`, `GET catalog/{kind}/{slug}`, `PUT|DELETE catalog/{kind}/{slug}/overrides`

## Repos
- CropStack: https://github.com/krugerhomeassistant/CropStack
- Image: `ghcr.io/krugerhomeassistant/cropstack`
- Sister project / reference implementation: https://github.com/krugerhomeassistant/Bloomery

## External docs
- Open-Meteo forecast (16 d, past_days ≤ 92, hourly soil moisture/temperature, ET0, RH) https://open-meteo.com/en/docs · seasonal (ECMWF EC46/SEAS5, ≤ 7 months, 51 members) https://open-meteo.com/en/docs/seasonal-forecast-api · climate projections (CMIP6 HighResMIP, 10 km, bias-corrected to ERA5-Land) https://open-meteo.com/en/docs/climate-api
- FAO ECOCROP (CC BY 4.0 per FAO Data Catalog; no bulk download) https://ecocrop.apps.fao.org · catalog record https://data.apps.fao.org/catalog/api/3/action/package_show?id=ecocrop · bulk via Recocrop (GPL code, 1,710 taxa) https://cran.r-project.org/web/packages/Recocrop/index.html · FAO DB terms https://www.fao.org/contact-us/terms/db-terms-of-use/en/
- Catalog sources (full list with licences in `docs/research/catalog-data-sources.md`): Wikidata https://www.wikidata.org/wiki/Wikidata:Licensing · World Flora Online (CC0) https://www.worldfloraonline.org · USDA PLANTS https://plants.sc.egov.usda.gov · pyfao56 (FAO-56 tables, CC0) https://github.com/kthorp/pyfao56 · BBCH (CC BY 4.0) https://www.openagrar.de · DSSAT genotypes (BSD-3) https://github.com/DSSAT/dssat-csm-os/tree/develop/Data/Genotype · OpenFarm rescue (CC0, 340 crops) https://github.com/thefullnacho/openfarm-crops-rescue · EPPO open data https://data.eppo.int/documentation/opendata · GloBI https://globalbioticinteractions.org/data · iNaturalist open data https://github.com/inaturalist/inaturalist-open-data · FAO DAD-IS https://www.fao.org/dad-is/en/ · Wikipedia companion list https://en.wikipedia.org/wiki/List_of_companion_plants
- Scraping etiquette: robots.txt RFC 9309 https://www.rfc-editor.org/rfc/rfc9309.html · iNaturalist API practices https://www.inaturalist.org/pages/api+recommended+practices · CC attribution practices https://wiki.creativecommons.org/wiki/Recommended_practices_for_attribution
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
