# Stocky — Stock Market Learning Dashboard

## What this is
A personal stock-market **learning instrument** (not a trading terminal) for a beginner investor who is also a professional AI engineer. The user learns markets by *using* the app; Claude Code builds it. Prioritize polish, honest framing of uncertainty, and educational value over trading features.

**Product identity (v0.2):** *pro analysis views with beginner captions.* Every veteran tool (breadth, RSI, golden/death crosses, risk-vs-reward scatter, correlation, candlesticks) ships with a "what this is / why vets watch it / when it lies to you" explainer via clickable `Term` popovers. The full **S&P 500** is the universe, filtered by an **affordability cap** (default ≤ $200/share) and ranked per sector by a transparent **Stocky score**.

## Design philosophy
- Teach, don't predict. Every visual should build intuition about risk, volatility, and opportunity cost.
- Scenario ranges, never point predictions.
- Always benchmark against "what if you'd just bought VOO instead."
- Clearer signal from a big universe: the full S&P 500 is ingested, but each sector surfaces a ranked **top-5 affordable** shortlist (expandable) rather than a wall of 500.
- Modern dark fintech aesthetic (Linear/Raycast energy), NOT a generic bootstrap dashboard.

## Core features (build in this order)

### 1. Pulse view (v0.1)
- Sector treemap heatmap, green/red by daily % move
- Watchlist cards with sparklines: daily % change, 52-week range position, volume vs 30-day average
- Unusual-volume and big-mover flags
- Upcoming earnings + macro calendar (Fed meetings, CPI dates)

### 2. Time Machine (v0.1)
- Input: ticker, past date, dollar amount ("what if I'd put $500 into NVDA on March 1")
- Output: value today, total return %, max drawdown along the path (highlight it — "this is the dip that would've scared you out"), and the same amount in VOO side-by-side
- Chart: animated line of both paths

### 3. Scenario Cones (v0.2)
- Monte Carlo fan chart from the stock's own historical volatility (e.g., 1000 GBM paths from 1-2yr daily returns)
- Show bull/base/bear bands with probability shading
- Explicit copy: "range of plausible futures given past behavior — not a prediction"

### 4. Daily Brief (v0.2)
- Scheduled daily job (GitHub Actions cron) pulls fresh data, then calls the Claude API to write a ~5-sentence morning narrative: what moved, plausible why, what's on the calendar
- Rendered as a briefing card at the top of the dashboard
- API key via ANTHROPIC_API_KEY env var (.env, gitignored). Never hardcode keys.

### 5. Learning layer (SHIPPED in v0.2, pulled forward from v0.3)
- Every metric (P/E, RSI, drawdown, beta, VOO, etc.) is clickable → plain-English popover with **what / why vets watch it / when it lies to you**. Lives in `frontend/src/lib/glossary.ts` (~35 terms) + `components/ui/Term.tsx`. Plus a dismissible "Start here" card that explains VOO on first visit.

