# Security policy

CropStack stores your garden's location and, once integrations land, Home Assistant and AI credentials, so security reports are taken seriously.

## Reporting a vulnerability

Please **don't open a public issue**. Report it privately via
[GitHub security advisories](https://github.com/krugerhomeassistant/CropStack/security/advisories/new).
You'll get a reply within a week, and a fix in the next release for confirmed issues.

## Supported versions

Only the latest release receives fixes. Update with `docker compose pull && docker compose up -d`.

## Design notes

- All data stays in your SQLite file (`/data`). Outbound requests: garden coordinates to Open-Meteo (climate, once per location) and place-search text to OpenStreetMap Nominatim (only when you search). Future weather, AI and notification integrations will be opt-in.
- The container runs as an unprivileged user (uid 10001).
- Run CropStack behind HTTPS (or a private network such as Tailscale) when it's reachable from outside your home, and set `CROPSTACK_SECURE_COOKIES=true`.
