"""Market data service: yfinance ingestion + DuckDB caching.

Design goals:
  * **Idempotent ingestion** — re-running never duplicates rows (PK upsert).
  * **Cache-first** — within ``CACHE_TTL_SECONDS`` we serve straight from DuckDB
    and never touch the network.
  * **Range-aware** — we track [covered_start, covered_end] per ticker so an older
    Time Machine date triggers a wider back-fill.
  * **Warm-up aware** — the full S&P 500 is ingested in chunks on a background
    thread, priority tickers first, with progress exposed via /health/data.
"""

from __future__ import annotations

import datetime as dt
import json
import threading
import time
from dataclasses import dataclass, field

import pandas as pd
import yfinance as yf

from ..config import (
    ALL_TICKERS,
    ANOMALY_DAY_MOVE_PCT,
    PRIORITY_TICKERS,
    settings,
)
from ..db import db_lock

_PRICE_COLUMNS = ["ticker", "date", "open", "high", "low", "close", "adj_close", "volume"]

# Lookback deep enough for the Entry Radar's historical-echo study: MA200
# warm-up (~290 calendar days) + ~4.5 years of detectable setups + the forward
# window. Widening this triggers a one-time universe back-fill on next warm-up.
HISTORY_LOOKBACK = dt.timedelta(days=2000)


class MarketDataError(RuntimeError):
    """Raised when data cannot be fetched or is unavailable for a ticker."""


def _utcnow() -> dt.datetime:
    """Timezone-naive UTC now (DuckDB TIMESTAMP columns are naive)."""
    return dt.datetime.now(dt.UTC).replace(tzinfo=None)


# --------------------------------------------------------------------------- #
# yfinance download + normalization
# --------------------------------------------------------------------------- #
def _download(tickers: list[str], start: dt.date, end: dt.date) -> pd.DataFrame:
    """Download daily bars for ``tickers`` → long-format DataFrame.

    Columns: ticker, date, open, high, low, close, adj_close, volume.
    yfinance's ``end`` is exclusive, so we add a day to include ``end`` itself.
    """
    if not tickers:
        return pd.DataFrame(columns=_PRICE_COLUMNS)

    raw = yf.download(
        tickers=tickers,
        start=start.isoformat(),
        end=(end + dt.timedelta(days=1)).isoformat(),
        auto_adjust=False,
        group_by="ticker",
        progress=False,
        threads=True,
    )
    if raw is None or raw.empty:
        return pd.DataFrame(columns=_PRICE_COLUMNS)

    frames: list[pd.DataFrame] = []
    multi = isinstance(raw.columns, pd.MultiIndex)
    for ticker in tickers:
        if multi:
            if ticker not in raw.columns.get_level_values(0):
                continue
            df = raw[ticker].copy()
        else:
            df = raw.copy()

        df = df.dropna(how="all")
        if df.empty:
            continue

        df = df.reset_index()
        df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
        if "date" not in df.columns and "datetime" in df.columns:
            df = df.rename(columns={"datetime": "date"})
        if "adj_close" not in df.columns:  # auto_adjust=True fallback
            df["adj_close"] = df["close"]

        df["ticker"] = ticker
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["volume"] = df["volume"].fillna(0).astype("int64")
        frames.append(df[_PRICE_COLUMNS])

    if not frames:
        return pd.DataFrame(columns=_PRICE_COLUMNS)
    return pd.concat(frames, ignore_index=True)


def _download_with_retry(tickers: list[str], start: dt.date, end: dt.date) -> pd.DataFrame:
    """One retry on transient yfinance failures; errors are logged, not raised."""
    for attempt in (1, 2):
        try:
            df = _download(tickers, start, end)
            if not df.empty or attempt == 2:
                return df
        except Exception as exc:  # network/parse hiccup — log and retry once
            _log("fetch_error", ",".join(tickers[:3]) + "…", f"attempt {attempt}: {exc}"[:180])
            if attempt == 2:
                return pd.DataFrame(columns=_PRICE_COLUMNS)
        time.sleep(1.0)
    return pd.DataFrame(columns=_PRICE_COLUMNS)


# --------------------------------------------------------------------------- #
# Validation + data-quality log
# --------------------------------------------------------------------------- #
def _log(kind: str, ticker: str, detail: str) -> None:
    with db_lock() as con:
        con.execute(
            "INSERT INTO ingest_log (ts, ticker, kind, detail) VALUES (?, ?, ?, ?)",
            [_utcnow(), ticker, kind, detail],
        )


