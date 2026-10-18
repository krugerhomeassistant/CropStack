# ACTIVE CONTEXT

**Date:** 2026-10-18 · **Version:** 0.51.0 · **Alembic head:** 0019 · **Tests:** 220 backend, browser e2e green.
History of earlier sessions: `ACTIVE_CONTEXT_ARCHIVE.md`.

## What CropStack is today
Households and garden climate (30 y Open-Meteo), 60-crop catalog (CC BY-SA, cited values), 22 pests/diseases/beneficials, jobs on **Today** (sow, set out, harvest, water, protect, check; crop-specific facts), garden planner (plot-plan map, beds/rows/pots, per-cell planting, date stepper, past sowings count as sown), **year plan** (greedy draft, replace-on-replan, Clear plan), harvest log, **Pantry**, optional assistant (Ask). Owner uses it as an iPhone home-screen PWA on ZimaOS; his wife uses Today.

## Owner and rules (from many messages)
Personal, non-commercial. Fully dynamic (no presets). Never restrict or destroy his work: only suggest. "Information is our main focus" but key points, not floods; cleaner "windows". Must look professional. English and metric only is fine. He sends many messages in a row: note each as a to-do here or in PLAN, do not stop the current work. Do not ask questions that research can answer.

## How to work (commands)
- Backend tests: `cd backend && .venv/bin/python -m pytest -q` (209 pass, ~40 s).
- Lint (do before every push): `ruff format . && ruff check .` from repo root.
- Frontend: `cd frontend && npx tsc --noEmit && npm run build`.
- Browser e2e: `npm run build` once, then `scripts/e2e-local.sh` (wipes data, restarts the stubbed server on :8512; takes ~100 s, so run it in the background with a log: `(scripts/e2e-local.sh > /tmp/e2e.log 2>&1 &)`). First run after a cold start can fail on the setup form: run again. Never run e2e on a dirty DB.
- Screenshots: `npm run screenshots` (see CI for the env vars).
- New crop: also draw `frontend/src/icons/crops/<slug>.svg` (DESIGN.md "Crop icons"); `test_every_real_crop_has_a_frontend_icon` fails without it.
- Catalog: `backend/.venv/bin/python scripts/ingest check` (needs network; the real-catalog pytest covers validity offline), `python scripts/coverage.py` (regenerate `docs/COVERAGE.md`; CI fails if stale).
- Migrations: set `CROPSTACK_DATA_DIR=/tmp/cs-mig`, `alembic upgrade head`, then `alembic revision --autogenerate` (or hand-write like 0016), name `NNNN_name.py`, revision id = number, `ruff check --fix`, bump `HEAD` in `backend/tests/test_migrations.py`.

## Release checklist
1. `python scripts/bump.py X.Y.Z`; CHANGELOG section; update README/WIKI/ARCHITECTURE/PLAN/LESSONS/this file; `python scripts/coverage.py`.
2. Tests + lint + build + e2e locally (all green) before pushing.
3. Work on a feature branch and open a PR (`gh api` REST; GraphQL is blocked in cloud sessions); wait for CI green, squash-merge to `main` (the owner has said to merge without asking again once CI is green). Commit with trailers `Co-Authored-By: Claude <model> <noreply@anthropic.com>` and the `Claude-Session:` line; `git pull --rebase`; push to `main`. A new version on main = release (CI: lint, tests, e2e, Docker image to ghcr, GitHub release; ~6 min). Poll `gh run list -L1` until `completed`.
4. Deploy to the owner: his copy is `E:\Projects\Personal\CropStack` (device bridge `$HOME/mnt/Personal/CropStack`): shallow-clone main to a temp dir, `rm -rf .git`, `cp -rT` over it (never touch his git config). He then pulls `ghcr.io/krugerhomeassistant/cropstack:latest` in ZimaOS and restarts.
5. Real-container smoke test: `docker pull` the image, run with `--network host -v /tmp/data:/data`, hit `/api/health` (needs `dockerd &` first in the sandbox; local `docker build` fails on the proxy CA, use the CI image).

## Next (owner asked, not done)
Butternut (Cucurbita moschata) in the catalog with cited values.

## Next up (priority order; specs in PLAN.md "Next up")
1. Needs model (PLAN 8.2) so the year plan sizes each crop's block to what the household eats.
2. Year plan polish: re-plan diff view; live crops keep their cells until harvested (known gap); lock a job's date.
3. Look and feel: apply the plot-plan/window style to Climate, Crops, More; map pinch-zoom/pan; move a planting between cells/beds; undo/redo.
4. Data: sow depth still an estimate for 36 crops; companions (Wikipedia CC BY-SA list); storage life per crop (USDA AH-66) for Pantry; varieties; animals catalog; more organisms.
5. Pantry link to harvest; Mealie integration (future, owner not running Mealie).
6. Home Assistant integration (MQTT/REST), assistant photo diagnosis/tools/streaming/history, encrypt API key at rest, imperial units in job text (low priority).

## Open issues / unverified
- Year plan overlap on accept fixed in 0.45.1. Re-check on the owner's real data after deploy.
- Owner's Bed 1 showed "6 cells have two plantings at once" (cause unknown: hand painting or an old plan). Ask him to check after updating to 0.40.0 and using Clear plan.
- Planner look on his phone and the year plan on real climate data are unverified by me.
- README screenshots in `docs/images/` are old (regenerate with `npm run screenshots`).
- Owner action: enable "Allow GitHub Actions to create pull requests" so the monthly catalog-refresh workflow can open PRs.
- Sandbox quirks: `gh` GraphQL is blocked (use `gh run list`, REST); the sandbox proxy resets some connections (retry); `sqlite3` CLI is missing (use python).

