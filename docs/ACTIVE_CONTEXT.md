# ACTIVE CONTEXT

**Date:** 2026-10-10 · **Version:** 0.27.0

## Current subtask
**v0.27.0 shipped the four items below (cells, staggering, recommendations); follow-ups: edit a planting's dates/quantity inside the bed card, move a planting between cells, Today jobs naming cells, rotation warnings in the grid, recommendation cache and perennials.** Owner feedback 2026-10-10 on the v0.26 garden plan: (1) specify exactly what goes where: per-cell placement inside a bed; (2) mixed and staggered beds: one bed, row or pot holds several crops in any order, in succession over time; (3) easy to customise and wired into jobs, crowding and rotation; (4) show recommendations of what to plant, when and where. Plan: cells per bed (`bed.cell_cm`), `planting.cells`, date-aware occupancy and conflicts, `GET /recommendations`, a bed editor with a crop palette, painting and a date slider. **Owner request 2026-10-10: "add the garden planner part".** v0.26.0 is the first slice (PLAN 8.3): beds as objects, SVG plan with drag, planting-to-bed, overcrowding. Still open in 8.3: undo/redo, rotate, polygon and keyhole beds, structures, paths, trees and shade (sun model), rulers, per-plant placement with a date slider, rotation conflicts, auto-layout from the plan generator, export and print. Then 8.1 setup interview, 8.2 needs, 8.4 plan generator. v0.25.0: organisms have `hosts` (crop slugs; empty = any) and Check jobs filter by the planting's crop. v0.24.0: weekly Check jobs (`kind=check`, template how-to-check) show all organisms; no host links yet so the list is not crop-specific. Next: host links per crop, more organisms, feeding, setup interview. v0.22.0 released (the Docker Hub 429 cleared on re-run). v0.23.0: first 9 organisms in `catalog/organisms/` (facts fetched from UC IPM pages 2026-10-10 after the owner accepted the permission prompt; hornworm cocoon claim dropped because the page did not support it). Next: scouting "Check" jobs from these entries, more organisms (late blight needs a registered source for the Hutton rule; AHDB), then feeding and the setup interview. v0.22.0 harvest logging shipped (table 0010, API, Garden UI, e2e). v0.21.0 CI failed on the screenshots script (fixed in 1a33d87). v0.20.0 (soil question; watering uses it) released after CI; v0.19.0 Water jobs, v0.18.0 Protect jobs, v0.17.0 the task engine and Today jobs. Owner confirmed (2026-10-09) live weather works on the ZimaOS install. Next: rest of the setup interview (space, water source, household, time, budget), crop-specific how-to text (generic per-kind steps shipped in v0.21.0), 6.6 feeding, 6.7 scouting, then hardening-off and successions; Today weather advice and the how-to text per job. Process note: `ss` is missing in the sandbox; find the stub server by scanning /proc (see /tmp/restart.sh pattern) and run e2e and screenshots against separate fresh data dirs.

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
Phase 5 catalog content (ingestion pipeline, following the handoff reading order above) → 6 crop engine → 7 Today tasks. Live weather confirmed working on the ZimaOS install. 4.3 (sensors, observations) waits for Home Assistant work.
