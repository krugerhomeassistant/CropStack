# Changelog

All notable changes to CropStack (app and Docker image) are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.46.0] - 2026-10-16

### Added
- **Gaps between beds on the plot plan.** Where two beds face each other with nothing between them, a thin dimension line shows the clear ground in metres (up to 6 m apart). It follows the bed while you drag it, and lines for the selected bed turn green.

### Fixed
- **Cells no longer hang over the edge of a bed.** A 2.5 m bed on 30 cm cells got nine columns (2.7 m), so the last column of plants stuck out of the bed on the plan. The cell size is now picked so whole cells fit the bed exactly, the one nearest 30 cm (2.5 × 1.5 m gets 25 cm cells), when you draw a bed and again when you resize it. A size you set yourself stays while it still fits. Existing beds are refitted once on update; their plantings are mapped onto the new cells and the overhang is dropped. Beds whose sides are not a multiple of 5 cm keep 30 cm.

### Changed
- **One date for the whole plan.** The date stepper moved from the bed panel to above the plan, so the plan and the bed panel always show the same day. Plantings that start later show faint in both (before, the bed panel showed them nowhere, so a bed with a cabbage planned looked empty).
- **What is planted.** The bed panel lists the plants per crop ("6× Chilli", with "+4 planned" for what goes in later), and with no bed selected the same list covers the whole garden.
- Beetroot, radish, strawberry and tomato are now red, chilli orange-red, carrot orange, and the other well-known crops keep their natural colours (beetroot was purple); other crops keep a steady colour from their name.

### Removed
- **The Garden map section** (Leaflet with satellite/street tiles and the draggable origin pin) and its `leaflet`, `react-leaflet` and `@types/leaflet` dependencies. The plot plan is the one place beds are positioned. Place search in garden setup (OpenStreetMap Nominatim) stays. A top-view image (drone photo) as a plan background is planned instead.

## [0.45.1] - 2026-10-16

### Fixed
- **A drafted year plan can always be used.** "Year plan overlaps occupied cells in Bed N" appeared on plans the planner itself drew: the drafter held cells for the days to maturity it read from the climate, while the server (and every saved planting) holds them for the catalog cycle, so crops the drafter packed into the same cell one after the other clashed on acceptance. The drafter now reserves the longer of the two, and a test drafts and accepts a plan twice against the real catalog.

## [0.45.0] - 2026-10-12

### Added
- **Exact placement in the year plan.** A plant's patch is now worked out from its spacing in both directions, never tighter than the catalog says: a 45 × 45 cm tomato takes a 2 × 2 patch of 30 cm cells (before: three cells in a row, which is 90 × 30 cm), a 30 × 90 cm potato a 3 × 1 patch, and small plants share a cell as many as fit in both directions (10 × 20 cm: three). A crop's block is a solid rectangle of whole patches, so every plant has its own ground, and the plan, painting a bed, the over-capacity warning and the suggestions all count plants the same way.
- **Companions are placed by what touches.** The drafter puts a block against a good companion that grows then and keeps it out of a bed that holds one of its bad companions at the same time; "Grows beside" now means the blocks really touch. A companion flower goes against the crop's block, on the edge of the bed where there is room.
- **Two more flowers (zinnia, petunia) and many more pairs.** Companion pairs are read in both directions from the Wikipedia table (the row for a crop and the row for a flower) and family-level entries ("brassicas", "cucurbits", "alliums", "beans") now apply to each such crop: 363 good and 56 bad pairs, up from 143 and 31. A crop's flowers are its good partners that are companion flowers, so they are no longer a separate list.
- **Spacing for every crop.** Twelve crops had none (broad bean, Brussels sprouts, chilli, cucumber, Jerusalem artichoke, mustard greens, oregano, pumpkin, swede, sweet corn, Swiss chard, watermelon); they now carry usual in-row and between-row spacings, flagged as estimates.

### Changed
- A companion flower's job reads "Start picking marigold flowers", and the plant suggestions and key points say "flowers from" and "In flower" instead of "harvest".

## [0.44.0] - 2026-10-12

