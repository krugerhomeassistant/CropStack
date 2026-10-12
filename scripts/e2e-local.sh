#!/usr/bin/env bash
# Run the browser tests locally against a fresh stubbed server (no network needed).
# Usage: scripts/e2e-local.sh   (needs `npm ci` in frontend/, a built frontend/dist, and backend/.venv)
# A dirty database makes e2e fail, so the server is always restarted on a wiped data dir.
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
for d in /proc/[0-9]*; do  # `ss`/`pkill -f` are unreliable in the sandbox: match the command line directly
  pid=${d#/proc/}; [ "$pid" = "$$" ] && continue
  tr '\0' ' ' < "$d/cmdline" 2>/dev/null | grep -q "python.* -m tests.e2e_server --port 8512 $" && kill "$pid" || true
done
sleep 2; rm -rf /tmp/cs-e2e
(cd "$root/backend" && CROPSTACK_DATA_DIR=/tmp/cs-e2e CROPSTACK_STATIC_DIR=../frontend/dist CROPSTACK_SCHEDULER=false \
  nohup .venv/bin/python -m tests.e2e_server --port 8512 >/tmp/e2e.log 2>&1 &)
for _ in $(seq 40); do curl -sf http://127.0.0.1:8512/api/health >/dev/null && break; sleep 1; done
sleep 5  # the first run after a cold start can time out on the setup form: just run again
cd "$root/frontend" && CROPSTACK_URL=http://127.0.0.1:8512 CHROMIUM_PATH=${CHROMIUM_PATH:-/opt/pw-browsers/chromium} npm run e2e
