# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.5.1

## Current subtask
Catalog data-sourcing research merged into the docs (user: "open-source data, even if we need to scrape and store it ourselves; accurate, extensive, truthful"). Phase 3 (platform) is released as v0.5.0.

## Last execution results
- v0.5.1 (fix, rebased onto the research commits): after updating to v0.5.0 the user saw "Cannot reach the CropStack server" (cached v0.4 app calling removed `/api/auth/*`). Reproduced with Docker images 0.4.0 → latest and a persistent Playwright profile; fix = version check via `/api/health` + one automatic reload, real error messages, "Try again" = full reload (LESSONS 39–40). Upgrade of real v0.4 data verified on the published image (healthy, data intact).
- Report `docs/research/catalog-data-sources.md` (licences verified on primary pages 2026-10-09; conflicts resolved: ECOCROP = CC BY 4.0 per FAO Data Catalog, OpenFarm data = CC0, 340-crop rescue repo CC0).
- Decisions: catalog in `catalog/` (not `data/`, the runtime volume); catalog licence CC BY-SA 4.0, code MIT; per-value provenance + evidence levels; maintainer-only ingestion pipeline with licence gate (SPEC §16, §16.1). PLAN 3.4, 5, 9.1 updated; WIKI, RESOURCES, TOOLING, LESSONS 35–38, README updated. No code changes.
- v0.5.0 state (previous session): backend 45/45, ruff clean, frontend build OK; one unreproduced test error seen once during 3.3, watch CI.

## Handoff to the implementing session
- Pull `main` first; then read, in order: this file, SPEC §6.1, §16, §16.1, PLAN 3.4 / Phase 5 / 9.1, `docs/research/catalog-data-sources.md` (decisions + source table), `docs/research/notes/*.md` (per-domain evidence: cited values, URLs, licence quotes, gaps).
- Treat `licence_conflicts_resolved.md` as overriding the other notes where they disagree.
- Values marked "unverified" in the notes must not be bundled until checked.

## Blockers
- None. Open: SPEC §19 Q6 (ask ARC-VOPI for reuse permission?); user may veto CC BY-SA 4.0 for the catalog.

## Immediate next step
Phase 4.1: environment engine v2 (DOY distributions with recency weighting/trend; query API prob/gdd/chill/water_balance; numpy decision: check arm64 wheel + RAM). Phase 3.4 catalog infrastructure is now unblocked and can follow.
