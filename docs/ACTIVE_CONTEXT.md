# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.8.0

## Current subtask
Phase 4.2 (forecast, scheduler, data sources) done, target v0.8.0. Remaining Phase 4: 4.3 calibration hooks (sensors, observations).

## Last execution results
- Backend 86/86, ruff clean, frontend build OK. Playwright: Today weather card (light + dark), data-source switches (toggle style), forecast off hides the card, place search off hides search. CI image verified: `forecast` job runs ~60 s after start, failure recorded in `/api/health` (sandbox proxy cert), container stays healthy.
- v0.7.0 released earlier today (catalog foundation).

## Handoff to the implementing session
- Pull `main` first; then read, in order: this file, SPEC §6.1, §16, §16.1, PLAN 3.4 / Phase 5 / 9.1, `docs/research/catalog-data-sources.md` (decisions + source table), `docs/research/notes/*.md` (per-domain evidence: cited values, URLs, licence quotes, gaps).
- Treat `licence_conflicts_resolved.md` as overriding the other notes where they disagree.
- Values marked "unverified" in the notes must not be bundled until checked.

## Standing requirements
- **Professional look and feel** (owner, 2026-10-09): "just for me" is about licensing only. Design system (PLAN 6.9) comes before the Today screen; every changed screen gets a visual check in light/dark and phone/desktop before release.

## Blockers
- None. Decided 2026-10-09 (user: personal, non-commercial use; repo stays public): public `catalog/` = CC BY-SA 4.0; no ARC request for now; personal-use values go in a private pack on the server (SPEC §16.1, §19 Q6–7).

## Immediate next step
4.3 (sensor + observation tables, manual entry, bias fit) or Phase 6.9 design system → 5 catalog content → 6 crop engine → 7 Today tasks.
