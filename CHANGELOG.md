# Changelog

All notable changes to CropStack (app and Docker image) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/krugerhomeassistant/CropStack/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/krugerhomeassistant/CropStack/releases/tag/v0.1.0
