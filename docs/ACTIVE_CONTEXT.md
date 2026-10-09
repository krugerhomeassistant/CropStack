# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.9.0

## Current subtask
Phase 6.9 design system done, released as v0.9.0 together with the README and WIKI rewrite.

## Last execution results
- All pages and components moved to the UI kit and tokens; desktop rail ≥ 1024 px; Today two columns on desktop; designed empty states for Today jobs and Garden beds. `npm run screenshots` reviewed (24 images, light/dark × phone/desktop). Build and type check clean.
- README rewritten (what works now vs roadmap, screenshots in `docs/images/`), WIKI rewritten against the current code.

## Handoff to the implementing session
- Pull `main` first; then read, in order: this file, SPEC §6.1, §16, §16.1, PLAN 3.4 / Phase 5 / 9.1, `docs/research/catalog-data-sources.md` (decisions + source table), `docs/research/notes/*.md` (per-domain evidence: cited values, URLs, licence quotes, gaps).
- Treat `licence_conflicts_resolved.md` as overriding the other notes where they disagree.
- Values marked "unverified" in the notes must not be bundled until checked.

## Standing requirements
- **README and WIKI current** (owner, 2026-10-09: "extremely outdated"; rewritten in v0.9.0): reread and update both on every release, and refresh `docs/images/` when screens change.
- **Professional look and feel** (owner, 2026-10-09): "just for me" is about licensing only. Design system (PLAN 6.9) comes before the Today screen; every changed screen gets a visual check in light/dark and phone/desktop before release.

## Blockers
- None. Decided 2026-10-09 (user: personal, non-commercial use; repo stays public): public `catalog/` = CC BY-SA 4.0; no ARC request for now; personal-use values go in a private pack on the server (SPEC §16.1, §19 Q6–7).

## Immediate next step
Phase 5 catalog content (ingestion pipeline, following the handoff reading order above) → 6 crop engine → 7 Today tasks. Still open from the owner: real climate and forecast values from the ZimaOS install (first real Open-Meteo call). 4.3 (sensors, observations) waits for Home Assistant work.
