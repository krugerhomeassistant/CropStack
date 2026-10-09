#!/bin/sh
# Fix ownership of bind-mounted /data (often created root-owned by the host), then drop to uid 10001.
set -e
if [ "$(id -u)" = "0" ]; then
  mkdir -p "$CROPSTACK_DATA_DIR"
  chown -R cropstack:cropstack "$CROPSTACK_DATA_DIR"
  exec setpriv --reuid=cropstack --regid=cropstack --init-groups "$@"
fi
exec "$@"
