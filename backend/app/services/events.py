# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""The what-changed engine — plain-English, day-over-day events on the watchlist.

Stateless: yesterday's view is simply today's frame minus its last row, so there
is no snapshot table to drift out of sync. Every event is template-assembled
from computed values (metrics + flags) and obeys the same no-advice copy law as
the rest of the teaching layer. Descriptions, never instructions.
"""

from __future__ import annotations

import datetime as dt
import threading
from dataclasses import dataclass

import pandas as pd

from ..config import BIG_MOVER_PCT, display_name
from ..models import WatchEvent
from . import flags as flags_service
from . import market
from .flags import GLOSSARY
from .metrics import StockMetrics, compute_metrics, pullback_series
from .screener import is_stale

_lock = threading.Lock()
_events_cache: dict = {"key": None, "value": None}

_PULLBACK_WINDOW = 63  # ~3 months, matching the radar's default lookback

# Per-ticker and global caps keep the feed a briefing, not a wall.
_MAX_PER_TICKER = 2
_MAX_TOTAL = 12
_VOL_JUMP_RATIO = 1.25
_VOL_JUMP_POINTS = 10.0


@dataclass(frozen=True)
class EventTemplate:
    code: str
    severity: int
    tone: str  # constructive | caution | neutral


# The registry lives HERE (never in flags.py, whose source is scanned for
# code="..." literals). flag_new/flag_cleared severities are derived per-flag.
TEMPLATES: dict[str, EventTemplate] = {
    "ma200_break": EventTemplate("ma200_break", 5, "caution"),
    "ma200_reclaim": EventTemplate("ma200_reclaim", 4, "constructive"),
    "death_cross_new": EventTemplate("death_cross_new", 4, "caution"),
    "golden_cross_new": EventTemplate("golden_cross_new", 3, "constructive"),
    "flag_new": EventTemplate("flag_new", 3, "caution"),
    "flag_cleared": EventTemplate("flag_cleared", 2, "constructive"),
    "vol_jump": EventTemplate("vol_jump", 3, "caution"),
    "new_high_52w": EventTemplate("new_high_52w", 2, "constructive"),
    "new_low_52w": EventTemplate("new_low_52w", 3, "caution"),
    "big_move": EventTemplate("big_move", 2, "neutral"),
    "rsi_flip": EventTemplate("rsi_flip", 2, "neutral"),
}

_FLAG_SEVERITY = {"high": 4, "medium": 3, "low": 2}


def _depth(adj: pd.Series) -> float | None:
    if adj is None or len(adj) < _PULLBACK_WINDOW + 1:
        return None
    d = pullback_series(adj, _PULLBACK_WINDOW).iloc[-1]
    return None if pd.isna(d) else float(d)


def _ev(ticker: str, code: str, headline: str, detail: str, severity: int | None = None,
        tone: str | None = None) -> WatchEvent:
    t = TEMPLATES[code]
    return WatchEvent(
        ticker=ticker, name=display_name(ticker), code=code,
        headline=headline, detail=detail,
        tone=tone or t.tone, severity=severity if severity is not None else t.severity,
    )


def detect(ticker: str, today: StockMetrics | None, yday: StockMetrics | None,
           flags_today: dict[str, object], flags_yday: dict[str, object]) -> list[WatchEvent]:
    """All events for one ticker from today-vs-yesterday metric + flag views."""
    if today is None or yday is None:
        return []
    out: list[WatchEvent] = []

    # Trend line crossing — the headline change (sale ⇄ verdict).
    if yday.above_ma200 and not today.above_ma200:
        out.append(_ev(ticker, "ma200_break",
            f"{ticker} crossed below its 200-day: its dip just became a verdict.",
            f"The most-watched line separating an uptrend from a downtrend gave way "
            f"at {today.price:.2f}. Rules that work in uptrends stop working here."))
    elif not yday.above_ma200 and today.above_ma200:
        out.append(_ev(ticker, "ma200_reclaim",
            f"{ticker} reclaimed its 200-day: the sale rack is back inside the store.",
            f"Price closed above the long average again after a {today.change_pct:+.1f}% "
            f"session — a repaired trend, not a promise."))

    # Fresh crosses.
    if today.cross == "death" and yday.cross != "death":
        out.append(_ev(ticker, "death_cross_new",
            f"{ticker} printed a death cross.",
            "The 50-day average crossed below the 200-day — a widely watched, and "
            "famously late, confirmation that momentum turned down."))
    if today.cross == "golden" and yday.cross != "golden":
        out.append(_ev(ticker, "golden_cross_new",
            f"{ticker} printed a golden cross.",
            "The 50-day average crossed above the 200-day — a trend confirmation "
            "enough people watch to make it partly self-fulfilling. It lags."))

    # Flags appearing / clearing.
    new_codes = set(flags_today) - set(flags_yday)
    cleared_codes = set(flags_yday) - set(flags_today)
    for code in new_codes:
        f = flags_today[code]
        sev = _FLAG_SEVERITY.get(f.severity, 2) if f.kind == "risk" else 2
        tone = "caution" if f.kind == "risk" else "constructive"
        out.append(_ev(ticker, "flag_new",
            f"New flag on {ticker}: {f.label}.", f.why, severity=sev, tone=tone))
    for code in cleared_codes:
        f = flags_yday[code]
        if f.kind != "risk":
            continue  # only the clearing of a hazard is worth a line
        label = GLOSSARY.get(code, {}).get("label", f.label)
        out.append(_ev(ticker, "flag_cleared",
            f"{ticker} shed a warning: {label}.",
            "A risk pattern that was flagged yesterday is no longer present — the "
            "chart repaired that particular fault, at least for now."))

    # Volatility regime shift.
    if today.vol_90d is not None and yday.vol_90d is not None and yday.vol_90d > 0:
        if today.vol_90d >= yday.vol_90d * _VOL_JUMP_RATIO and \
           (today.vol_90d - yday.vol_90d) >= _VOL_JUMP_POINTS:
            out.append(_ev(ticker, "vol_jump",
                f"{ticker}'s volatility jumped {yday.vol_90d:.0f}→{today.vol_90d:.0f}%.",
                f"Typical weekly swings are now roughly ±{today.vol_90d / (52 ** 0.5):.0f}%. "
                "The ride got wilder before any story explained why."))

    # New extremes.
    if today.is_new_high_52w and not yday.is_new_high_52w:
        out.append(_ev(ticker, "new_high_52w",
            f"{ticker} tagged a fresh 52-week high.",
            "Nobody who owns it is holding a loss — clear air above, and no support "
            "directly beneath a new high."))
    if today.is_new_low_52w and not yday.is_new_low_52w:
        out.append(_ev(ticker, "new_low_52w",
            f"{ticker} tagged a fresh 52-week low.",
            "This is where value hunters look and where value traps live; the trend "
            "and the business decide which."))

    # Big daily move (skip if a more specific event already covers today).
    if abs(today.change_pct) >= BIG_MOVER_PCT:
        tone = "constructive" if today.change_pct > 0 else "caution"
        out.append(_ev(ticker, "big_move",
            f"{ticker} moved {today.change_pct:+.1f}% today.",
            "A move this size on one day usually means news, an earnings reaction, or "
            "an index change — heavy conviction, not necessarily the right call.",
            tone=tone))

    # RSI regime flip.
    if today.rsi_signal is not None and today.rsi_signal != yday.rsi_signal:
        word = "overbought" if today.rsi_signal == "overbought" else "oversold"
        out.append(_ev(ticker, "rsi_flip",
            f"{ticker} flipped to {word} (RSI {today.rsi14:.0f}).",
            "Momentum stretched into an extreme. It marks a stretched move, never a "
            "turn by itself — strong stocks stay stretched for weeks."))

    # Per-ticker cap, most urgent first.
    out.sort(key=lambda e: (-e.severity, e.code))
    return out[:_MAX_PER_TICKER]


def detect_from_frame(ticker: str, df: pd.DataFrame) -> list[WatchEvent]:
    """Build both day views from one frame and diff them."""
    df = df.sort_index()
    if len(df) < 2:
        return []
    today = compute_metrics(ticker, df)
    yday = compute_metrics(ticker, df.iloc[:-1])
    if today is None or yday is None:
        return []
    adj = df["adj_close"] if "adj_close" in df else df["close"]
    ft = {f.code: f for f in flags_service.evaluate(today, _depth(adj))}
    fy = {f.code: f for f in flags_service.evaluate(yday, _depth(adj.iloc[:-1]))}
    return detect(ticker, today, yday, ft, fy)


def build_events(
    tickers: list[str] | None = None, as_of: dt.date | None = None
) -> list[WatchEvent]:
    """Watchlist events since yesterday, capped and severity-ordered.

    Read-only over the cached price frames (add() already fetched them);
    memoized per analytics cache generation. ``as_of`` is the universe's newest
    session (the basket passes it): a frame whose last bar trails it — or the
    newest frame here — by more than STALE_SESSIONS is a stopped feed, and its
    frozen last bar is not news "since yesterday", so it emits nothing.
    """
    from . import analytics
    from . import watchlist as watchlist_service

    if tickers is None:
        try:
            tickers = watchlist_service.tickers()
        except Exception:
            tickers = []

    key = (analytics._cache["key"], tuple(tickers), as_of)
    with _lock:
        if _events_cache["key"] == key and _events_cache["value"] is not None:
            return _events_cache["value"]

    end = dt.date.today()
    start = end - market.HISTORY_LOOKBACK
    frames = {t: df for t, df in market.read_cached(tickers, start, end).items()
              if not df.empty}
    last_bar = {t: df.index.max().date() for t, df in frames.items()}
    newest = max([d for d in (as_of, *last_bar.values()) if d is not None], default=None)

    events: list[WatchEvent] = []
    for ticker in tickers:
        df = frames.get(ticker)
        if df is not None and not is_stale(last_bar[ticker], newest):
            events += detect_from_frame(ticker, df)

    # Most urgent first: severity, then biggest daily move, then ticker.
    events.sort(key=lambda e: (-e.severity, -abs(_headline_move(e.headline)), e.ticker))
    events = events[:_MAX_TOTAL]
    with _lock:
        _events_cache.update(key=key, value=events)
    return events


def _headline_move(headline: str) -> float:
    """Pull a signed % out of a headline for the secondary sort; 0 if none."""
    import re

    m = re.search(r"([+-]\d+(?:\.\d+)?)%", headline)
    return float(m.group(1)) if m else 0.0