def _validate(df: pd.DataFrame) -> pd.DataFrame:
    """Drop unusable rows and log (but keep) suspicious ones.

    Real >40% single-day moves happen (earnings crashes, meme squeezes), so we
    log them for transparency rather than silently discarding — honest data.
    """
    if df.empty:
        return df

    bad = df["close"].isna() | (df["close"] <= 0)
    if bad.any():
        for ticker in df.loc[bad, "ticker"].unique():
            _log("bad_price", str(ticker), f"{int(bad.sum())} null/≤0 close rows dropped")
        df = df.loc[~bad].copy()

    for ticker, group in df.groupby("ticker"):
        moves = group.sort_values("date")["close"].pct_change().abs() * 100.0
        for idx in moves.index[moves > ANOMALY_DAY_MOVE_PCT]:
            _log(
                "anomaly",
                str(ticker),
                f"{df.loc[idx, 'date']}: {moves.loc[idx]:.0f}% single-day move",
            )
    return df


# --------------------------------------------------------------------------- #
# Cache bookkeeping
# --------------------------------------------------------------------------- #
def _needs_fetch(ticker: str, start: dt.date, end: dt.date) -> bool:
    with db_lock() as con:
        row = con.execute(
            "SELECT covered_start, covered_end, last_fetched FROM ingest_meta WHERE ticker = ?",
            [ticker],
        ).fetchone()

    if row is None:
        return True
    covered_start, covered_end, last_fetched = row
    if start < covered_start or end > covered_end:
        return True  # requested a wider window than we have

    age = _utcnow() - last_fetched
    return age.total_seconds() > settings.cache_ttl_seconds


def _store(df: pd.DataFrame) -> None:
    """Idempotent upsert of price rows keyed by (ticker, date)."""
    if df.empty:
        return
    with db_lock() as con:
        con.register("incoming_prices", df)
        con.execute(
            f"INSERT OR REPLACE INTO prices ({', '.join(_PRICE_COLUMNS)}) "
            f"SELECT {', '.join(_PRICE_COLUMNS)} FROM incoming_prices"
        )
        con.unregister("incoming_prices")


def _update_meta(ticker: str, start: dt.date, end: dt.date) -> None:
    with db_lock() as con:
        con.execute(
            """
            INSERT INTO ingest_meta (ticker, covered_start, covered_end, last_fetched)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (ticker) DO UPDATE SET
                covered_start = LEAST(ingest_meta.covered_start, EXCLUDED.covered_start),
                covered_end   = GREATEST(ingest_meta.covered_end, EXCLUDED.covered_end),
                last_fetched  = EXCLUDED.last_fetched
            """,
            [ticker, start, end, _utcnow()],
        )


def _ingest(tickers: list[str], start: dt.date, end: dt.date) -> set[str]:
    """Fetch → validate → store the stale subset of ``tickers``.

    Returns the set of tickers that actually produced rows.
    """
    stale = [t for t in tickers if _needs_fetch(t, start, end)]
    if not stale:
        return set()

    df = _validate(_download_with_retry(stale, start, end))
    _store(df)
    got = set(df["ticker"].unique()) if not df.empty else set()
    for ticker in stale:
        _update_meta(ticker, start, end)  # honor TTL even for empties
        if ticker not in got:
            _log("empty", ticker, "no rows returned")
    return got


def _ensure(tickers: list[str], start: dt.date, end: dt.date) -> None:
    _ingest(tickers, start, end)


# --------------------------------------------------------------------------- #
# Background warm-up of the whole universe
# --------------------------------------------------------------------------- #
@dataclass
class WarmState:
    status: str = "idle"  # idle | warming | ready
    total: int = len(ALL_TICKERS)
    loaded: int = 0
    started_at: dt.datetime | None = None
    finished_at: dt.datetime | None = None
    failed: list[str] = field(default_factory=list)


_warm_state = WarmState()
_warm_lock = threading.Lock()
_warm_thread: threading.Thread | None = None


def warm_state() -> WarmState:
    return _warm_state


def _chunks(seq: list[str], size: int) -> list[list[str]]:
    return [seq[i : i + size] for i in range(0, len(seq), size)]


def warm_universe() -> None:
    """Ingest ALL_TICKERS (priority first) in chunks. Idempotent & resumable."""
    global _warm_state
    with _warm_lock:
        if _warm_state.status == "warming":
            return
        _warm_state = WarmState(status="warming", started_at=_utcnow())

    end = dt.date.today()
    start = end - HISTORY_LOOKBACK
    failed: list[str] = []
    loaded = 0

    for chunk in _chunks(ALL_TICKERS, settings.ingest_chunk_size):
        got = _ingest(chunk, start, end)
        for ticker in chunk:
            # Only count as failed if we have nothing cached at all for it.
            if ticker not in got and not _has_any_rows(ticker):
                failed.append(ticker)
        loaded += len(chunk)
        _warm_state.loaded = loaded
        _warm_state.failed = failed

    _warm_state.status = "ready"
    _warm_state.finished_at = _utcnow()


