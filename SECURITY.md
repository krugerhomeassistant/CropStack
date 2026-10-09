# Security policy

CropStack stores your garden's location and, once integrations land, Home Assistant and AI credentials, so security reports are taken seriously.

## Reporting a vulnerability

Please **don't open a public issue**. Report it privately via
[GitHub security advisories](https://github.com/krugerhomeassistant/CropStack/security/advisories/new).
You'll get a reply within a week, and a fix in the next release for confirmed issues.

## Supported versions

Only the latest release receives fixes. Update with `docker compose pull && docker compose up -d`.

## Design notes

- All data stays in your SQLite file (`/data`); nothing leaves your server unless you enable an external weather, AI or notification service.
- The container runs as an unprivileged user (uid 10001).
- Run CropStack behind HTTPS (or a private network such as Tailscale) when it's reachable from outside your home, and set `CROPSTACK_SECURE_COOKIES=true`.
