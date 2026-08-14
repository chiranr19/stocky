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
