# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.5.0

## Current subtask
Phase 3 (platform) released as v0.5.0: Alembic migrations (0001 baseline, 0002 households/sites, 0003 user prefs), households with roles + invite links, app shell (Today · Garden · More), personal settings (start screen, units), /api/v1, translation layer.

## Last execution results
- Backend 45/45, ruff clean, frontend build OK. Migration tests upgrade real v0.2.0/v0.4.0 schemas (fixtures from git tags) and prove the foreign-keys-off guard prevents cascade deletes. Playwright E2E: owner signup → setup → Today; settings (imperial, start = climate) persist; invite → wife joins, sees Today, no edit controls, no invite section.
- One unreproduced test error seen once during 3.3 (passed 7 reruns); watch CI.

## Blockers
- Phase 3.4 (catalog storage) and Phase 5 (catalog content) wait for the user's separate deep-research chat on data sources and storage.

## Immediate next step
Phase 4.1: environment engine v2 (DOY distributions with recency weighting/trend; query API prob/gdd/chill/water_balance; numpy decision: check arm64 wheel + RAM). Independent of the catalog research.
