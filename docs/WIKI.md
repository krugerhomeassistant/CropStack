# WIKI — CropStack

## Purpose
Self-hosted, Docker-based garden and homestead planner. It turns a location (coordinates or postal code) into local climate facts (hardiness zone, frost dates, soil temperature, daylight) and combines them with plant data to produce a rolling task calendar, from indoor sowing to harvest. Local-first: one SQLite file, optional integrations (weather, Home Assistant, AI) are opt-in.

## Users & principles
- Home gardeners and homesteaders running their own server (NAS, Pi, home lab).
- Works offline in the field (PWA); nothing leaves the server unless an integration is enabled.
- Plans are explainable: every task shows the rule and dates it came from.

## Glossary
| Term | Meaning |
|---|---|
| Hardiness zone | USDA zone (1a–13b) from average annual extreme minimum temperature |
| Last spring frost (LSF) | Date after which frost risk drops below the chosen probability; anchor for spring tasks |
| First fall frost (FFF) | Date the fall frost risk rises above the chosen probability; end of the outdoor season for tender crops |
| Growing season | Days between LSF and FFF |
| Days to maturity (DTM) | Seed or transplant to first harvest, per variety |
| Hardening off | Gradual outdoor exposure of indoor seedlings before transplanting |
| Succession interval | Days between repeated sowings of the same crop for a continuous harvest |
| Companion matrix | Beneficial / antagonistic pairings between plants |
| Crop family | Botanical family used for rotation (e.g. Solanaceae, Brassicaceae) |
| Rotation conflict | Same crop family in the same bed within the configured number of seasons |
| Plot / bed | Physical growing area on the garden map (raised bed, row, container, guild) |
| Task | A dated action generated from plant timing + climate (sow, transplant, harden off, feed, prune, harvest) |

## Planned scheduling rules (to be confirmed during implementation)
- Indoor sowing = LSF − (variety weeks before LSF).
- Hardening off starts 7–10 days before transplant.
- Transplant / direct sow = LSF + variety offset, gated on minimum soil temperature when known.
- Harvest window = sow or transplant date + DTM (± variety spread).
- Last viable sowing = FFF − DTM − buffer (fall planting).
- Weather overrides shift or flag tasks (frost alert → protect or delay tender transplants; heat → extra watering; heavy rain → skip watering).

## Workflows
- **Health check**: `GET /api/health` → `{status, version}`; also runs `SELECT 1` against SQLite. Used by the Docker `HEALTHCHECK`.
- **App shell**: the PWA loads, calls `/api/health` and shows server status and version.
- **Routing**: `/api/*` = API (404 JSON for unknown routes); every other path serves a built file if it exists inside the build dir, else `index.html` (client-side routing; traversal attempts fall back to `index.html`).

## Configuration
See `README.md` → Configuration. All env vars use the `CROPSTACK_` prefix (`backend/app/config.py`).

## Data
- `./data/cropstack.db` (SQLite, WAL) and `./data/secret.key` (auto-generated session key, mode 600).
- Back up the whole `data/` folder.

## Release process
`python scripts/bump.py X.Y.Z` → commit → push to `main`. CI publishes `ghcr.io/krugerhomeassistant/cropstack:X.Y.Z` and creates the GitHub release from `CHANGELOG.md`.
