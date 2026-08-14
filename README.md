# Stocky 📈

**A stock-market learning dashboard: pro analysis views with beginner captions.**

[![CI](https://github.com/chiranr19/stocky/actions/workflows/ci.yml/badge.svg)](https://github.com/chiranr19/stocky/actions/workflows/ci.yml)

Stocky shows you the tools a market veteran actually uses — breadth, RSI, golden
crosses, risk-vs-reward maps, correlation, candlesticks — and pins a plain-English
note to every one of them: **what it is, why vets watch it, and when it lies to
you**. The full S&P 500 is screened down to stocks you can actually afford
(default ≤ $200/share), and everything is benchmarked against the boring
alternative: just buying VOO.

> ⚠️ Educational tool for building intuition about risk, volatility, and
> opportunity cost. **Not financial advice.**

![Stocky — Market Pulse](docs/screenshot.png)

## What's inside

| Page | What it does |
| --- | --- |
| **Pulse** `/` | VOO · VIX · 10-yr yield + market breadth, Entry Radar preview, sector-by-sector **affordable shortlists** ranked by a transparent score, movers, watchlist |
| **Entry Radar** `/radar` | Affordable stocks in a **pullback**, ranked by a transparent entry score (depth · trend · RSI · quality) and **validated against each stock's own history**: N similar past dips → median next-month move, win rate, worst case. Setups to study — never buy signals |
| **Explore** `/explore` | Risk-vs-reward scatter (all 500 names), scanners (gainers/losers/volume/52-week highs·lows/gaps), golden/death crosses, RSI extremes |
| **Compare** `/compare` | Up to 3 tickers vs VOO: normalized growth, stats, correlation matrix, return distributions |
| **Deep dive** `/stock/…` | Candlesticks + MA50/200 + volume + RSI, score breakdown, fundamentals, distribution vs VOO |
| **Time Machine** `/time-machine` | "What if I'd put $500 in NVDA on that date?" vs VOO — with the scariest drawdown highlighted |
| **Calendar** `/calendar` | Upcoming earnings + macro dates (Fed, CPI, jobs) |

**The teaching layer is the point:** ~35 glossary terms, and every metric label in
the app is clickable → a popover explains it like you're new (because the builder
was). The **Stocky score** (Momentum 40 · Stability 30 · Resilience 20 ·
Liquidity 10) is fully transparent — a starting point for learning, never a
recommendation. A freshness badge proves how current the data is against the
NYSE calendar.

**The reading layer** answers the question a beginner actually has in front of a
chart — *the line is going up, is that good or is that risky?* Every stock page
and the market overview carry plain-English readings, each one saying what the
data shows, what a veteran does with it, and **what would make that reading
wrong**. Tones are limited to constructive / caution / neutral: interpretations,
never instructions (enforced by a test that fails on advice-like phrasing).

## Stack

`backend/` — **FastAPI + DuckDB + yfinance**: warms the full S&P 500 on startup
(priority tickers first), computes all analytics from cached daily bars.
`frontend/` — **Next.js (App Router) + Tailwind + Recharts + lightweight-charts**:
dark fintech workbench with a ⌘K palette over the whole universe.

## Run it

```bash
# 1 — backend (http://localhost:8000)
cd backend
python -m venv .venv && .venv\Scripts\Activate.ps1   # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

```bash
# 2 — frontend (http://localhost:3000)
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

First boot ingests ~500 tickers into DuckDB (~1–2 min; the dashboard is usable in
seconds — progress at `/health/data`). Tests: `cd backend && pytest`.

## Honest notes

- **Data** is end-of-day from Yahoo Finance via yfinance; intraday is delayed.
  Raw close is used for prices/affordability, adjusted close for returns.
- **Fundamentals** (`.info`) are flaky by nature — fetched on demand, cached a
  day, degrade gracefully.
- **S&P 500 membership** is a committed snapshot (`backend/app/data/`);
  regenerate with `python backend/scripts/build_sp500.py`.
- **Data trust:** ~5.5 years of daily history per name. Audit it yourself with
  `python backend/scripts/audit_data.py` — coverage, gaps vs the NYSE calendar,
  bad prices, and every flagged >40% single-day move. Recent IPOs legitimately
  have thin history; the app says "too few past cases" instead of inventing
  statistics.
- Next.js is deliberately pinned to 14.2.x; charts are Recharts +
  lightweight-charts rather than Tremor. Reasoning lives in commit history —
  deliberate, not oversight.

## Roadmap

Monte Carlo scenario cones · Claude-written Daily Brief (GitHub Actions cron) ·
editable watchlist · FRED macro feed.
