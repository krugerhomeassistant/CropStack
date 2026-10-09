# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.7.0

## Current subtask
Phase 3.4 catalog infrastructure done (target v0.7.0): `catalog.py` models + loader + licence gate + private pack + overrides (migration 0005), catalog API, `catalog/` with LICENSE/NOTICE/README/sources.yaml (26 sources)/schema, Dockerfile ships `catalog/`.

## Last execution results
- Backend 78/78 (3 consecutive runs; the old flaky error was a username collision from `id()`, fixed), ruff clean, schema files current.
- v0.6.0 released earlier today (analog-year climate engine, data-only climate card, no-presets test).
- CI-built image verified in Docker: starts on upgraded user data, loads bundled catalog, picks up a private-pack crop (`origin: private`).

## Handoff to the implementing session
- Pull `main` first; then read, in order: this file, SPEC §6.1, §16, §16.1, PLAN 3.4 / Phase 5 / 9.1, `docs/research/catalog-data-sources.md` (decisions + source table), `docs/research/notes/*.md` (per-domain evidence: cited values, URLs, licence quotes, gaps).
- Treat `licence_conflicts_resolved.md` as overriding the other notes where they disagree.
- Values marked "unverified" in the notes must not be bundled until checked.

## Standing requirements
- **Professional look and feel** (owner, 2026-10-09): "just for me" is about licensing only. Design system (PLAN 6.9) comes before the Today screen; every changed screen gets a visual check in light/dark and phone/desktop before release.

## Blockers
- None. Decided 2026-10-09 (user: personal, non-commercial use; repo stays public): public `catalog/` = CC BY-SA 4.0; no ARC request for now; personal-use values go in a private pack on the server (SPEC §16.1, §19 Q6–7).

## Immediate next step
Phase 4.2 (16-day forecast + background scheduler + data sources page) or Phase 5 content (crops via the ingestion pipeline).
