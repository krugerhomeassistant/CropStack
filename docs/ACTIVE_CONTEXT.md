# ACTIVE CONTEXT

**Date:** 2026-10-09 · **Version:** 0.4.0 (code) · Spec v1 draft

## Current subtask
Specification and roadmap written after user feedback: fully dynamic (no presets/modes/regions), action-first Today screen for the household (wife: what to plant, water, feed, harvest; what to look for; keep or remove), climate as charts on a secondary page (for the user), guided setup interview (space, water, people, diet, time, budget), layout editor, plan generator, animals with calendars.

## Last execution results
- `docs/SPEC.md` (sections 0–19, principles P1–P9, acceptance criteria AC-P1…P8) and `docs/PLAN.md` (Phases 3–14, atomic tasks) written; README features/roadmap rewritten to match; WIKI/ARCHITECTURE/RESOURCES/TOOLING/LESSONS updated.
- No code changes in this step. Backend 33/33 and CI green as of v0.4.0.

## Blockers
- None. Open questions listed in SPEC §19 (multi-site timing, seasonal tilt default, catalog contribution, pasture model, language order).

## Immediate next step
User reviews SPEC/PLAN. Then start PLAN Phase 3.1 (Alembic baseline matching `user`, `garden`, `climatecache`; entrypoint runs `alembic upgrade head`; migration test from a v0.4.0 DB fixture).