### Added
- **Companion flowers you can plant.** Marigold, nasturtium, borage, chamomile, sweet alyssum and sunflower are now catalog entries (a new `purpose: companion` on a crop marks a plant grown for the garden, not the table: no food group or yield). Borage, chamomile and sunflower take their temperatures, pH and rainfall from FAO ECOCROP; marigold, nasturtium and alyssum have no ECOCROP row, so their temperature and spacing values are flagged estimates. All six appear in "Plant now" and can be painted into a bed like any crop.
- **The year plan places them.** Beside a crop that has traditional flowers, the drafter puts a small block (two cells) of a flower that can be sown at that time, in the same bed, timed to bloom while the crop grows. One block serves every crop in the bed that goes with that flower. Each item says "Companion flower for Tomato" or "With Sweet alyssum beside it"; crops whose flowers cannot be sown in their season (a marigold in winter) keep the "traditionally grown with" hint instead.

## [0.43.0] - 2026-10-12

### Added
- **Companion planting in the year plan.** A new `catalog/companions.yaml` holds 143 traditional good pairs and 31 pairs to keep apart between the catalog's crops, plus flowers grown beside 15 of them (facts from Wikipedia's "List of companion plants", revision 1334550406, CC BY-SA, evidence `traditional`). The drafter now prefers a bed that already holds a good companion that season, never puts a crop in a bed with one of its "avoid" crops at the same time, and each planned planting says what it grows beside and which flowers are traditionally grown with it. They are hints, never rules: you can still plant anything anywhere by hand.

### Changed
- **Proper spacing for big plants.** A plant that needs more ground than one cell (a tomato or a squash on 30 cm cells) now takes as many cells as it needs, kept together as one patch, and the plant count follows (a potato block that held 12 plants now shows 4 on 12 cells). This applies to the year plan, painting a bed, the "over capacity" warning and the plant suggestions, which now say "1 plant per 3 cells" where that is so.

## [0.42.2] - 2026-10-12

### Changed
- **A calmer plot plan.** A planting is now one solid block of its crop's colour with no lines between cells, planned plantings are a faint tint instead of dashed cell outlines, a crowded bed has a thin solid line instead of a thick dashed border, and layout frames are a quiet hairline.

## [0.42.1] - 2026-10-12

### Fixed
- Password managers fill the sign-in form correctly: the fields now carry proper name, id and autocomplete attributes, and Log in and Create account are separate forms.

## [0.42.0] - 2026-10-12

### Added
- **Sign-up is always open.** Anyone can create an account, choosing "Start my own" household or "Join a household" with an invite link or code from an owner. `CROPSTACK_ALLOW_REGISTRATION` now defaults to `true`; `auto` is kept as an alias of it and `false` closes sign-up (invite links still work).

### Changed
- A browser that has signed in before opens on Log in (new browsers open on Create account), so signing out does not drop you onto a sign-up form.
- **A more modern plot plan.** A fine metre grid replaces the plus marks, beds have a soft soil tint and thin edge, planted cells are coloured tiles that match the bed editor, the selected bed has a soft halo, and the bed editor's frame is thin and rounded.

## [0.41.0] - 2026-10-11

### Added
- **The year plan feeds your household.** Set how many people you feed; the plan sizes each crop from a balanced basket (400 g of vegetables per person per day, split across leafy greens, fruiting vegetables, roots, brassicas, beans and peas, squash, onions and herbs), fills your beds as well as it can, and shows how much of the need they cover, the weeks that fall short, and what adding about 4 m² of bed would change.

### Changed
- Crop areas in a drafted plan now depend on yield, not a fixed six cells.

### Fixed
- Switching a data source on or off no longer touches other settings.

### Notes
- Yields per m² are labelled estimates for now (low confidence); they will be replaced with sourced figures.

## [0.40.0] - 2026-10-11

### Added
- **Clear plan.** The Year plan section says how many plantings from an earlier plan are still to do and has a Clear plan button (with a confirmation). It removes only what the plan scheduled and nothing has started.

### Fixed
- **Drafting a year plan again no longer doubles everything.** Using a new plan replaces the earlier plan's unstarted plantings, and the new draft is made as if they were not there. Anything you sowed, planted or painted by hand stays and still blocks its cells. Plans saved before this version are recognised automatically.

## [0.39.1] - 2026-10-11

### Changed
- **Sowing depths now come from published tables.** For 17 crops the depth on a sow job is taken from the University of Missouri and Mississippi State extension planting tables. Where the two differ (sweet corn, pumpkin, peas) you see the range, for example "1.3 to 5 cm". The other crops keep their labelled estimates.

