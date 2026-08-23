# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""The living watchlist — the user's editable cast, persisted in DuckDB.

Seeded once from ``config.WATCHLIST`` (plus DVA); after that the ``watchlist``
table is the source of truth. Removing a name sets ``active = FALSE`` rather
than deleting it, so a hide/restore round-trip preserves the original
``added_at`` (and therefore an honest "since you added it" number).

Read-mostly, low-traffic; every touch goes through ``db_lock``.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass

import pandas as pd

from ..config import WATCHLIST
from ..db import db_lock
from . import market

# A deliberately loose ticker shape: letters, digits, dot, dash, caret (for the
# odd class share / index). Anything else is rejected before a network fetch.
_TICKER_RE = re.compile(r"^[A-Z0-9.\-^]{1,10}$")

# DVA (DaVita) — the user's first self-directed pick, seeded as a 'user' row so
# it never demands a curated role (its story comes from the archetype engine).
_SEED_USER: list[str] = ["DVA"]


@dataclass(frozen=True)
class WatchlistEntry:
    ticker: str
    added_at: dt.date
    added_price: float | None
    source: str  # 'seed' | 'user'
    active: bool
    position: int


def _last_close(con, ticker: str) -> float | None:
    row = con.execute(
        "SELECT close FROM prices WHERE ticker = ? ORDER BY date DESC LIMIT 1",
        [ticker],
    ).fetchone()
    return float(row[0]) if row and row[0] is not None else None


def _seed(con) -> None:
    """Populate the table once, idempotently. No module-level flag — the test
    suite swaps DBs per test, so this re-checks with a cheap COUNT each call."""
    count = con.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]
    if count:
        return
    today = dt.date.today()
    seeds = [(t, "seed") for t in WATCHLIST] + [(t, "user") for t in _SEED_USER]
    for pos, (ticker, source) in enumerate(seeds):
        con.execute(
            """
            INSERT INTO watchlist (ticker, added_at, added_price, source, active, position)
            VALUES (?, ?, ?, ?, TRUE, ?)
            ON CONFLICT (ticker) DO NOTHING
            """,
            [ticker, today, _last_close(con, ticker), source, pos],
        )


def _row_to_entry(row) -> WatchlistEntry:
    ticker, added_at, added_price, source, active, position = row
    return WatchlistEntry(
        ticker=ticker,
        added_at=added_at,
        added_price=float(added_price) if added_price is not None else None,
        source=source,
        active=bool(active),
        position=int(position),
    )


def _select(con, *, active: bool) -> list[WatchlistEntry]:
    rows = con.execute(
        """
        SELECT ticker, added_at, added_price, source, active, position
        FROM watchlist WHERE active = ? ORDER BY position
        """,
        [active],
    ).fetchall()
    return [_row_to_entry(r) for r in rows]


def tickers() -> list[str]:
    """Active watchlist tickers, in display order (seeds it on first call)."""
    with db_lock() as con:
        _seed(con)
        return [e.ticker for e in _select(con, active=True)]


def entries() -> list[WatchlistEntry]:
    """Active entries; lazily back-fills a NULL added_price once data exists."""
    with db_lock() as con:
        _seed(con)
        out = _select(con, active=True)
        for e in out:
            if e.added_price is None:
                px = _last_close(con, e.ticker)
                if px is not None:
                    con.execute(
                        "UPDATE watchlist SET added_price = ? WHERE ticker = ?",
                        [px, e.ticker],
                    )
        return _select(con, active=True) if any(e.added_price is None for e in out) else out


def hidden() -> list[WatchlistEntry]:
    """Removed (inactive) entries, restorable via add()."""
    with db_lock() as con:
        _seed(con)
        return _select(con, active=False)


def _fetch_history(ticker: str) -> pd.DataFrame:
    """The 2000-day history fetch, isolated so tests can monkeypatch it.

    Fetching the full window (not just 430 days) means a freshly added name has
    the depth the Entry Radar's echo stats need, immediately.
    """
    end = dt.date.today()
    return market.get_history(ticker, end - market.HISTORY_LOOKBACK, end)


def add(ticker: str) -> WatchlistEntry:
    """Add or restore a ticker. Idempotent: an already-active name is returned
    unchanged. Raises ValueError for a malformed symbol, MarketDataError for one
    with no price data."""
    ticker = ticker.strip().upper()
    if not _TICKER_RE.match(ticker):
        raise ValueError(f"'{ticker}' is not a valid ticker symbol.")

    with db_lock() as con:
        _seed(con)
        existing = con.execute(
            "SELECT ticker, added_at, added_price, source, active, position "
            "FROM watchlist WHERE ticker = ?",
            [ticker],
        ).fetchone()
        if existing is not None and bool(existing[4]):
            return _row_to_entry(existing)  # already active — nothing to do

    # Fetch outside the lock (network). Raises MarketDataError for a bogus symbol.
    df = _fetch_history(ticker)
    added_at = df.index.max().date()
    added_price = float(df["close"].iloc[-1])

    with db_lock() as con:
        if existing is not None:
            # Restore: reactivate, PRESERVING the original added_at/price/source.
            con.execute(
                "UPDATE watchlist SET active = TRUE WHERE ticker = ?", [ticker]
            )
        else:
            next_pos = con.execute(
                "SELECT COALESCE(MAX(position), -1) + 1 FROM watchlist"
            ).fetchone()[0]
            # ON CONFLICT guards the narrow race where a concurrent add inserted
            # this same new ticker while we were fetching its history outside the
            # lock — reactivate rather than raise a duplicate-key error.
            con.execute(
                """
                INSERT INTO watchlist (ticker, added_at, added_price, source, active, position)
                VALUES (?, ?, ?, 'user', TRUE, ?)
                ON CONFLICT (ticker) DO UPDATE SET active = TRUE
                """,
                [ticker, added_at, added_price, next_pos],
            )
        row = con.execute(
            "SELECT ticker, added_at, added_price, source, active, position "
            "FROM watchlist WHERE ticker = ?",
            [ticker],
        ).fetchone()

    from . import analytics

    analytics.invalidate_metrics_cache()
    return _row_to_entry(row)


def remove(ticker: str) -> None:
    """Hide a ticker (restorable). Raises ValueError if it isn't on the list."""
    ticker = ticker.strip().upper()
    with db_lock() as con:
        _seed(con)
        found = con.execute(
            "SELECT 1 FROM watchlist WHERE ticker = ? AND active = TRUE", [ticker]
        ).fetchone()
        if found is None:
            raise ValueError(f"'{ticker}' is not on the watchlist.")
        con.execute("UPDATE watchlist SET active = FALSE WHERE ticker = ?", [ticker])

    from . import analytics

    analytics.invalidate_metrics_cache()
