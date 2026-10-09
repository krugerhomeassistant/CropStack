# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.6.0

## Current subtask
Phase 4.1 + 4.4 released as v0.6.0: analog-year environment engine (`environment.py`), raw climate archive per site (migration 0004), probability/bands endpoints, climate card rewritten to describe data without fixed rules, AC-P1 no-presets test.

## Last execution results
- Backend 61/61 (+ no-presets check), ruff clean, frontend build OK; Playwright: one card for a Western-Cape-like and a frosty synthetic climate, frost dates only where frost occurs at the risk level, no page errors.
- v0.5.1 (earlier today): stale cached app after update now reloads itself (LESSONS 39–40).
- Real Open-Meteo responses still unverified from the sandbox (shared IP over quota); the user's install will make the first real call with 7 variables.

## Handoff to the implementing session
- Pull `main` first; then read, in order: this file, SPEC §6.1, §16, §16.1, PLAN 3.4 / Phase 5 / 9.1, `docs/research/catalog-data-sources.md` (decisions + source table), `docs/research/notes/*.md` (per-domain evidence: cited values, URLs, licence quotes, gaps).
- Treat `licence_conflicts_resolved.md` as overriding the other notes where they disagree.
- Values marked "unverified" in the notes must not be bundled until checked.

## Blockers
- None. Open: SPEC §19 Q6 (ask ARC-VOPI for reuse permission?); user may veto CC BY-SA 4.0 for the catalog.

## Immediate next step
Phase 3.4 catalog infrastructure (schemas, loader, overrides, provenance, `catalog/LICENSE` + `NOTICE`, licence gate) per SPEC §16.1 and the research handoff above; then Phase 4.2 (forecast + scheduler). Open user decisions unchanged: CC BY-SA 4.0 veto? ARC permission request?
