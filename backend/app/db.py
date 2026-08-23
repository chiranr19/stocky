# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""DuckDB access layer.

A single connection guarded by a lock. FastAPI runs sync endpoints in a thread
pool, and DuckDB connections are not safe to share across threads without
serialization — for a low-traffic learning app a module-level lock is the
simplest correct approach.
"""

from __future__ import annotations

import threading

import duckdb

from .config import settings

# Reentrant so `db_lock` can hold it while calling get_connection().
_lock = threading.RLock()
_con: duckdb.DuckDBPyConnection | None = None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    ticker    VARCHAR,
    date      DATE,
    open      DOUBLE,
    high      DOUBLE,
    low       DOUBLE,
    close     DOUBLE,
    adj_close DOUBLE,
    volume    BIGINT,
    PRIMARY KEY (ticker, date)
);

CREATE TABLE IF NOT EXISTS ingest_meta (
    ticker        VARCHAR PRIMARY KEY,
    covered_start DATE,
    covered_end   DATE,
    last_fetched  TIMESTAMP
);

-- Data-quality trail: anomalies, dropped rows, fetch errors. Surfaced by
-- /health/data so the UI can be honest about what it did and didn't get.
CREATE TABLE IF NOT EXISTS ingest_log (
    ts     TIMESTAMP,
    ticker VARCHAR,
    kind   VARCHAR,   -- 'anomaly' | 'bad_price' | 'fetch_error' | 'empty'
    detail VARCHAR
);

-- On-demand fundamentals cache (yfinance .info subset), refreshed ~daily.
CREATE TABLE IF NOT EXISTS stock_info (
    ticker       VARCHAR PRIMARY KEY,
    fetched_at   TIMESTAMP,
    payload_json VARCHAR
);

-- Followed Filers (v0.8): public insider (SEC Form 4) and congressional (STOCK
-- Act PTR) disclosures. Every row keeps its provenance URL; only rows that pass
-- the integrity pipeline land here — malformed/suspect ones go to ingest_log.
CREATE TABLE IF NOT EXISTS disclosed_trades (
    source      VARCHAR,   -- 'edgar' | 'house' | 'senate'
    filing_id   VARCHAR,   -- accession number / DocID (provenance key)
    filer       VARCHAR,   -- reporting owner / member name
    filer_role  VARCHAR,   -- 'Director, CEO' | 'Senator (R-AL)' | ...
    ticker      VARCHAR,
    asset_class VARCHAR,   -- 'equity' | 'option' | 'other' (only equity is priceable)
    action      VARCHAR,   -- 'buy' | 'sell' | 'grant' | 'other'
    trade_date  DATE,      -- when they traded
    filed_date  DATE,      -- when the public could first know (the lag tax anchor)
    shares      DOUBLE,    -- NULL when only a range is disclosed (congress)
    price       DOUBLE,    -- per-share (Form 4); NULL for congress
    value_lo    DOUBLE,    -- disclosed dollar range low  (congress); else shares*price
    value_hi    DOUBLE,    -- disclosed dollar range high (congress); else shares*price
    scheduled   BOOLEAN,   -- 10b5-1 pre-arranged plan (Form 4) — not a reaction
    url         VARCHAR,   -- link to the original official filing
    PRIMARY KEY (source, filing_id, ticker, trade_date, action)
);

-- Incremental-fetch watermark per (source, key). `key` is an issuer CIK for
-- EDGAR, a chamber/year for congress. Lets any failed run resume cleanly.
CREATE TABLE IF NOT EXISTS filer_meta (
    source           VARCHAR,
    key              VARCHAR,
    last_checked     TIMESTAMP,
    last_filing_date DATE,
    PRIMARY KEY (source, key)
);

-- Living watchlist (v0.9). Seeded once from config.WATCHLIST (+ DVA); after
-- that the DB is the source of truth. Remove = active FALSE (restorable), so
-- 'since added' history and provenance survive a hide/restore round-trip.
CREATE TABLE IF NOT EXISTS watchlist (
    ticker      VARCHAR PRIMARY KEY,
    added_at    DATE NOT NULL,       -- trading day it joined the list
    added_price DOUBLE,              -- close that day (NULL until data exists)
    source      VARCHAR NOT NULL,    -- 'seed' | 'user'
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    position    INTEGER NOT NULL     -- stable display order
);
"""


def _connect() -> duckdb.DuckDBPyConnection:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(settings.duckdb_path))
    con.execute(_SCHEMA)
    return con


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return the shared connection, creating it on first use."""
    global _con
    if _con is None:
        with _lock:
            if _con is None:
                _con = _connect()
    return _con


class db_lock:  # noqa: N801 - used as a context manager, reads like `with db_lock():`
    """Serialize access to the shared DuckDB connection."""

    def __enter__(self) -> duckdb.DuckDBPyConnection:
        _lock.acquire()
        return get_connection()

    def __exit__(self, *exc: object) -> None:
        _lock.release()
