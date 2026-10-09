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