def start_background_warm() -> None:
    global _warm_thread
    with _warm_lock:
        if _warm_state.status == "warming":
            return
        if _warm_thread is not None and _warm_thread.is_alive():
            return
        _warm_thread = threading.Thread(target=warm_universe, name="warm", daemon=True)
        _warm_thread.start()


def _has_any_rows(ticker: str) -> bool:
    with db_lock() as con:
        row = con.execute(
            "SELECT 1 FROM prices WHERE ticker = ? LIMIT 1", [ticker]
        ).fetchone()
    return row is not None


# --------------------------------------------------------------------------- #
# Public read API
# --------------------------------------------------------------------------- #
def get_history(ticker: str, start: dt.date, end: dt.date) -> pd.DataFrame:
    """Cached daily bars for one ticker, fetching/back-filling as needed.

    Indexed by ``date`` (ascending): open, high, low, close, adj_close, volume.
    """
    ticker = ticker.upper()
    _ensure([ticker], start, end)
    with db_lock() as con:
        df = con.execute(
            """
            SELECT date, open, high, low, close, adj_close, volume
            FROM prices WHERE ticker = ? AND date BETWEEN ? AND ? ORDER BY date
            """,
            [ticker, start, end],
        ).df()

    if df.empty:
        raise MarketDataError(
            f"No price data available for '{ticker}'. Check the symbol, the date "
            f"range, or your network connection to yfinance."
        )
    df["date"] = pd.to_datetime(df["date"])
    return df.set_index("date")


def get_histories(tickers: list[str], start: dt.date, end: dt.date) -> dict[str, pd.DataFrame]:
    """Batch version of :func:`get_history`; skips tickers with no data."""
    tickers = [t.upper() for t in tickers]
    _ensure(tickers, start, end)

    out: dict[str, pd.DataFrame] = {}
    with db_lock() as con:
        for ticker in tickers:
            df = con.execute(
                """
                SELECT date, open, high, low, close, adj_close, volume
                FROM prices WHERE ticker = ? AND date BETWEEN ? AND ? ORDER BY date
                """,
                [ticker, start, end],
            ).df()
            if df.empty:
                continue
            df["date"] = pd.to_datetime(df["date"])
            out[ticker] = df.set_index("date")
    return out


def read_cached(tickers: list[str], start: dt.date, end: dt.date) -> dict[str, pd.DataFrame]:
    """Read ONLY what's already in DuckDB — never triggers a fetch.

    Used by the heavy analytics endpoints (screener, riskmap, scanners) which run
    over the whole universe and rely on the background warm-up rather than
    fetching hundreds of tickers inline.
    """
    tickers = [t.upper() for t in tickers]
    out: dict[str, pd.DataFrame] = {}
    with db_lock() as con:
        for ticker in tickers:
            df = con.execute(
                """
                SELECT date, open, high, low, close, adj_close, volume
                FROM prices WHERE ticker = ? AND date BETWEEN ? AND ? ORDER BY date
                """,
                [ticker, start, end],
            ).df()
            if df.empty:
                continue
            df["date"] = pd.to_datetime(df["date"])
            out[ticker] = df.set_index("date")
    return out


# --------------------------------------------------------------------------- #
# Data health
# --------------------------------------------------------------------------- #
def data_health() -> dict:
    """Raw counts for /health/data; freshness vs the calendar is added by the router."""
    with db_lock() as con:
        loaded = con.execute("SELECT COUNT(DISTINCT ticker) FROM prices").fetchone()[0]
        latest = con.execute("SELECT MAX(date) FROM prices").fetchone()[0]
        last_ingest = con.execute("SELECT MAX(last_fetched) FROM ingest_meta").fetchone()[0]
        anomalies = con.execute(
            "SELECT COUNT(*) FROM ingest_log WHERE kind = 'anomaly'"
        ).fetchone()[0]
        # Depth proof: how much history each ticker actually has.
        depth = con.execute(
            """
            SELECT median(n), min(n), arg_min(ticker, n), min(first_date)
            FROM (
                SELECT ticker, COUNT(*) AS n, MIN(date) AS first_date
                FROM prices GROUP BY ticker
            )
            """
        ).fetchone()

    median_sessions, min_sessions, thinnest, earliest = depth or (None, None, None, None)
    span_days = (latest - earliest).days if (latest and earliest) else None

    state = _warm_state
    return {
        "status": state.status,
        "tickers_loaded": int(loaded or 0),
        "tickers_total": state.total,
        "priority_total": len(PRIORITY_TICKERS),
        "warm_loaded": state.loaded,
        "latest_trading_date": latest,
        "last_ingest_at": last_ingest,
        "anomalies_count": int(anomalies or 0),
        "failed_tickers": list(state.failed),
        "history_span_days": span_days,
        "median_sessions": int(median_sessions) if median_sessions else None,
        "thinnest_ticker": thinnest,
        "thinnest_sessions": int(min_sessions) if min_sessions else None,
    }
