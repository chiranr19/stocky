"""On-demand fundamentals via yfinance ``.info``, cached ~1 day in DuckDB.

``.info`` is slow and occasionally flaky, so it is never bulk-fetched — only
pulled for a single ticker when its deep-dive page asks, then cached.
"""

from __future__ import annotations

import datetime as dt
import json

import yfinance as yf

from ..db import db_lock
from ..models import Fundamentals

_TTL = dt.timedelta(days=1)

# yfinance .info key -> our field name.
_FIELDS = {
    "marketCap": "market_cap",
    "trailingPE": "trailing_pe",
    "forwardPE": "forward_pe",
    "beta": "beta",
    "dividendYield": "dividend_yield",
    "profitMargins": "profit_margin",
    "shortPercentOfFloat": "short_percent_of_float",
    "fiftyTwoWeekHigh": "fifty_two_week_high",
    "fiftyTwoWeekLow": "fifty_two_week_low",
}


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(tzinfo=None)


def _read_cache(ticker: str) -> tuple[dt.datetime, dict] | None:
    with db_lock() as con:
        row = con.execute(
            "SELECT fetched_at, payload_json FROM stock_info WHERE ticker = ?", [ticker]
        ).fetchone()
    if row is None:
        return None
    return row[0], json.loads(row[1])


def _write_cache(ticker: str, payload: dict) -> None:
    with db_lock() as con:
        con.execute(
            """
            INSERT OR REPLACE INTO stock_info (ticker, fetched_at, payload_json)
            VALUES (?, ?, ?)
            """,
            [ticker, _utcnow(), json.dumps(payload)],
        )


def _extract(info: dict) -> dict:
    return {field: info.get(key) for key, field in _FIELDS.items()}


def get_fundamentals(ticker: str) -> Fundamentals:
    ticker = ticker.upper()
    cached = _read_cache(ticker)
    fetched_at: dt.datetime
    if cached is not None and (_utcnow() - cached[0]) < _TTL:
        fetched_at, payload = cached
    else:
        try:
            info = yf.Ticker(ticker).info or {}
            payload = _extract(info)
            _write_cache(ticker, payload)
            fetched_at = _utcnow()
        except Exception:
            if cached is not None:  # serve stale on failure
                fetched_at, payload = cached
            else:
                return Fundamentals(ticker=ticker, available=False)

    available = any(v is not None for v in payload.values())
    return Fundamentals(ticker=ticker, available=available, fetched_at=fetched_at, **payload)
