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
