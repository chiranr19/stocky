# Handoff — v1.0 the study wall (2026-08-23)

## What shipped this session
Four new **study visualizations** on /watchlist (and the cone on every /stock page), built to
the user's ask: *"more graphs and charts and forecasts and study viz — interactive, interesting,
stimulating, weird, different, intelligent, informative."* Each is a teaching instrument with a
metaphor lede, a self-reading computed line, a methodology popover, and a "where this lies to you"
footer. Verified live against real data; **1320 backend tests + full `next build` (15 routes) green.**

### The four (study flow: past → texture → structure → future)
1. **The race + trend barcode** (`RaceChart`) — every name's $1k over the year on one chart,
   ghost-mode (VOO + selected bold), finish-line standings, and the selected name's MA200 barcode
   + vs-VOO verdict. Late joiners are *named*, never started from a false line.
2. **The rain gallery** (`RainGallery`) — 60 daily moves per name as a div-dot beeswarm; VOO pinned
   first, calm→wild, yesterday's dot in accent, a synchronized "Replay the 60 days".
3. **The constellation** (`Constellation`) — MDS star map + minimum-spanning-tree links; tap a star
   for "gravity view" (others dim by |ρ|).
4. **The cone of uncertainty** (`ConePanel`) — the honest forecast, full theater.

### Backend (new: `services/cone.py`, `routers/cone.py`; +fields in learn/metrics/models)
- **`GET /cone`**: stationary block bootstrap (Politis–Romano) over ~504 daily log returns, 2,000
  paths, pointwise p10/p25/p50/p75/p90 as start-price multipliers, ~24 sample paths, VOO cone
  alongside. Deterministic (seeded per ticker/as_of/horizon), cached per analytics generation,
  read-only over `universe_closes()`. ≥250 sessions → else teaching 422; unknown → 404.
- `metrics.mds_layout()` / `mst_edges()` (+ `_distance_matrix`) — classical MDS + Mantegna MST on
  √(2(1−ρ)). `learn._member` gained `rain`/`regime_1y`/`series_start`; `_build` gained `rain_dates`
  + `constellation`. `_downsample` refactored to expose `_downsample_series` (shared indices).
- Tests: `test_cone.py`, `test_study.py`; `test_frontend_copy.py` now also scans `studyCopy.ts`.

### Frontend (new: `components/study/*`, `lib/studyCopy.ts`, `lib/motion.ts`)
- `ConePanel` (reusable — /watchlist picker + /stock), `RaceChart`, `RainGallery`, `Constellation`,
  `StudyLede`, `ConeSection`. Lens-native throughout (cone/race flip $↔%). All JS animation gates on
  `useReducedMotion()` (matchMedia). `types.ts` + `api.ts` (`getCone`) mirror the backend.
- Copy law extended: p50 = "the middle path", p25–p75 = "the middle half"; "median" never reaches UI.

## Verified live (2026-08-21 close)
Cone bands widen; NVDA 6mo middle-half **$478–$685** vs VOO **$513–$581** ("a wider cone is a wilder
ride, not better odds"). "Run the futures" drew 24 paths + "18 of 24 ended above where CMS sits
today". Lens toggle flips cone summary + race axis $↔% and persists. **1020 rain dots / 17 strips**,
**15 MST edges / 16 nodes**, cone on /stock/NVDA. No React/hydration errors after a clean `.next`
rebuild.

## Not done / next
- **Nav overflows ~62px at 375px, app-wide** (⌘K + freshness cluster + the v0.9 scrollable link row).
  Reproduced on untouched /radar, so it's a **pre-existing** issue, not the study viz (those are
  mobile-clean). Worth a small separate nav fix.
- **Digest + mobile snapshot deliberately untouched** — a stale cone in an inbox reads as a
  prediction. If ever added, it must be labeled as-of and never framed as a call.
- **Cone default on /watchlist = highest-attention member** (currently CMS). If that name has 200–249
  sessions it 422s with the teaching message (rare; the panel handles it). Real mega-caps are deep.
- **KO** may still sit in `hidden` from an earlier live test (harmless).
- **Nothing is committed** — v0.8 + v0.9 + v1.0 + the parallel filers track are all uncommitted.

## Run it
Servers via `.claude/launch.json` (backend :8010, frontend :3000, `NEXT_PUBLIC_API_URL=…:8010`).
After backend router/model changes, **restart the backend** (no `--reload`). After heavy frontend
edits, if HMR shows `Cannot find module './NNN.js'` (corrupt chunks), stop the dev server,
`rm -rf frontend/.next`, restart — that cleared it this session.
