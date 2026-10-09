# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.2.0

## Current subtask
Phase 1 done (accounts + garden profile). User wants to install on ZimaOS and follow updates.

## Last execution results
- Backend 13/13, ruff clean, frontend build OK, Playwright E2E (sign up → setup → reload → logout → bad login) passes, no page errors.
- First CI run on main was still in progress at commit time.

## Blockers
- GHCR package `cropstack` must be set Public by the user after CI publishes it, or ZimaOS can't pull it.

## Immediate next step
Phase 2: climate engine. Research data sources first (hardiness zone outside the US, frost dates, soil temp, geocoding). The engine must handle both hemispheres (Southern: frost season Jun–Aug) and non-US locations (USDA zones are defined from US data; compute the zone from the local extreme-minimum temperature instead).
