# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.20.0

## Current subtask
v0.20.0 (soil question; watering uses it) released after CI; v0.19.0 Water jobs, v0.18.0 Protect jobs, v0.17.0 the task engine and Today jobs. Owner confirmed (2026-10-09) live weather works on the ZimaOS install. Next: rest of the setup interview (space, water source, household, time, budget), per-job how-to text, 6.6 feeding, 6.7 scouting, then hardening-off and successions; Today weather advice and the how-to text per job. Process note: `ss` is missing in the sandbox; find the stub server by scanning /proc (see /tmp/restart.sh pattern) and run e2e and screenshots against separate fresh data dirs.

## Open to-dos (owner: "make note of missed/still to dos")
- UI kit: Sheet/Dialog, Tabs, Toast, Select. Add with the first screen that needs them (PLAN 6.9).
- Climate charts v2 (PLAN 11): ET0, user-picked threshold curves, trend, this-season overlay, sensor overlay, takeaway sentence, attribution line; add the chart rules to `docs/DESIGN.md`. Chart tests: unit tests for the pure helpers if they grow.
- Catalog (PLAN 5): fetchers v2b (DSSAT, Wikidata Afrikaans, WFO, USDA PLANTS, EPPO, Wikipedia companions; ECOCROP is done); monthly CI job opening a PR with the YAML diff; prose-similarity CI check; herbs and the rest of the 60 crops; varieties (≥ 2 per crop); 20 fruit species; 5 cover crops; 40 organisms; override editor and custom crops.
- Done: the owner confirmed weather data pulls correctly on the ZimaOS install (2026-10-09).
- Waits for Home Assistant work: 4.3 sensors and observations.

- **Owner request 2026-10-09 (mid-Phase 6): global contribution + perpetual data collection.** Way for anyone to add plants/animals/values (PRs to `catalog/`; issue forms for "request a species" and "report a value"; a contributor guide with the YAML schema, sources and licence rules; CI that validates schema, sources and prose similarity on every PR) and a collection loop that never stops (monthly scheduled ingest job opening a PR with the YAML diff; a coverage report listing crops/animals still missing values; a "needs data" label queue). DONE in v0.14.0 (guide, issue forms, PR template, coverage report, monthly refresh workflow, in-app link). Still open: prose-similarity CI check, fetchers v2b; first real run of the monthly workflow needs the owner to enable Actions PR creation (repo Settings → Actions → "Allow GitHub Actions to create pull requests").

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
