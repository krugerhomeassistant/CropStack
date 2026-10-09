# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.2.0

## Current subtask
Phase 1 done (accounts + garden profile). User wants to install on ZimaOS and follow updates.

## Last execution results
- Backend 13/13, ruff clean, frontend build OK, Playwright E2E (sign up → setup → reload → logout → bad login) passes, no page errors.
- CI green on main; releases v0.1.0 and v0.2.0 created; `ghcr.io/krugerhomeassistant/cropstack:latest` pullable anonymously.

## Blockers
- None. Waiting on the user to install on ZimaOS.

## Immediate next step
Phase 2: climate engine. Research data sources first (hardiness zone outside the US, frost dates, soil temp, geocoding). The engine must handle both hemispheres (Southern: frost season Jun–Aug) and non-US locations (USDA zones are defined from US data; compute the zone from the local extreme-minimum temperature instead).
