# PLAN

## Phase 0 — Foundation (v0.1.0)
- [x] Mirror Bloomery repo layout (backend / frontend / docs / scripts / .github)
- [x] Verify latest package versions (pip/npm registries, 2026-10-09)
- [x] Backend: config, SQLite engine, app factory, `/api/health`, security headers, SPA fallback
- [x] Backend test (`backend/tests/test_health.py`), ruff clean
- [x] Frontend: Vite + React + Tailwind v4 + PWA shell with theme tokens, dark mode, icon
- [x] Multi-stage Dockerfile (non-root, healthcheck), entrypoint, compose, `.env.example`
- [x] CI (version check, lint, tests, build, GHCR multi-arch image, auto release), Dependabot, issue/PR templates
- [x] README, CHANGELOG, CONTRIBUTING, SECURITY, CODE_OF_CONDUCT, LICENSE
- [x] Living docs in `docs/`
- [x] Create GitHub repo and push `main` (rebased on GitHub's LICENSE commit)
- [x] GHCR image `cropstack` is publicly pullable (verified anonymous manifest fetch, 2026-10-09)
- [x] ZimaOS compose (`docker-compose.zimaos.yml`, /DATA/AppData/cropstack, 256 MiB) + README guide incl. updating
- [ ] User: install on ZimaOS
- [ ] Verify `docker compose up -d --build` on the user's host

## Phase 1 — Accounts & garden profile (v0.2.0)
- [x] `user` model, argon2 hashing, register/login/logout/me/password (Bloomery pattern, IP throttling)
- [x] `garden` model: name, lat/lon, postal code, frost probability (default 50%); one per user
- [x] UI: sign-up/login, garden setup (geolocation + manual), home card, edit, logout
- [x] Tests: 13 backend (auth flow, throttle, registration modes, garden CRUD/isolation/validation) + Playwright E2E
- [ ] Elevation (fetch with climate in Phase 2 rather than asking the user)
- [ ] Onboarding step "confirm detected climate" (needs Phase 2)

## Phase 2 — Climate engine (v0.3.0)
- [ ] Research data sources: USDA zone (PRISM / phzmapi), frost dates (NOAA normals or Open-Meteo historical), soil temp, daylight (astral calc)
- [ ] `climate.py` pure functions: zone, LSF/FFF at a probability, season length, daylight curve
- [ ] Geocoding for postal codes (Open-Meteo / Nominatim), cached in DB
- [ ] Tests with fixed fixtures (no network)
- [ ] Southern Hemisphere support (frost season Jun–Aug) and non-US zones (compute zone from local extreme-minimum temperature)

## Phase 3 — Encyclopedia & task engine (v0.4.0)
- [ ] Plant data schema (When/How/What), seed dataset (start with ~40 common crops), licence-checked sources
- [ ] `schedule.py`: tasks from variety timing × climate (rules in WIKI)
- [ ] Calendar + task list UI, mark done/skip
- [ ] iCal feed

## Phase 4 — Garden mapper & rotation (v0.5.0)
- [ ] Bed/plot model + drag-and-drop canvas, square-foot grid, spacing warnings
- [ ] Plantings per bed per season; rotation conflict detection by crop family
- [ ] Companion warnings on the map

## Phase 5 — Weather adaptation (v0.6.0)
- [ ] Forecast client (Open-Meteo), frost/heat/rain rules shifting tasks
- [ ] Notifications (ntfy / Gotify / HA / Web Push, Bloomery pattern)

## Phase 6 — Home Assistant (v0.7.0)
- [ ] REST sensor feed + HACS integration (Bloomery `custom_components` pattern)
- [ ] MQTT ingest for soil moisture / light / greenhouse sensors; irrigation automation hooks

## Phase 7 — AI co-pilot (v0.8.0)
- [ ] Provider abstraction (port Bloomery `ai.py`: ollama/openai/anthropic/custom)
- [ ] Garden-context chat, photo diagnostics (vision models), preservation recipes from harvest

## Later — Homestead suite
- [ ] Pantry & preservation inventory · Seed vault · Livestock & orchard modules