## Active development sequence
- [ ] Year-plan re-plan diff: preview added/removed/moved items before replacement.
- [ ] Year-plan lifecycle: preserve live crops until harvest/finish; support locked job dates.
- [ ] Flower wording: expose planting purpose so companion plants use flowering/picking language.
- [ ] Planner usability: consistent windows, map zoom/pan, move planting, undo/redo.
- [ ] Data depth: sourced depths, Pantry storage metadata, varieties, animals and organisms.
- [ ] Pantry ↔ harvest, then Mealie integration.
- [ ] Home Assistant and assistant integrations.


## v0.45.0
Plants at real size: `planting.spots` (`[x, y, w, h]` cm per plant; `cells` is their cover, `layout.cover`), made by `layout.fill` (offset rows at the crop's spacing over painted cells, avoiding other plantings) in `plantings._place`; `beds.spots_of` lays out old rows from their cells; clashes are `layout.spot_clashes` (rectangles, not cells). Year plan drafting still works in cells: `layout.Patch/patch/best_block/plants_in` (spacing in both directions -> a patch of whole cells; a block is a solid rectangle of whole patches, then `layout.stagger` offsets every other row of patches by half a patch when the free ground allows), `yearplan.draft` scores blocks by touching good companions (`COMPANION_BONUS`, `BED_COMPANION_BONUS`) and refuses beds with an "avoid" crop; flower stands go against the host block / bed edge. `taken` now carries the crop as a fifth element (so adjacency can see existing plantings); `Want.footprint` became `Want.dims`; `kept` was removed. `catalog/companions.yaml` is read in both directions with family-level expansion (363 good / 56 avoid), flowers are derived (good partners with `purpose: companion`); zinnia and petunia added; 12 crops got estimated spacings (`plant_spread`/`row_spacing`, flagged). Flowers say "pick"/"in flower" (job title, suggestions). Limits: a patch is whole cells, so a spacing that is not a multiple of the cell wastes ground (finer cells follow it more closely); odd spacings like 20 x 45 cm take a 2-cell patch for one plant; adjacency is edge-to-edge only; the avoid rule is bed-level; the Today button still says "Mark harvest started" for flowers and the planting list still says "Harvest expected". Next: per-planting `purpose` in the API so those two say "flowering"; calendula/cosmos (no pairs in the source for our crops: only worth adding with a pair source); the re-plan diff.

## v0.44.0
Six companion flowers in the catalog (`purpose: companion`, `catalog/crops/{marigold,nasturtium,borage,chamomile,alyssum,sunflower}.yaml`, added to `scripts/ingest/crosswalk.yaml`; temperatures/pH/rainfall from ECOCROP for borage, chamomile, sunflower; marigold, nasturtium, alyssum temperatures and spacing are flagged estimates; cycle_days is a hand-set sow-to-bloom estimate, not ECOCROP's seed-ripening cycle). `engine/yearplan._flower_blocks` places a 2-cell block beside crops that list the flower. Dev note: running `scripts/ingest fetch` rewrites the Harrington hash in `snapshots.lock` (the OSU page changed upstream); revert the lock unless you mean to re-ingest, and merge new files with a small script rather than `ingest merge` (it would rewrite existing crops). Next: flowers' own harvest/Today wording ("pick" not "harvest"), more flowers/herbs (calendula, cosmos, zinnia), adjacency-aware placement, the re-plan diff.

## v0.43.0
Year plan: proper spacing (plants needing more than a cell take several, kept together; `layout.cells_per_plant/plants_in`) and companion planting (`catalog/companions.yaml`, 143 good / 31 avoid pairs + flowers from Wikipedia rev 1334550406; `engine/yearplan.py` prefers beds with a good companion, refuses a bed with an avoid crop; items carry `pairs_with`, `flowers`, `cells_per_plant`). Limits: companions are a bed-level hint (no adjacency, no interplanting rows), flowers are text only (not in the catalog as plantable crops), pairs come from one list and are all `traditional`; the same crop can appear in several beds so "pairs with" can name a crop planted in another window of the season. Next: flowers/herbs as plantable catalog entries so the plan can place them, an adjacency-aware placement, the re-plan diff.

## v0.42.0
Plot plan restyle (metre grid, soil-tinted beds, crop-colour tiles, halo on selection; styling only) and always-open sign-up with "Start my own" / "Join a household" (invite still required to join; `CROPSTACK_ALLOW_REGISTRATION` default `true`, `auto` alias, `false` closes). Next on the plot plan: flat crop marks instead of emoji, per-bed fill bar, pinch-zoom/pan, tidier bed toolbar. Laptop dev (Windows): Python 3.12 venv in `backend/.venv`, set `PYTHONUTF8=1` for pytest, Node LTS via winget; the bash/Chromium e2e script is Linux-only, CI runs it.

## v0.41.0
Needs model: `people` setting, `food_group` + `yield_per_m2` on all 60 crops, demand-driven drafter, coverage card on the Plan tab. Limits: yields are estimates, harvests spread evenly, live crops hold cells only to cycle end. Next: sourced yields, setup interview 8.1, Climate/Crops/More facelift, move planting + undo.