## [0.39.0] - 2026-10-10

### Added
- **Pests and diseases.** 13 more organisms (late and early blight, cabbage caterpillars, carrot fly, onion thrips, Colorado potato beetle, cucumber beetles, clubroot, downy mildew, blossom end rot, spider mites, cutworms, allium rust), each with how to recognise it, when to look and what to do first. The weekly Check job lists the ones that affect that crop.

## [0.38.0] - 2026-10-10

### Changed
- **The planner is redrawn as a plot plan.** The map frames your beds (no more empty canvas), beds have a timber edge and soil, each planted cell shows its crop icon (faded with a dashed outline for what is only planned), names sit on small tags with a ⏳ count of what is still to plant, and there is a 1 m scale. The tools (Move, Bed, Row, Pot) float over the map as one pill. The selected bed is ringed in green.
- The bed panel sits beside the map on desktop (the map stays in view while you plant) and below it on a phone. Crops to plant are large icon tiles in a scrolling row; the bed's cells are drawn bigger inside a timber frame.

## [0.37.0] - 2026-10-10

### Added
- **Pantry** (More → Pantry): record preserved and stored food (canned, frozen, dried, fermented, cellar, fresh) with amount, date put by, use-by date and where it is. A use-by date is worked out from how it is kept when you leave it blank. Anything due within a month or past its date is listed first under "Use first"; "Use one" counts it down and removes it at zero.

## [0.36.0] - 2026-10-10

### Added
- **Sowing depth** for 53 crops, shown on sow jobs. These are marked as estimates (usual seed-packet guidance) until a source is attached.

### Changed
- **Today is calmer**: each job card shows its title, why, and one key line (for example "1 cm deep · 8 cm apart"); the crop's full facts, general steps and what to look for are under "Details".

## [0.35.0] - 2026-10-10

### Added
- **The plan shows what is planted**: each bed on the plan is filled cell by cell in its crops' colours for what is growing now, with dashed cells for what is planned, the crop icons and a count of what is still to plant. Bed buttons show the same icons. Cells in the bed grid carry a crop icon and name.
- **Crop-specific job details**: a sow, set-out, harvest or water job lists that crop's own spacing, thin-to distance, soil temperature, days to come up (warm versus cold soil), light, seedling age and cycle, read from the catalog. The general steps moved under "General steps".

## [0.34.1] - 2026-10-10

### Fixed
- **"Request failed (500)" when planting**: two planting requests at once (quick taps, or a plan being used) both planned the same jobs and one failed on the unique key, even though its planting had been saved. Job planning is now serialised.
- A quick tap on a bed cell sometimes planted nothing (the stroke ended before the screen updated). The stroke is now tracked directly.
- Painting a cell on today's date or earlier records the planting as sown (or set out) straight away, instead of pending.
- "Draft a year plan" is a full button in the section instead of a squeezed, wrapping one.

## [0.34.0] - 2026-10-10

### Added
- **Year plan**: on the Plant tab, "Draft a year plan" fills your beds for the next 12 months from your climate's sowing windows, one block of cells per crop, with cells that grew the same family last avoided. Review it by month, leave out what you do not want, then "Use this plan" to create all the plantings and jobs at once. While a draft is open it shows as dashed cells in each bed (step the date to see it through the year).
- **31 more crops** (60 in all): leek, shallot, brussels sprouts, kohlrabi, rocket, mustard greens, pak choi, endive, fennel, rhubarb, globe artichoke, okra, sweet potato, broad bean, runner bean, chilli, coriander, basil, dill, thyme, sage, rosemary, oregano, chives, mint, strawberry, swede, horseradish, Jerusalem artichoke, celeriac and watercress. Temperatures, rainfall, cycle length, water use and spacing come from the cited sources (FAO ECOCROP, FAO-56, Harrington, OpenFarm rescue); descriptions are our own words.

### Fixed
- Erasing cells from a planting left its plant count unchanged, so the bed said "More plants than the cells hold". The count now follows the number of cells.

## [0.33.0] - 2026-10-10

### Added
- **Already growing**: plant on a date in the past and the planting is recorded as sown (or set out), with its harvest worked out from that day and no overdue sowing job.
- **Key points**: tap any suggested crop (Plant tab or the chips above a bed) for a short sheet: when to plant, expected harvest dates, how often it works in your climate, spacing, seedlings needed and rotation family, with a link to the full crop page. Bed cells and the Plantings list show harvest expected and the next job.

