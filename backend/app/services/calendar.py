# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Calendar service: upcoming earnings (best-effort) + static macro dates."""

from __future__ import annotations

import datetime as dt
import json
import threading
from pathlib import Path

import yfinance as yf

from ..config import DEFAULT_BUDGET, WATCHLIST, display_name, settings
from ..models import CalendarResponse, EarningsEvent, MacroEvent

_MACRO_PATH = Path(__file__).resolve().parent.parent / "data" / "macro_2026.json"

# Earnings dates are flaky/slow to fetch, so cache them in-process for the day.
_earnings_cache: dict = {"date": None, "events": []}
_earnings_lock = threading.Lock()


def _load_macro(today: dt.date) -> list[MacroEvent]:
    with _MACRO_PATH.open(encoding="utf-8") as f:
        data = json.load(f)
    events = [
        MacroEvent(date=dt.date.fromisoformat(e["date"]), label=e["label"], kind=e["kind"])
        for e in data["events"]
    ]
    return sorted([e for e in events if e.date >= today], key=lambda e: e.date)


def _next_earnings(ticker: str, today: dt.date) -> dt.date | None:
    try:
        df = yf.Ticker(ticker).get_earnings_dates(limit=8)
        if df is None or df.empty:
            return None
        future = [idx.date() for idx in df.index if idx.date() >= today]
        return min(future) if future else None
    except Exception:
        return None


def _watchlist_tickers() -> list[str]:
    try:
        from . import watchlist as watchlist_service

        return watchlist_service.tickers()
    except Exception:
        return list(WATCHLIST)


def _tracked_tickers() -> list[str]:
    """Watchlist plus a few top screener picks — kept small (earnings fetch is slow)."""
    tickers = [t for t in _watchlist_tickers() if t != settings.benchmark]
    try:
        from . import analytics

        scores = analytics._sector_scores(DEFAULT_BUDGET)
        for ranked in scores.values():
            if ranked:
                tickers.append(ranked[0].ticker)  # top pick per sector
    except Exception:
        pass
    return list(dict.fromkeys(tickers))


def _upcoming_earnings(today: dt.date) -> list[EarningsEvent]:
    with _earnings_lock:
        if _earnings_cache["date"] == today:
            return _earnings_cache["events"]

    events: list[EarningsEvent] = []
    for ticker in _tracked_tickers():
        d = _next_earnings(ticker, today)
        if d is not None:
            events.append(EarningsEvent(ticker=ticker, name=display_name(ticker), date=d))
    events.sort(key=lambda e: e.date)

    with _earnings_lock:
        _earnings_cache["date"] = today
        _earnings_cache["events"] = events
    return events


def build_calendar() -> CalendarResponse:
    today = dt.date.today()
    return CalendarResponse(
        earnings=_upcoming_earnings(today),
        macro=_load_macro(today),
    )
