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