### Changed
- **Bed changes never throw away your work.** Resizing a bed keeps every planted cell (those beyond a smaller edge are kept and counted); changing the cell size redraws the same ground on the new grid. Saving a bed only writes the fields you changed.
- **Any cell can be planted.** The server no longer refuses a cell for lying outside the grid.
- Tool row on the plan fits on one line (Move, Bed, Row, Pot).

## [0.32.0] - 2026-10-10

### Changed
- **The Garden page is four windows**: Plan, Plant, Calendar and Plantings, instead of one long scroll. The plan has a short tool row and a row of bed buttons; tapping a bed opens its own panel with the cell grid, and the bed's rename, resize and layout form sits behind "Edit bed".
- **Plant** lists what can go in the ground now and soon in one line each (crop, when, best weeks) with a single Plant button. Plant takes you to a bed with that crop already chosen and the date set; the crops suggested for now are also chips above the grid.
- The date slider is gone: step a month at a time, or pick a date, with a Today button.
- Painting more of the same crop on the same day adds cells to that planting instead of creating a new planting for every stroke. The Plantings list also groups identical plantings and keeps its extra actions (failed, harvest, bed, delete) behind More.
- A full bed now says why: cells with two plantings at once, more plants than the cells hold, or too little room. It no longer says "need 0 m²".
- An error with no message from the server now shows its status number.

### Added
- **Calendar**: a month view of sowing, setting-out and harvest days with a dot per day; tap a day for its jobs.

## [0.31.0] - 2026-10-10

### Added
- Tap a planting in a bed's cell grid to change its sow date, set-out date, number of plants and "holds the cells until" date in one form. Dates could not be edited before; jobs are recalculated when you save.

## [0.30.0] - 2026-10-10

### Changed
- **Draw the garden plan freely.** Pick Draw bed, Draw row or Draw pot and drag on the plan to draw it at any size (a click places the standard size). Drag a bed to move it, and drag the round handle on its corner to resize it. The plan always has room to draw in, even with no beds. The three fixed-size buttons are gone.

### Added
- **Layouts.** Give beds a layout name (for example "Back garden") and they are framed together on the plan and move as one when you drag any of them or the layout's name; a switch turns the grouping off when you want to move a single bed.

## [0.29.0] - 2026-10-10

### Added
- Garden assistant settings now follow the Bloomery pattern: Claude, OpenAI, OpenRouter, Ollama or any OpenAI-compatible service, each with default address and model (leave blank), model suggestions, a link to get a key, and a **Test** that tries the form's values before you save. Switching service drops the old key; a saved key shows only its last four characters.
- A compose file can preconfigure the assistant with `CROPSTACK_AI_PROVIDER`, `_BASE_URL`, `_MODEL`, `_API_KEY` and `_TIMEOUT`; Settings override them.

### Fixed
- OpenAI GPT-5 models are called with the token limit they accept; a reasoning model's visible thinking is removed from replies; service errors show the provider's own message.

## [0.28.1] - 2026-10-10

### Changed
- The AI feature is now called the **garden assistant** (Settings and Ask) instead of the co-pilot.

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

[Unreleased]: https://github.com/krugerhomeassistant/CropStack/compare/v0.46.0...HEAD
[0.46.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.45.1...v0.46.0
[0.45.1]: https://github.com/krugerhomeassistant/CropStack/compare/v0.45.0...v0.45.1
[0.45.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.44.0...v0.45.0
[0.44.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.43.0...v0.44.0
[0.43.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.42.2...v0.43.0
[0.42.2]: https://github.com/krugerhomeassistant/CropStack/compare/v0.42.1...v0.42.2
[0.42.1]: https://github.com/krugerhomeassistant/CropStack/compare/v0.42.0...v0.42.1
[0.42.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.41.0...v0.42.0
[0.41.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.40.0...v0.41.0
[0.40.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.39.1...v0.40.0
[0.39.1]: https://github.com/krugerhomeassistant/CropStack/compare/v0.39.0...v0.39.1
[0.39.0]: https://github.com/krugerhomeassistant/CropStack/compare/v0.38.0...v0.39.0
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
