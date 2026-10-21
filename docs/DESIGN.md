# DESIGN

The visual system for CropStack. Tokens live in `frontend/src/index.css` (`@theme`), components in `frontend/src/components/ui/`. Every changed screen is checked in light and dark, phone and desktop, before a release (`npm run screenshots`).

## Concept: seed packet and field notebook

CropStack is a working tool used outdoors on a phone, in sun, often with dirty hands, by people who are not necessarily technical. It borrows from the things gardeners already trust: seed packets (one bold colour that tells you what kind of thing you're holding) and field notebooks (ruled, plain, legible). It should feel calm and sure, never decorative.

**The one bold element**: the coloured task-group label on Today (Plant, Water, Feed, Harvest, Protect, Check, Animals, Maintain). Colour there is information. Everything else stays quiet.

## Colour

| Token | Light | Dark | Role |
|---|---|---|---|
| `canvas` | `#F2F5F1` | `#101611` | page background (cool green-grey, not cream) |
| `surface` | `#FFFFFF` | `#18211A` | sections, inputs |
| `sunken` | `#E7ECE5` | `#0C110D` | wells: weather band, selected states |
| `line` | `#D9E1D7` | `#2A352C` | hairline rules and borders |
| `ink` | `#18261C` | `#E6EDE5` | text |
| `muted` | `#56645A` | `#A3B0A5` | secondary text |
| `leaf` | `#2E6B3F` | `#7CC48A` | brand, primary actions, Plant |
| `on-leaf` | `#FFFFFF` | `#101611` | text on leaf |
| `marigold` | `#E8A317` | `#F2B941` | Protect / urgent: fills only, with `ink` text |
| `water` | `#1F6AA8` | `#7DB6E8` | Water tasks, rain |
| `feed` | `#7A5230` | `#D2A47C` | Feed tasks, soil |
| `harvest` | `#B83E22` | `#F08A6B` | Harvest tasks |
| `check` | `#5E4B98` | `#B3A3E6` | Check / scouting tasks |
| `animals` | `#8A5E14` | `#E0B45E` | Animal tasks |
| `danger` | `#B3261E` | `#F2B8B5` | destructive actions, errors |

All text colours meet WCAG AA (≥ 4.5:1) on `surface` and `canvas` in both themes (checked 2026-10-09). Colour is never the only signal: task groups also carry an icon and a name.

## Type

- **Bricolage Grotesque** (variable): headings, page titles, big numbers (temperatures, counts). Weight 650–800, tracking −0.01em. It brings the character of a seed catalogue.
- **Atkinson Hyperlegible Next** (variable): body and UI. Designed for low-vision readers; chosen for outdoor phone use.
- Scale (major third, 16 px base): 12 · 14 · 16 · 20 · 25 · 31 · 39. Body 16/1.5; small 14/1.45; captions 12/1.4. Line length ≤ 70 characters.
- Sentence case everywhere. No all-caps labels, no eyebrow labels above headings.

## Shape, depth, spacing

- Radius follows hierarchy: page sections 16 px, rows and inputs 10 px, buttons 12 px, chips and switches fully round.
- Depth: sections sit on the canvas with a hairline `line` border, no shadow. Shadows only for things that float above the page: bottom nav, sheets, toasts.
- Spacing on a 4 px grid; page gutter 16 px (phone) / 32 px (desktop); 24 px between sections.
- Tap targets ≥ 44 × 44 px.

## Layout

- Phone (< 1024 px): single column, bottom nav (Today · Garden · More), content max 640 px.
- Desktop (≥ 1024 px): left rail (240 px) with the same destinations plus the More items expanded; content max 960 px; Today uses two columns (tasks | weather and week).

## Components (`components/ui/`)

`Button` (primary · secondary · ghost · danger; md · sm), `IconButton`, `Section` (title, optional action, body), `Field` (label, hint, error around any input), `TextInput`, `Select`, `RadioCards`, `Switch`, `Badge`, `EmptyState` (icon, title, one sentence, action), `ErrorState` (what happened + Try again), `Skeleton`, `Sheet` (bottom sheet on phone, dialog on desktop). Toasts and tabs are added with the first screen that needs them.

## Motion

Only in answer to an action: switches slide, sheets rise, pressed buttons darken. No entrance animations. `prefers-reduced-motion` turns transitions off.

## Copy

Plain verbs, sentence case, the user's words ("Water bed 3", not "Irrigation event"). Actions keep their name through a flow ("Save garden" → "Garden saved"). Empty screens say what will appear and what to do now; errors say what happened and how to fix it, without apologising.

## Rejected defaults (and why)

- Warm cream background + rounded sans (Nunito): the generic generated-app look; replaced by a cool canvas and a type pairing chosen for legibility.
- One rounded card with the same soft shadow for everything: replaced by ruled sections and hierarchy-based radius.
- Middle-dot meta strings ("Friday · My garden"), all-caps eyebrows, arrows in buttons: template chrome, not information.

## The planner (v0.38.0)

The one place the app is allowed earth tones: the garden map is a plot plan. Beds use a soft `feed` tint with a thin edge, planted cells are tiles in the crop's colour (the same colour as in the bed editor) with the crop icon on top, the ground is a fine one-metre grid, and the selected bed has a soft `leaf` halo and thin ring. The bed editor sits in a thin rounded frame, not a thick border. Tools float over the map as a single pill (floating things may carry a shadow). Where two beds face each other, a thin dimension line shows the gap in metres (muted; green for the selected bed). The map frames the beds (1 m of margin, 2.6 m below for the pill) and holds still while a bed is dragged. Desktop: map (3/5) and bed panel (2/5) side by side; phone: stacked.

**Resizable windows.** `Section` carries a bottom handle (`role=separator`) that sets the window's height by drag or arrow keys; double tap resets it. The height is kept in `localStorage` under the window's title (or its `name`, for a window without one). Content scrolls inside a shortened window.

## Crop icons

One flat icon per catalog crop in `frontend/src/icons/crops/<slug>.svg` (`_seedling.svg` is the fallback for a crop without one). `CropIcon` draws it in HTML and scales with the surrounding text; inside an `<svg>` (plot plan, bed grid) use `<image href={cropIconUrl(slug)}>`. A backend test fails when a catalog crop has no icon.

- **Flat colour**: solid shapes in the plant's true-to-life colour, no outlines, no gradients, no filters. Details are fills or 2.6 px round-cap strokes in a darker or lighter shade of the same plant.
- **Canvas**: `viewBox="0 0 64 64"`, subject centred and filling roughly 56 px, leaves and stems may reach the edge but never clip. Plain `<svg>` with one `viewBox` and no ids, scripts, fonts or external references (Vite inlines the small files, so the PWA works offline).
- **Palette**: leaf greens `#2E6B3F` `#5FA845` `#A7D96B`, soil/wood `#7A5230`, then each crop's own fruit, root or flower colour. At most one soft white highlight (`opacity .3-.4`) on round fruit.
- **Same style for the rest**: pests, diseases and beneficial insects live in `frontend/src/icons/organisms/<slug>.svg` (a test requires one per `catalog/organisms` entry) and animals in `frontend/src/icons/animals/<slug>.svg`; they follow the same rules.
- **Check**: after adding or changing icons, view them at 96 px and 24 px side by side; they must stay recognisable at 24 px.
