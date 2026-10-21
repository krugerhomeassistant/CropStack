# ACTIVE CONTEXT

**Date:** 2026-10-21 · **Version:** 0.54.0 · **Alembic head:** 0020 · **Tests:** 228 backend, browser e2e green.
History of earlier sessions: `ACTIVE_CONTEXT_ARCHIVE.md`.

## What CropStack is today
Households and garden climate (30 y Open-Meteo), 60-crop catalog (CC BY-SA, cited values), 22 pests/diseases/beneficials, jobs on **Today** (sow, set out, harvest, water, protect, check; crop-specific facts), garden planner (plot-plan map, beds/rows/pots, per-cell planting, date stepper, past sowings count as sown), **year plan** (greedy draft, replace-on-replan, Clear plan), harvest log, **Pantry**, optional assistant (Ask). Owner uses it as an iPhone home-screen PWA on ZimaOS; his wife uses Today.

## Owner and rules (from many messages)
Personal, non-commercial. Fully dynamic (no presets). Never restrict or destroy his work: only suggest. "Information is our main focus" but key points, not floods; cleaner "windows". Must look professional. English and metric only is fine. He sends many messages in a row: note each as a to-do here or in PLAN, do not stop the current work. Do not ask questions that research can answer.

## How to work (commands)
- Backend tests: `cd backend && python -m pytest -q` (228 pass, ~80 s; venv in the cloud sandbox: `/tmp/csvenv`).
- Lint (do before every push): `ruff format . && ruff check .` from repo root.
- Frontend: `cd frontend && npx tsc --noEmit && npm run build`.
- Local e2e in the sandbox: kill any old server first, `rm -rf /tmp/claude-0/e2edata`, then `cd backend && CROPSTACK_DATA_DIR=/tmp/claude-0/e2edata CROPSTACK_STATIC_DIR=../frontend/dist CROPSTACK_SCHEDULER=false python -m tests.e2e_server --port 8512 &` and `cd frontend && CROPSTACK_URL=http://127.0.0.1:8512 CHROMIUM_PATH=/opt/pw-browsers/chromium npm run e2e` (fresh data each run).
- Browser e2e (his machine): `npm run build` once, then `scripts/e2e-local.sh` (wipes data, restarts the stubbed server on :8512; takes ~100 s, so run it in the background with a log: `(scripts/e2e-local.sh > /tmp/e2e.log 2>&1 &)`). First run after a cold start can fail on the setup form: run again. Never run e2e on a dirty DB.
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

## Where we are (2026-10-21, v0.54.0)
Shipped this stretch: setup wizard, wanted crops, buy-by seed list, household reset, Arrange v2 (icon selector, whole bed / section / amount linked, scatter/rows/columns, companions, preview, plants never overlap, Fix overlaps), butternut, stage selector, Place in bed, harvest windows capped at the catalogued cycle (planting and year plan), icons for all 22 organisms plus hen and bee, **Animals v0** (coop shape on the plan, flocks, egg log, Animals page under More). The owner confirmed on his phone that the beetroot dates and the drafter look right.

