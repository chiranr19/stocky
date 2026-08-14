"""Application configuration and static reference data.

The S&P 500 universe, company names, and sector map are loaded from a committed
snapshot (``app/data/sp500_constituents.json``) rather than yfinance's flaky
``.info`` endpoint — this keeps the app fast and works offline once prices are
cached. Regenerate the snapshot with ``python scripts/build_sp500.py``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = Path(__file__).resolve().parent / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_BACKEND_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Where the DuckDB file and any other artifacts live (gitignored).
    data_dir: Path = _BACKEND_ROOT / "data"

    # Cache freshness: within this window we serve from DuckDB without re-fetching.
    cache_ttl_seconds: int = 900

    # Everything gets benchmarked against this ("what if you'd bought VOO instead").
    benchmark: str = "VOO"

    # Frontend origins allowed to call the API.
    cors_origins: list[str] = ["http://localhost:3000"]

    # On startup, kick off a background thread that warms the whole universe.
    warm_on_start: bool = True

    # How many tickers per yfinance bulk download.
    ingest_chunk_size: int = 100

    # Reserved for the Daily Brief job. Never hardcode a key.
    anthropic_api_key: str = ""

    @property
    def duckdb_path(self) -> Path:
        return self.data_dir / "stocky.duckdb"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


# --------------------------------------------------------------------------- #
# S&P 500 universe (loaded from committed snapshot)
# --------------------------------------------------------------------------- #
def _load_sp500() -> dict:
    path = _DATA_DIR / "sp500_constituents.json"
    with path.open(encoding="utf-8") as f:
        return json.load(f)


_SP500 = _load_sp500()
SP500_SNAPSHOT_DATE: str = _SP500["snapshot_date"]
CONSTITUENTS: list[dict[str, str]] = _SP500["constituents"]

UNIVERSE: list[str] = [c["ticker"] for c in CONSTITUENTS]
NAME_BY_TICKER: dict[str, str] = {c["ticker"]: c["name"] for c in CONSTITUENTS}
SECTOR_BY_TICKER: dict[str, str] = {c["ticker"]: c["sector"] for c in CONSTITUENTS}
SUBINDUSTRY_BY_TICKER: dict[str, str] = {
    c["ticker"]: c["sub_industry"] for c in CONSTITUENTS
}


# --------------------------------------------------------------------------- #
# Sectors → SPDR ETFs
# --------------------------------------------------------------------------- #
# GICS sector name (matches the constituents file) → its SPDR ETF proxy, a short
# UI label, and an approximate S&P 500 weight (only used to size heatmap tiles).
SECTORS: list[dict[str, object]] = [
    {"gics": "Information Technology", "etf": "XLK", "label": "Technology", "weight": 0.30},
    {"gics": "Communication Services", "etf": "XLC", "label": "Communication", "weight": 0.09},
    {"gics": "Consumer Discretionary", "etf": "XLY", "label": "Consumer Disc.", "weight": 0.11},
    {"gics": "Financials", "etf": "XLF", "label": "Financials", "weight": 0.13},
    {"gics": "Health Care", "etf": "XLV", "label": "Health Care", "weight": 0.12},
    {"gics": "Industrials", "etf": "XLI", "label": "Industrials", "weight": 0.08},
    {"gics": "Consumer Staples", "etf": "XLP", "label": "Staples", "weight": 0.06},
    {"gics": "Energy", "etf": "XLE", "label": "Energy", "weight": 0.04},
    {"gics": "Utilities", "etf": "XLU", "label": "Utilities", "weight": 0.025},
    {"gics": "Real Estate", "etf": "XLRE", "label": "Real Estate", "weight": 0.023},
    {"gics": "Materials", "etf": "XLB", "label": "Materials", "weight": 0.022},
]
ETF_BY_GICS: dict[str, str] = {s["gics"]: str(s["etf"]) for s in SECTORS}
GICS_BY_ETF: dict[str, str] = {str(s["etf"]): str(s["gics"]) for s in SECTORS}
LABEL_BY_GICS: dict[str, str] = {s["gics"]: str(s["label"]) for s in SECTORS}
SECTOR_ETFS_LIST: list[str] = [str(s["etf"]) for s in SECTORS]


# --------------------------------------------------------------------------- #
# Macro context tickers (fear gauge + rates) — same ingestion pipeline.
# --------------------------------------------------------------------------- #
MACRO_TICKERS: list[str] = ["^VIX", "^TNX"]
MACRO_META: dict[str, dict[str, str]] = {
    "^VIX": {"label": "VIX", "name": "CBOE Volatility Index (fear gauge)", "unit": "level"},
    "^TNX": {"label": "10Y Yield", "name": "10-Year Treasury Yield", "unit": "percent"},
}


# --------------------------------------------------------------------------- #
# Watchlist (seeded highlights, shown compact on the Pulse page)
# --------------------------------------------------------------------------- #
WATCHLIST: list[str] = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "AMD", "META", "VOO",
]

# Friendly overrides for the watchlist (constituents file names are used for the
# rest of the universe; VOO isn't in the S&P 500 constituents list).
COMPANY_NAMES: dict[str, str] = {
    "NVDA": "NVIDIA",
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "TSLA": "Tesla",
    "AMD": "Advanced Micro Devices",
    "META": "Meta Platforms",
    "VOO": "Vanguard S&P 500 ETF",
}


def display_name(ticker: str) -> str:
    """Best available human name for a ticker."""
    return COMPANY_NAMES.get(ticker) or NAME_BY_TICKER.get(ticker) or ticker


def sector_of(ticker: str) -> str | None:
    """GICS sector for an S&P 500 member (None for ETFs / macro tickers)."""
    return SECTOR_BY_TICKER.get(ticker)


# Warm these first so the dashboard is usable within seconds; the rest of the
# universe streams in behind them.
PRIORITY_TICKERS: list[str] = list(
    dict.fromkeys([*WATCHLIST, settings.benchmark, *SECTOR_ETFS_LIST, *MACRO_TICKERS])
)

# Full set the ingester knows about (priority first, then the rest of the S&P).
ALL_TICKERS: list[str] = list(dict.fromkeys([*PRIORITY_TICKERS, *UNIVERSE]))


# --------------------------------------------------------------------------- #
# Analysis / screener knobs (documented so the Learning layer can explain them)
# --------------------------------------------------------------------------- #
# Pulse card flag thresholds.
UNUSUAL_VOLUME_RATIO = 1.5  # today's volume vs 30-day average
BIG_MOVER_PCT = 4.0  # absolute daily % move

# Affordability.
DEFAULT_BUDGET = 200.0  # user's real max share price
BUDGET_PRESETS = [50, 100, 200, 500]  # None (in the UI) = no cap

# Technical windows.
MA_SHORT = 50
MA_LONG = 200
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70.0
RSI_OVERSOLD = 30.0
VOL_WINDOW = 90  # trading days for annualized volatility
CROSS_LOOKBACK = 10  # sessions to still call a golden/death cross "recent"
GAP_PCT = 2.0  # |open vs prior close| to flag a gap

# Screener.
MIN_DOLLAR_VOLUME = 5_000_000.0  # 20-day avg $ volume liquidity gate
SCORE_WEIGHTS = {
    "momentum": 0.40,   # 3-month return percentile (in-sector) + above-MA bonuses
    "stability": 0.30,  # inverse of 90-day volatility percentile
    "resilience": 0.20, # shallower 1-year drawdown percentile
    "liquidity": 0.10,  # dollar-volume percentile
}

# Data-quality guard: a single-day move larger than this is logged as an anomaly.
ANOMALY_DAY_MOVE_PCT = 40.0
