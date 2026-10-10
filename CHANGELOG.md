# Changelog

All notable changes to CropStack (app and Docker image) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.28.0] - 2026-10-10

### Added
- **AI co-pilot (first slice).** Owners choose a service in Settings (Ollama on your own server, any OpenAI-compatible API, or Anthropic), a model and an API key, and can test it, remove the key or turn it off. Everyone with edit rights can then use **Ask** (More → Ask): the model sees the garden's place, soil, plantings and open jobs and can only advise. The key is stored on the server and is never sent back to the browser; the service appears under Settings → Data sources once set up.

## [0.27.0] - 2026-10-10

### Added
- **Cells.** Each bed, row or pot is a grid of cells (30 cm by default; change it per bed). Pick a crop, drag across the cells to put it exactly where you want it, and drag with "Take out of cells" to clear. One bed can hold several crops in any order.
- **Staggering.** Every planting holds its cells from sowing to a "holds the cells until" date (or the crop's longest cycle). Move the date slider to see the bed at any time; a cell can take another crop once the first one is out, and the grid flags cells where two plantings overlap.
- **What to plant.** The Garden page lists what can be sown or set out now and soon from your climate, with the best weeks, and names a bed with free cells for it (preferring cells that did not hold the same family). "Plant in Bed 1" does it in one tap.
- Quantity is worked out from the crop's spacing and the cells chosen when you leave it empty.

### Changed
- Deleting a bed leaves its plantings unplaced; a smaller bed drops the cells outside it; changing the cell size clears the bed's cells.

### Internal
- Migration 0012 (`bed.cell_cm`, `planting.cells`, `planting.ends_on`), `engine/layout.py` cell helpers, `engine/recommend.py`, `GET /api/v1/recommendations`.

## [0.26.2] - 2026-10-10

### Fixed
- The server now tells browsers to re-check the page, the app worker and the manifest on every visit, and to keep the built, versioned files for a year. Before, a phone could keep an old copy of the page and keep showing old screens after an update.

## [0.26.1] - 2026-10-10

### Fixed
- An installed app (home-screen icon) could keep showing the previous screens after the server was updated, so new features such as the garden plan did not appear. The app now notices when the server is newer than the screens it has loaded, clears its stored copies once and reloads. Apps older than this release need a one-off refresh (see the wiki).

## [0.26.0] - 2026-10-10

### Added
- **Garden plan.** Draw your beds, rows and containers to scale on the Garden page: add one from a template (raised bed 1.2 × 2.4 m, row, pot), drag it into place, and rename or resize it. Give each planting a bed from its own list, or when you plant. A bed turns amber and says so when the plants in it need more room than it has (from each crop's catalogued spread and row spacing). Renaming a bed renames it in its plantings and jobs; deleting a bed keeps the plantings.

## [0.25.0] - 2026-10-10

### Changed
- A Check job now lists only the pests and diseases that affect that crop (tomato hornworm for tomatoes, powdery mildew for cucurbits, peas, onions, peppers and tomatoes), plus the general ones and the helpers. Organisms in the catalog can name the crops they affect with `hosts`; empty means any crop.

## [0.24.0] - 2026-10-10

### Added
- **Weekly Check job** for every planting that is in the ground. Open "How to do it" to see what to look for: each pest, disease and helper in the catalog with how to recognise it, whether to keep or remove it, and the gentlest first action. Marking it checked (or skipping it) schedules the next look a week later.

## [0.23.0] - 2026-10-10

### Added
- **First organisms in the catalog:** aphids, tomato hornworm, slugs and snails, powdery mildew and whiteflies, plus the helpers that eat them (ladybirds, lacewings, hoverflies, parasitic wasps). Each says what to look for, when to look, whether to keep it, remove it or leave it below a threshold, and the gentlest first action. Text is written fresh; facts cite UC IPM as a facts-only source.

## [0.22.0] - 2026-10-09

### Added
- **Log a harvest** on any planting that is up or growing: how much (kg, g, count or bunch), saved with today's date. The Garden page shows the running total ("Picked: 3.5 kg") for each planting. Harvests are deleted with their planting.

## [0.21.0] - 2026-10-09

### Added
- **How to do it** under every job on Today: a few plain steps for sowing, setting out seedlings, harvesting, watering and protecting from frost or heat. They live in the catalog as task templates, so anyone can improve them with a pull request.

## [0.20.0] - 2026-10-09

### Added
- **Soil question in garden setup.** Sandy, silty or loamy, clay, or not sure, each with a one-line feel test. Watering now uses how much water your kind of soil holds, so sandy gardens get Water jobs sooner and clay gardens later. Existing gardens keep the middle value until you choose.

### Note
- The three soil values come from one worked example each in FAO Irrigation and Drainage Paper 56 (loamy sand 90, silt 170, silty clay 120 mm of water per metre). They are a feel-test answer, not a lab measurement.

## [0.19.0] - 2026-10-09

### Added
- **Water jobs on Today.** For everything you have growing outdoors, CropStack keeps a running account of the water in the soil: what the crop uses each day (from the day's evaporation and the crop's stage), what rain puts back, and how deep the roots reach. When the soil is expected to run dry within three days, Today lists a Water job with how much to give ("about 12 mm, which is 12 litres for every square metre") and why. Say you watered and the count starts again; if rain arrives the job goes away.

### Note
- Until the setup questions ask about your soil, one standard soil is assumed, and 80 % of rain is counted.

## [0.18.0] - 2026-10-09

### Added
- **Protect jobs on Today.** When the forecast for the next 7 days shows a night at or below a growing crop's killing temperature, or a day above the heat where it stops growing, Today lists a Protect job ("Cover tomato in Bed 1 against frost") with the forecast figure and the crop's limit. It uses each crop's own limits, so hardy crops are left alone, and it moves or disappears as the forecast changes. Seedlings still indoors and plantings not yet sown are not included.

### Note
- Frost-kill and heat limits for many crops are still estimates (marked as such in the catalog), and the text uses °C for now.

## [0.17.0] - 2026-10-09

### Added
- **Today shows real jobs.** From your plantings, CropStack makes the jobs: sow, set out seedlings and start harvesting, each with the reason ("Sown on 4 September, tomato usually ripens after about 95 days, worked out from its heat needs and your climate"). Jobs due today are grouped (Plant, Harvest), overdue ones are marked, and the next two weeks are listed under Coming up. Mark a job sown, set out or harvest started, or skip it; the planting moves along with it. Jobs follow the planting if you change it and disappear if it fails or is deleted.

### Development
- Task engine core: `task` and `taskchange` tables (migration 0008), generators keyed so regeneration updates instead of duplicating, a change log, and a 12-hourly refresh job. `GET /api/v1/today`, `PATCH /api/v1/tasks/{id}`.
- `engine.windows.maturity`: days from sowing to harvest for a given start date (p10/p50/p90 over the years on record).

## [0.16.0] - 2026-10-09

### Added
- **Plantings.** On a crop page, *Plant this* fills in the best date from the sowing or set-out window and records what you are planting, how many and where. The Garden tab lists your plantings and lets you move each one along (sown, up, set out, harvesting, finished) or mark it failed. Viewers can see plantings but not change them.

### Development
- `planting` table (migration 0007) and `/api/v1/plantings` (list, add, update, delete) with forward-only status rules.

## [0.15.0] - 2026-10-09

### Added
- **Start indoors, set out seedlings** on crop pages, next to sowing in the ground: the set-out dates that work, how many days before to sow indoors, and the chance of success for each day. Seedlings get a head start, so it often opens a longer season than direct sowing.
- Seedling ages at set-out for 17 crops (marked as estimates until sourced).

## [0.14.0] - 2026-10-09

### Added
- **Anyone can add plants and animals.** A contributor guide (`docs/CONTRIBUTING-CATALOG.md`), issue forms to request a species or report a value, a catalog pull-request template, and a generated to-do list of every missing or estimated value (`docs/COVERAGE.md`).
- **Suggest a correction** link on each crop page, opening the report form for that crop.

### Development
- A monthly GitHub Action re-runs the importers and opens a pull request with the data diff. CI fails when `docs/COVERAGE.md` is stale.

## [0.13.0] - 2026-10-09

### Added
- **When to sow here** on every crop page (once the garden has a location): the dates you can direct-sow it, the best stretch, how long until harvest, and a chart of the chance of success for each sowing day. It is worked out from the crop's requirements and your own climate record, with nothing to configure. Where it cannot succeed, the page says what stands in the way.
- Frost-kill temperatures for 28 crops (marked as estimates until sourced).

### Development
- New `engine` package (`phenology`, `windows`): pure functions over the analog-year climate. Direct sowing only; indoor starts, transplants and protected growing come next.
- API: `GET /api/v1/crops/{slug}/windows`.

## [0.12.0] - 2026-10-09

### Added
- **Growing conditions** on every crop page: the air temperature it grows in and does best in, the soil acidity (pH) it copes with, the length of its growing cycle, and the yearly rainfall it is usually grown in, all from FAO's ECOCROP database, each with a numbered source.

### Development
- `scripts/ingest` reads FAO ECOCROP from the Recocrop R package on CRAN (needs `pip install pyreadr pandas`). Ranges that are missing, zero-filled or out of order are skipped, and ECOCROP's killing temperature is left out because its 0 can mean either 0 °C or "not given".
- Catalog ranges can now describe a best band as well as a single best value (`opt_min`, `opt_max`).

## [0.12.0] - 2026-10-09

## [0.11.0] - 2026-10-09

### Added
- **Climate charts** under More → Climate (or Climate in the side menu): temperature through the year (a typical day's high and low with the range in 8 years out of 10), rain per month, soil temperature, day length, and, only where nights actually freeze, the chance of a freezing night on each day. A dotted line marks today.
- Hover or touch a chart to read the values for that day; with the keyboard, focus a chart and use the left and right arrow keys. Every chart has a "Show as a table" view.
- Charts follow your unit choice (°C or °F, mm or inches) and look right in light and dark mode.

### Changed
- The Climate page opens with the summary card, then the charts.

## [0.11.0] - 2026-10-09

## [0.10.0] - 2026-10-09

### Added
- **Crops**: a catalog of 29 common vegetables, under More (or in the side menu on a computer). Search by English or Afrikaans name, scientific name or plant family. Each crop page shows, in plain words, the soil temperature it needs to germinate and how many days seedlings take at each temperature, how much water it uses compared with a lawn, how deep its roots go and when to water, its size and spacing, and growth-stage lengths from field trials.
- Every value on a crop page has a numbered source, listed at the end with its licence and how strong the evidence is; values reported by growers are marked as rough guides.
- **Where the crop data comes from**: a credits page listing every catalog source and its licence.

### Changed
- Radio buttons are drawn in the app's own style, so unselected options no longer look selected in dark mode.

### Development
- `scripts/ingest`: imports catalog values from FAO-56 (via pyfao56), the Harrington germination tables and the OpenFarm rescue data, keeps a hash-locked snapshot of each source, never overwrites hand-written values, and checks names and families against GBIF.
- `npm run e2e` checks the main flows in a real browser (sign up, garden setup and edit, settings, data sources, household, invites, roles, log out, desktop navigation) against `tests/e2e_server.py`, a server with outside services stubbed. CI runs it and the screenshots on every push and keeps the images as an artifact.

## [0.9.0] - 2026-10-09

### Added
- **Desktop layout**: on screens 1024 px and wider a side menu replaces the bottom bar, and Today shows your jobs and the weather side by side.
- A design system (docs/DESIGN.md) and a shared set of components, so every page looks and behaves the same: headings, sections, buttons, choice cards, switches, badges, loading, empty and error states.
- `npm run screenshots` captures every page in light and dark mode on a phone and a desktop for review before each release.

### Changed
- New look: a cool green-grey background, ruled sections instead of shadowed cards, Bricolage Grotesque for headings and Atkinson Hyperlegible Next (designed for legibility) for text. Colours pass WCAG AA contrast in light and dark mode.
- Today, Garden and Climate have designed placeholders and loading states; data-source details are listed as Sends, When and Licence.
- README and wiki rewritten to match the current app.

## [0.8.0] - 2026-10-09

### Added
- **Weather on Today**: today's high and low, rain chance and wind, the next 7 days with icons, and how the last 30 days compare with normal ("2 °C warmer than normal; drier than 8 in 10 years").
- The forecast refreshes itself in the background about every 3 hours, so Today opens instantly; if Open-Meteo is unreachable the last forecast is shown with its time.
- **Settings → Data sources**: every outside service CropStack talks to, what it sends and when. Owners can switch the forecast and place search off.

## [0.7.0] - 2026-10-09

### Added
- **Catalog foundation**: the format for crops, varieties, animal species and breeds, pests and beneficials, with a source and evidence level on every value, checked automatically (including licences). Content follows in the next releases.
- **Your own values win**: each household can override any catalog value (for example how much cold its tomatoes survive), and reset it.
- **Private pack**: a folder on your server (`/DATA/AppData/cropstack/catalog-private/` on ZimaOS) for your own crop and animal entries, in the same format, for personal use. It is never published.

## [0.6.0] - 2026-10-09

### Added
- **New climate engine**: your location's last 30 years are kept day by day and each year is treated as a possible future, so the app can answer questions like "chance of a night below −2 °C in these three weeks" or "days until this crop has had enough warmth". Recent years count more, and a real warming or cooling trend is taken out of older years. The record refreshes itself each January.
- Climate shows a warming/cooling trend per decade when it is statistically real.

### Changed
- **Climate is described from your data, never classified.** No "winter/summer rainfall" labels, no fixed "hot day" threshold, no rule for when frost is shown. You see rain per year and when most of it falls, the hottest day and coldest night of a typical year, frost dates whenever frost happens at your risk level, and frost nights per month.
- Climate data is downloaded once more after this update (more variables: evaporation, humidity, wind).

## [0.5.1] - 2026-10-09

### Fixed
- Right after an update the app could show "Cannot reach the CropStack server" while the browser still ran the previous version from its offline cache. It now notices the newer server and reloads itself once; "Try again" does a full reload; other errors show what actually went wrong.

## [0.5.0] - 2026-10-09

### Added
- **Households**: invite your family with a link (member, viewer or owner). Everyone shares the same garden; members do the daily work, viewers can only look, owners manage the garden location and people. Invite links work once, expire after 7 days and work even when public sign-up is closed.
- Sign-up asks for your name.

- **New layout**: Today · Garden · More at the bottom of the screen. The climate summary moved to More → Climate, so the home screen is about what to do.
- **Settings** (More → Settings): each person picks the screen the app opens on and metric or imperial units.

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

[Unreleased]: https://github.com/krugerhomeassistant/CropStack/compare/v0.12.0...HEAD
[0.12.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.10.0...v0.11.0
[0.8.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/krugerhomeassistant/CropStack/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/krugerhomeassistant/CropStack/releases/tag/v0.1.0
