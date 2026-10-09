# Changelog

All notable changes to CropStack (app and Docker image) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- **Households**: invite your family with a link (member, viewer or owner). Everyone shares the same garden; members do the daily work, viewers can only look, owners manage the garden location and people. Invite links work once, expire after 7 days and work even when public sign-up is closed.
- Sign-up asks for your name.

### Changed
- Your account and garden move into a household of your own automatically when you update. The climate data is fetched again once.
- The database now upgrades itself safely on start (versioned migrations). Existing installs from v0.1–v0.4 are upgraded in place; no action needed.

## [0.4.0] - 2026-10-09

### Added
- **Rain and heat** in *Your climate*: rainfall pattern (winter, summer, year-round or dry) with a plain-language hint, rain per year and per month, and hot days (≥ 30 °C) per year and per month.

### Changed
- Frost only takes the headline where it happens in at least half of all years. In mild climates such as the Western Cape the card leads with rain and heat, and frost is a single line ("Frost is rare" or "No frost").
- Climate data saved by v0.3.0 is refreshed once automatically to add rain and heat.

## [0.3.0] - 2026-10-09

### Added
- **Your climate** on the home screen: hardiness zone, last spring and first autumn frost dates at your chosen risk level, frost-free season length, how often frost happens, coldest night of a typical year, daylight range, elevation, and monthly average highs, lows and soil temperature. Works anywhere in the world, including the Southern Hemisphere.
- Calculated from 30 years of daily weather records (Open-Meteo, ERA5-Land / ERA5) the first time you open it, then cached; changing your frost risk updates the dates instantly.
- **Place search** in garden setup: find your garden by town, address or postal code (OpenStreetMap).

### Changed
- Privacy: the climate lookup sends your garden's coordinates to Open-Meteo, and place search sends what you type to OpenStreetMap. Nothing else leaves your server.

## [0.2.0] - 2026-10-09

### Added
- **Accounts**: sign up, log in and out, change password. Only the first account can sign up by default (`CROPSTACK_ALLOW_REGISTRATION`); failed logins are throttled per IP.
- **Garden profile**: name, location (with *Use my current location*), optional postal code and how much frost risk you accept. This is the input for the climate engine in the next release.
- **ZimaOS / CasaOS** install file (`docker-compose.zimaos.yml`) and update instructions.

## [0.1.0] - 2026-10-09

### Added
- Project foundation: FastAPI backend with SQLite (WAL), `/api/health`, security headers and session middleware; React 19 + Vite + Tailwind PWA shell; single multi-arch Docker image running as a non-root user; Docker Compose setup.
- CI: ruff lint and format, backend tests, frontend build, image publishing to GHCR and automatic GitHub releases on a version bump.
- Project docs: README, wiki, architecture, roadmap, contributing guide, security policy and Code of Conduct.

[Unreleased]: https://github.com/krugerhomeassistant/CropStack/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/krugerhomeassistant/CropStack/releases/tag/v0.1.0