## Stack (decided — don't relitigate)
- **Backend:** Python 3.11+, FastAPI, DuckDB for storage, yfinance for market data (FRED API later for macro)
- **Frontend:** Next.js (App Router, TypeScript) + Tailwind; ⌘K command palette searches the full universe. **Charts: Recharts** for line/scatter/area/histograms and **lightweight-charts** for the deep-dive candlesticks — *not* Tremor (Tremor's Tailwind config was too brittle and it wraps Recharts anyway; recorded as a deliberate deviation). shadcn/ui not initialized; components are hand-rolled Tailwind.
- **Jobs:** GitHub Actions cron for daily ingestion + Daily Brief generation
- **Repo layout:** monorepo — `/backend` (FastAPI + ingestion), `/frontend` (Next.js), `/.github/workflows`

## API endpoints
Built (v0.2):
- `GET /overview` — index/VIX/10Y tiles + S&P breadth (above MA50/200, adv/dec, new highs/lows)
- `GET /sectors?budget=` — 11 sectors, each with a ranked affordable shortlist (Stocky score + factors)
- `GET /movers?type=gainers|losers|volume|highs|lows|gaps&budget=&limit=` — scanner tables
- `GET /riskmap?budget=` — risk (90d vol) vs reward (1y return) scatter points + VOO reference
- `GET /signals?budget=` — recent golden/death crosses, RSI overbought/oversold lists
- `GET /compare?tickers=A,B,C` — normalized growth, stat table, correlation matrix, histograms (VOO auto-added)
- `GET /stock/{ticker}` — deep dive: OHLCV candles, MA50/200, RSI series, metrics, score, histograms
- `GET /stock/{ticker}/fundamentals` — on-demand yfinance `.info` subset, cached ~1 day
- `GET /pulse` — legacy sector heatmap + watchlist metrics (kept for the watchlist)
- `GET /timemachine?ticker=&date=&amount=` — backtest sim vs VOO
- `GET /calendar` — upcoming earnings (best-effort) + static macro dates
- `GET /universe` — full searchable ticker list (⌘K); `GET /health/data` — warm-up progress + freshness

Built (v0.3):
- `GET /radar?budget=&lookback=1m|2m|3m&limit=` — **Entry Radar**: affordable stocks ≥5% below their lookback high, ranked by entry score (depth 35 · trend 30 · RSI 20 · quality 15, `RADAR_WEIGHTS`), each with **echo stats** — forward 21-session outcomes of that stock's own similar past episodes (same depth bucket + trend state; N≥6 or null). `services/radar.py` + radar helpers in `services/metrics.py`; `/stock/{ticker}` now carries `entry`. Copy rule: *setups to study*, never buy signals; every echo shows N and the worst case.

Built (v0.4 — the reading layer):
- **`services/insights.py`** — deterministic "what does this mean" rules producing `Reading {aspect, headline, detail, tone, caveat}`; `tone ∈ constructive|caution|neutral`. Attached to `/stock/{ticker}` (`readings`) and `/overview` (`readings`). **Copy law, enforced by `tests/test_insights.py`:** every reading carries a caveat, and advice phrasing ("you should", "recommended", "guaranteed", "will rise") fails the suite.
- **Echo tiering**: exact depth bucket first, then a stepped widening ("dips ≥15%") down the bucket edges; `EchoStats.kind` = `exact|at_least` and the UI must label which. Took radar coverage from ~79% to ~99%.
- **Data trust**: `HISTORY_LOOKBACK` = 2000 days (~5.5y, median ~1,377 sessions/ticker); `/health/data` reports `history_span_days`, `median_sessions`, `thinnest_ticker`; `scripts/audit_data.py` audits coverage/gaps/bad prices/anomalies (exit 2 on real problems — a handful of recent IPOs legitimately fail the 300-session bar).

Planned: `GET /cone?ticker=` (Monte Carlo bands), `GET /brief` (Daily Brief text).

## v0.2 architecture notes
- **Universe:** committed snapshot `backend/app/data/sp500_constituents.json` (regenerate via `scripts/build_sp500.py`); macro tickers `^VIX`, `^TNX`.
- **Warm-up:** on startup a background thread ingests the whole universe in ~100-ticker chunks, **priority tickers first** (`WARM_ON_START`); progress + freshness via `/health/data`.
- **Analytics:** pure/tested math in `services/metrics.py` (RSI Wilder, MAs, crosses, vol, returns, correlation, histograms) + `services/screener.py` (per-sector percentile scoring); orchestrated in `services/analytics.py` with an in-process metrics cache keyed by (data date, warm progress). Read-only over cached DuckDB rows — never fetches inline.
- **Correctness rule:** raw `close` for prices/affordability/gaps; `adj_close` for returns/volatility.
- **Frontend routes:** `/` Pulse · `/radar` Entry Radar · `/explore` · `/compare` · `/stock/[ticker]` · `/time-machine` · `/calendar`. Global budget via `lib/budget.tsx`; teaching via `lib/glossary.ts` + `components/ui/Term.tsx`.
- **History depth:** `market.HISTORY_LOOKBACK` = 1200 days (~3.3y) so radar echo stats have a real sample; widening it again forces a one-time universe back-fill.

## User context
- Beginner investor; risk tolerance moderate; separately keeping core money in index funds — this app informs only a small "conviction" allocation
- Never present outputs as financial advice; include a small persistent disclaimer in the UI
- Default watchlist to seed: NVDA, AAPL, MSFT, GOOGL, AMZN, TSLA, AMD, META, VOO (benchmark)

## Conventions
- Type hints + pydantic models on all endpoints
- Tests for the sim math (Time Machine returns, drawdown calc, Monte Carlo shape)
- Keep ingestion idempotent; DuckDB file lives in /backend/data/ (gitignored)