## Owner asks, not done (priority order)
1. **The year-plan drafter is his source of truth.** Keep checking its dates and amounts against what he sees. The heat model (`phenology`, GDD at a 20 °C reference) runs slow for cool-season crops; v0.53.2/.3 only cap its answer at the catalogued cycle. A proper fix re-fits the model or the cycle data per crop.
2. **Animals, next slices:** catalog species and breeds for hens and bees (cited or `estimate: true`; replaces the 0.4 + 1.0 m² per hen guess in `routers/flocks.py`), animal jobs on Today (coop cleaning, health checks), bees, other animals. Icons exist in `frontend/src/icons/animals/` (hen, bee; add more in the same style).
3. **Data, once-off and shipped as defaults** (his words: gather, scrape or write from our own knowledge, then the user's edits win). Nothing is fetched at run time. Work list: `docs/COVERAGE.md` (empty and estimated fields, crop by crop, starting with beetroot, butternut, lettuce, tomato); butternut sow depth, pH, yield, spacing; storage life per crop for Pantry; South African varieties; more organisms. User changes are overrides (`cat.effective`), they never rewrite the shipped files.
4. **Crops missing from his vegetable list:** he has not named them yet; ask once, then add each with cited values and an icon.
5. Show the organism and animal icons in the UI (pests on crop pages and Today, hens on the plan), now that the art exists.
6. Small: the setup wizard crop pick now uses `CropSelect`; Arrange only logs eggs for today; no per-day egg history yet.

## Next up (roadmap, PLAN.md "Next up" has the specs)
Seed vault quantities and germination tests; plot plan background image; re-plan diff view; lock a job's date; Climate/Crops/More window style; map pinch-zoom/pan; move a planting; undo/redo; Pantry link to harvest; Home Assistant (MQTT/REST); assistant photo diagnosis; encrypt the API key at rest; Mealie (he does not run it).

## Open issues / unverified
- Still unchecked on his phone: Arrange v2 end to end, Fix overlaps on his Bed 5, the coop shape and Animals page (v0.54.0).
- Stale jobs: harvest dates live in `Task` rows; after a release that changes the logic they update only when jobs refresh (the "tasks" scheduler job runs shortly after start, then every 12 h; any planting edit refreshes too). If he reports an old date after an update, ask him to wait a few minutes or touch the planting before debugging.
- Owner action: enable "Allow GitHub Actions to create pull requests" so the monthly catalog-refresh workflow can open PRs.
- Sandbox quirks: `gh` GraphQL is blocked (use REST via `gh api`); the proxy resets some connections (retry); `sqlite3` CLI is missing (use python); never `pkill -f` a pattern that also appears in your own command line (it kills the shell, exit 144): kill by `pgrep -f "python -m tests[.]e2e_server"` in its own call.
- Not CropStack: the "Murmur"/JustAnotherSim sim-mode messages in this chat belong to another project; ignore them here.

## v0.45.0
Plants at real size: `planting.spots` (`[x, y, w, h]` cm per plant; `cells` is their cover, `layout.cover`), made by `layout.fill` (offset rows at the crop's spacing over painted cells, avoiding other plantings) in `plantings._place`; `beds.spots_of` lays out old rows from their cells; clashes are `layout.spot_clashes` (rectangles, not cells). Year plan drafting still works in cells: `layout.Patch/patch/best_block/plants_in` (spacing in both directions -> a patch of whole cells; a block is a solid rectangle of whole patches, then `layout.stagger` offsets every other row of patches by half a patch when the free ground allows), `yearplan.draft` scores blocks by touching good companions (`COMPANION_BONUS`, `BED_COMPANION_BONUS`) and refuses beds with an "avoid" crop; flower stands go against the host block / bed edge. `taken` now carries the crop as a fifth element (so adjacency can see existing plantings); `Want.footprint` became `Want.dims`; `kept` was removed. `catalog/companions.yaml` is read in both directions with family-level expansion (363 good / 56 avoid), flowers are derived (good partners with `purpose: companion`); zinnia and petunia added; 12 crops got estimated spacings (`plant_spread`/`row_spacing`, flagged). Flowers say "pick"/"in flower" (job title, suggestions). Limits: a patch is whole cells, so a spacing that is not a multiple of the cell wastes ground (finer cells follow it more closely); odd spacings like 20 x 45 cm take a 2-cell patch for one plant; adjacency is edge-to-edge only; the avoid rule is bed-level; the Today button still says "Mark harvest started" for flowers and the planting list still says "Harvest expected". Next: per-planting `purpose` in the API so those two say "flowering"; calendula/cosmos (no pairs in the source for our crops: only worth adding with a pair source); the re-plan diff.

## v0.44.0
Six companion flowers in the catalog (`purpose: companion`, `catalog/crops/{marigold,nasturtium,borage,chamomile,alyssum,sunflower}.yaml`, added to `scripts/ingest/crosswalk.yaml`; temperatures/pH/rainfall from ECOCROP for borage, chamomile, sunflower; marigold, nasturtium, alyssum temperatures and spacing are flagged estimates; cycle_days is a hand-set sow-to-bloom estimate, not ECOCROP's seed-ripening cycle). `engine/yearplan._flower_blocks` places a 2-cell block beside crops that list the flower. Dev note: running `scripts/ingest fetch` rewrites the Harrington hash in `snapshots.lock` (the OSU page changed upstream); revert the lock unless you mean to re-ingest, and merge new files with a small script rather than `ingest merge` (it would rewrite existing crops). Next: flowers' own harvest/Today wording ("pick" not "harvest"), more flowers/herbs (calendula, cosmos, zinnia), adjacency-aware placement, the re-plan diff.

## v0.43.0
Year plan: proper spacing (plants needing more than a cell take several, kept together; `layout.cells_per_plant/plants_in`) and companion planting (`catalog/companions.yaml`, 143 good / 31 avoid pairs + flowers from Wikipedia rev 1334550406; `engine/yearplan.py` prefers beds with a good companion, refuses a bed with an avoid crop; items carry `pairs_with`, `flowers`, `cells_per_plant`). Limits: companions are a bed-level hint (no adjacency, no interplanting rows), flowers are text only (not in the catalog as plantable crops), pairs come from one list and are all `traditional`; the same crop can appear in several beds so "pairs with" can name a crop planted in another window of the season. Next: flowers/herbs as plantable catalog entries so the plan can place them, an adjacency-aware placement, the re-plan diff.

## v0.42.0
Plot plan restyle (metre grid, soil-tinted beds, crop-colour tiles, halo on selection; styling only) and always-open sign-up with "Start my own" / "Join a household" (invite still required to join; `CROPSTACK_ALLOW_REGISTRATION` default `true`, `auto` alias, `false` closes). Next on the plot plan: flat crop marks instead of emoji, per-bed fill bar, pinch-zoom/pan, tidier bed toolbar. Laptop dev (Windows): Python 3.12 venv in `backend/.venv`, set `PYTHONUTF8=1` for pytest, Node LTS via winget; the bash/Chromium e2e script is Linux-only, CI runs it.

## v0.41.0
Needs model: `people` setting, `food_group` + `yield_per_m2` on all 60 crops, demand-driven drafter, coverage card on the Plan tab. Limits: yields are estimates, harvests spread evenly, live crops keep their cells until finished. Next: sourced yields, setup interview 8.1, Climate/Crops/More facelift, move planting + undo.
