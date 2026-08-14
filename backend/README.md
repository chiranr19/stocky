# Stocky — Backend

FastAPI service. Warms the full S&P 500 from yfinance into DuckDB, computes
technical metrics + a per-sector screener, and serves the dashboard's data.

## Setup

```bash
cd backend
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# macOS / Linux:         source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # optional; sensible defaults work out of the box
```

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

On startup a background thread warms the whole universe (priority tickers first).
Watch `GET /health/data` for progress and data freshness. Interactive docs at
http://localhost:8000/docs.

### Endpoints

- `GET /overview` · `GET /sectors?budget=` · `GET /movers?type=&budget=&limit=`
- `GET /riskmap?budget=` · `GET /signals?budget=` · `GET /compare?tickers=A,B,C`
- `GET /stock/{ticker}` · `GET /stock/{ticker}/fundamentals`
- `GET /timemachine?ticker=&date=&amount=` · `GET /pulse` · `GET /calendar`
- `GET /universe` · `GET /health/data`

## Test

```bash
pytest    # sim math, metrics (RSI/crosses/vol/correlation), screener, trading calendar
```

## How it works

1. **Warm-up** (`services/market.py`): chunked, retrying, idempotent `(ticker, date)`
   upserts into DuckDB; range-aware back-fill; anomalies logged to `ingest_log`.
2. **Metrics** (`services/metrics.py`, pure/tested): MA50/200, Wilder RSI(14), 90d
   volatility, 1m/3m/1y returns, crosses, gaps, 52w range, correlation, histograms.
   Raw `close` for prices/affordability; `adj_close` for returns/volatility.
3. **Screener** (`services/screener.py`, pure/tested): per-sector percentile score —
   Momentum 40 / Stability 30 / Resilience 20 / Liquidity 10, over the affordable,
   liquid (≥ $5M/day) subset.
4. **Orchestration** (`services/analytics.py`): builds every payload from an
   in-process metrics cache keyed by (data date, warm progress). Read-only over
   cached rows — never fetches inline.

Reference data lives in `app/data/` (S&P 500 snapshot, macro dates). The DuckDB
file lives at `backend/data/stocky.duckdb` (gitignored). Refresh the S&P 500
membership with `python scripts/build_sp500.py`.
