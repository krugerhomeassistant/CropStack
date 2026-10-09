# LESSONS LEARNED

Format: [Problem] → [Root cause] → [Verified solution]

Inherited from Bloomery (same stack; full list in that repo's `docs/LESSONS_LEARNED.md`):

1. **Tailwind v4 `@apply` of a custom class fails** → v4 only applies utilities → declare custom classes with `@utility name { … }`.
2. **Bind-mounted `/data` is root-owned on the host** → non-root app can't write → `entrypoint.sh` chowns as root, then `setpriv` drops to uid 10001.
3. **GHCR image can't be pulled by NAS dashboards** → package is private by default, separate from repo visibility → Package settings → Change visibility → Public.
4. **Tag push from the Claude sandbox returns 403** → egress policy → CI creates the tag + release itself when `main` has an unreleased version.
5. **`TestClient(app)` without `with` skips lifespan** → no tables → always use `with TestClient(app)` or call `init_db()`.
6. **`pkill -f pattern` killed the tool shell** → pattern in its own command line → stop servers with `fuser -k PORT/tcp`; start with `setsid nohup … &`.
7. **Chaining with `;` committed despite lint failure** → chain lint, tests and commit with `&&`.
8. **strftime `%-d` is glibc-only** → breaks on Windows → format with `d.day`.
9. **`starlette.testclient` warns to use `httpx2`** → harmless deprecation; revisit on a Starlette upgrade.

CropStack-specific:

10. **vite-plugin-pwa 2.0.0 (new major)** → builds cleanly with Vite 8.3.4 and the same config as Bloomery's 1.3 → no changes needed (verified 2026-10-09).
11. **Git in a connected Windows folder (device bridge) fails with `config.lock: File exists`** → git deletes its lock files and deletion is off by default there → clone/commit outside the mount, then `cp -r` into it; deliver later changes the same way or ask for delete permission.
12. **Copied repo shows every file as modified** → Windows mount has no exec bits → `git config core.fileMode false` (Windows Git's default anyway).
13. **GitHub repo created with a LICENSE commit** → local history unrelated → `git rebase -X ours origin/main` before the first push.
14. **`npm i playwright` pulled a newer browser build than /opt/pw-browsers has** → `chromium.launch({ executablePath: '/opt/pw-browsers/chromium' })`.
15. **ZimaOS 1.7 doesn't always notice new `:latest` images** (community-reported) → open the app → Save without changes to re-pull; `docker pull` first if needed.
16. **Browser geolocation fails on a LAN `http://` install** → requires a secure context → manual lat/long fields stay first-class; postal-code geocoding comes in Phase 2.

17. **ZimaOS showed host port `-8430}`** → user imported the generic `docker-compose.yml`; the ZimaOS importer doesn't expand `${CROPSTACK_PORT:-8430}` → import `docker-compose.zimaos.yml` (plain values); header comment in `docker-compose.yml` now says so.
18. **Open-Meteo "Daily API request limit exceeded" from the sandbox** → the cloud sandbox shares its IP with others → test with synthetic fixtures (`tests/test_climate.synthetic`); real calls run from the user's server with its own quota.
19. **WebFetch refused archive-api.open-meteo.com (robots)** → verify API shape from the open-source server code instead (sparse clone of `open-meteo/open-meteo`, grep `Sources/App`).
20. **Open-Meteo geocoding returned nothing for SA postal code `0081`** → its geocoder is name-based (GeoNames) → Nominatim `q=` finds postcodes.
21. **Nested `<form>` (place search inside garden form)** → invalid HTML, inner form ignored → plain div + button `type="button"` + Enter key with `preventDefault`.
22. **Playwright `getByText('Your climate')` matched the loading text** → `getByText` is case-insensitive substring by default → wait for a unique final element (`/^Zone /`).
23. **Zone test values on a boundary** (−17.78 °C = −0.004 °F → 6b, not 7a) → pick test temperatures inside a half-zone, not on its edge.
24. **Day lengths at ±latitude don't sum to 24 h** → refraction (−0.833°) lengthens both → ~24.7 h at 60°; test ranges, not symmetry.
25. **Climate card was frost-centric; user in the Western Cape barely gets frost** → designed from a northern/US gardening frame (frost dates as the anchor) → lead with what limits the garden locally (rain season, heat), show frost only where it occurs in ≥ 50 % of years; plan crop calendars from temperature windows, not frost offsets. Ask "what limits your garden?" before anchoring a feature on one hazard.
26. **Feature design drifted toward fixed heuristics (hot ≥ 30 °C, frost headline if ≥ 50 % of years)** → convenient constants are presets in disguise; user wants fully dynamic behaviour → SPEC P1/P2: every decision = requirement profile × environment data; thresholds belong to subjects (crop/animal), never to the app.
27. **Built the analysis view as the home screen** → developer interest ≠ household need; the user's wife wants "what do I do today" → SPEC P9 action first; per-user start screen; ask who uses each screen.
28. **Alembic batch migration on SQLite deleted child rows** → batch mode rebuilds a table (copy, drop, rename); with `PRAGMA foreign_keys=ON`, dropping `user` cascade-deleted every `garden` (reproduced) → run migrations with foreign keys OFF (outside a transaction, then `commit()` before `begin()`), turn back ON after; regression test `test_table_rebuild_during_migration_does_not_cascade_delete`.
29. **`git checkout -- file` to undo a deliberate break also reverted my uncommitted work in that file** → never use checkout/restore to undo an experiment on a file with uncommitted changes → copy the file aside first (`cp f /tmp/f.good`) and copy it back.
30. **Autogenerate turned a table rename into drop + create (garden → site)** → Alembic can't detect renames → always read autogenerated revisions; write data moves by hand (`INSERT … SELECT`) and test against real old schemas (fixtures from `git archive <tag>`).
31. **React Router 8 removed `react-router-dom`** → import everything from `react-router` (DOM bits from `react-router/dom`); needs React ≥ 19.2.7 and Node ≥ 22.22.
32. **Settings radios jumped back after a click** → controlled by the server value, which only changed after save + reload → keep a local optimistic copy, revert on error.
33. **Playwright `count()` right after a nav click returned 0** → `count()` doesn't wait → wait for the destination's heading first, then count.
34. **Syncing the E: copy with `cp -rT fresh_clone E:\…\CropStack` left a deleted file behind (`Home.tsx`)** → copy only adds/overwrites; deletion is off in connected folders → after each sync run `git status --short` there and move `??` leftovers into `E:\Projects\Personal\_to_delete\` (user deletes).
35. **FAO licence looked like CC BY-NC-SA 3.0 IGO / "no CC before 2018"** → those rules are FAO's *publications* policy; datasets follow the Statistical DB Terms and each dataset's own metadata → check the FAO Data Catalog record (`data.apps.fao.org/catalog/api/3/action/package_show?id=<name>`): ECOCROP is CC BY 4.0, plus FAO's no-promotion/no-endorsement terms.
36. **OpenFarm data licence unclear; no official dump** → README "Data License" section says CC0; site gone since 2025-04-21 → use the CC0 rescue repo (340 crops from Wayback) as a scaffold, mark values `grower-reported`.
37. **GitHub web/API pages blocked from research agents** → egress policy → read via `raw.githubusercontent.com` or a shallow `git clone`.
38. **Most practical growing knowledge (extension guides, ARC, UC IPM) is copyrighted** → only facts are free → store single cited values, write prose fresh, never mirror a list or table layout (EU/UK database right; SA compilation copyright).
39. **After updating to v0.5.0 the user saw "Cannot reach the CropStack server"** → the PWA served the cached v0.4 app, which called removed `/api/auth/*` paths (404) and reported every failure as unreachable; "Try again" re-ran the old code → reproduced with a persistent Playwright profile + Docker images 0.4.0 → latest (self-heals after ~5 s when the new service worker takes over). Fix: on failure check `/api/health`, reload once if the server version ≠ build version, real error messages, "Try again" = full reload. Rule: API-breaking changes need a version bump.
40. **Docker works in this sandbox** (`dockerd &`, then `docker run` the published GHCR images) → test upgrades against the real images, not only the source tree.
41. **Weighted median came out as 3.25 for values 1 (weight 3) and 10 (weight 1)** → interpolating between weight-block midpoints → use the weighted inverse CDF (smallest value whose cumulative weight passes q; average only on an exact boundary).
42. **Test series "value = year" was rewritten to 2025 everywhere** → a variable equal to its year is a perfect warming trend, and trend adjustment shifted all years to today → test windowing with a non-trend-adjusted variable (rain).
43. **Synthetic test climates ending in a fixed year (2024) looked stale in 2026** → the archive refreshes when a newer complete year exists → generate fixtures relative to `date.today()` (last 30 complete years), like the real fetch.
44. **The rare "1 error" in the test suite (seen in 3.3) was a username collision** → household tests built usernames from `id(client)`, and CPython reuses addresses of freed objects → generate unique names with `uuid4()` in tests that share one database; never use `id()` as an identifier across objects' lifetimes.
45. **Image would have looked for the catalog at `/catalog`** → default path derived from `__file__` (`parents[2]`) is the repo root in dev but `/` in the image (`/app/app/config.py`) → set `CROPSTACK_CATALOG_DIR=/app/catalog` in the Dockerfile and test the built image.
46. **Playwright `getByLabel('Weather')` matched the loading skeleton ("Loading the weather")** → label matching is substring and case-insensitive → wait for an element that only exists when loaded (`getByRole('list', { name: 'Next 7 days' })`).
47. **"drier than 10 in 10 years"** → percentile wording breaks at the extremes → say "almost every year on record" beyond the 95th/5th percentile.
48. **Background job touched other households in tests** → the scheduler refreshes all sites → assert on the household's own rows, not on global call counts; tests disable the scheduler (`CROPSTACK_SCHEDULER=false`) so nothing calls outside services.
49. **`pkill -f fake_server2` killed the Bash tool's own shell (exit 144)** → `-f` matches the full command line, which contained the pattern → find the PID with `pgrep -f "python /path/fake…"` and `kill <pid>`, or keep the server's PID when starting it.
50. **Screenshots showed the old user after "restarting" the fake server** → the old process still held port 8512, the new one failed to bind and the script talked to the old one → check `pgrep`/the server log before trusting a rerun.
51. **README and wiki drifted far behind the app (user, 2026-10-09)** → they were only patched per feature, never reread → review both on every release (in the release checklist, WIKI → Release process).
52. **`pgrep -f "python /tmp/…/fake" | xargs kill` killed the Bash tool's shell again (exit 144)** → the pattern also matches the shell running that very command line → start background servers with `nohup … & echo $! > server.pid` and stop them with `kill $(cat server.pid)`; never match by command line from the same shell.
53. **E2E `getByText('Marie')` matched the name, `@marie` and the sr-only "Role for Marie" label** → text locators are substring matches across visible and screen-reader text → wait on a unique string (`@marie`) or use `{ exact: true }`.
54. **A test request to the Wikidata API went out with the owner's email in the User-Agent** → copied the "contact in UA" convention without thinking → User-Agents carry only the project name and repo URL (`fetch.USER_AGENT`); never put the owner's email or other personal data in requests to outside services.
55. **The OSU Harrington page has a typo in an optimum range ("45–5")** → hand-made tables contain errors → extractors validate ordering and skip bad rows; only min/opt/max (which were consistent) are imported.
56. **GBIF reports *Pisum sativum* as a SYNONYM** → GBIF follows the move to *Lathyrus oleraceus* → keep the name gardeners use and record the expected status in `crosswalk.yaml` (`gbif_status`), so `check` stays green but the exception is visible.
57. **YAML dump wrote `&id001` anchors for repeated dates** → PyYAML aliases identical objects → custom dumper with `ignore_aliases()`.
58. **Network from the sandbox, 2026-10-09**: raw.githubusercontent, GBIF API, OSU, CRAN and Zenodo reachable; Wikidata API reachable with an identifying UA (429 without); Wikidata SPARQL endpoint blocked.
52. **`pkill -f <name>` killed the shell again (exit 144), a repeat of 49** → never use `pkill -f` from the Bash tool; `P=$(pgrep -f "python -m <module>" | head -1); [ -n "$P" ] && kill $P`.
53. **Chart axis text rendered at ~5 px on a phone** → an SVG with a fixed 640×240 viewBox scales everything down with the width → size the drawing to its container (ResizeObserver) so text stays 11 px.
54. **Dark-mode chart colours failed the dataviz validator** → text tokens (`water`, `harvest`) are tuned for text contrast, but dark charts need L 0.48–0.67 and chroma ≥ 0.1 → separate chart tokens validated with `validate_palette.js --mode dark --surface <app surface>`.
55. **Playwright hover missed a chart below the fold** → `boundingBox()` is viewport-relative and does not scroll → `scrollIntoViewIfNeeded()` first.
56. **Several rain bars labelled as the maximum** → `v === max` is true for ties → label by the index of the first maximum.
57. **ECOCROP's KTMP (killing temperature) is 0 for tomato** → 0 means both a real 0 °C and "not given" in this table → do not import it; take frost limits from curated or other sources.
58. **ECOCROP rainfall looked like "per growing cycle"** → Recocrop's docs say the FAO database holds *annual* precipitation (Recocrop divides it into monthly figures itself) → read the consuming code's docs before naming a field; the field is `annual_rainfall`.
59. **The catalog model rejected ECOCROP's four-point ranges** → `Range` had min/opt/max only → extended with `opt_min`/`opt_max`; the model gate caught it before bad data landed.
60. **`pyreadr` imports but fails ("requires pandas or polars")** → it has no hard dependency on a dataframe library → install pandas as well; the CLI error now says so.
61. **ECOCROP names are old (tomato is *Lycopersicon esculentum*)** → name matching misses → crosswalk by `CODE`, checked by eye against the scientific name.
62. **`rsync` is not installed in the sandbox** → restore a directory from git with `git checkout -- <dir>` when it has no other uncommitted changes.
63. **A new test registered a username another test had already used (409)** → API tests share one database within the run → use a unique username per test.
64. **E2E/screenshots against a leftover stub server showed old results or refused connections** → an earlier server still held the port → stop it by PID (`pgrep` + `kill`), wipe `/tmp/cs-e2e`, restart with `--port 8512`, and pass `CROPSTACK_URL` and `CHROMIUM_PATH=/opt/pw-browsers/chromium`.
65. **CI lint failed on `scripts/coverage.py` though local ruff passed** → I ran ruff from `backend/`, which skips the repo-root `scripts/` → run `ruff check . && ruff format --check .` from the repo root, as CI does.
66. **`kill` of the stub server silently did nothing, so e2e ran against stale data or timed out** → `ss` is not installed, so the PID lookup came back empty → find the process by scanning `/proc/*/cmdline` (never `pkill -f` or a `pgrep -f` pattern that also matches your own shell command, which kills the shell with exit 144), and confirm the log says "Uvicorn running".
67. **A POST response lost every field after the handler called a helper that commits** → `commit()` expires ORM attributes, so FastAPI serialised an empty object → call `db.refresh(row)` after the last commit.
68. **Autogenerated migrations need the database at head** ("Target database is not up to date") → point `CROPSTACK_DATA_DIR` at a scratch dir, `alembic upgrade head`, then `alembic revision --autogenerate`; rename the file to the next `000N_name.py` and fix `revision`/`down_revision` (and set the test HEAD).
