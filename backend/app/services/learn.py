# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""The watchlist through the teaching lens — powers /learn and the digest cast.

Read-only over the analytics metrics cache (never fetches inline), the same
contract the radar and screener honor. Every number is optional so a young
listing degrades to an honest "not enough history to measure" rather than
inventing a risk picture it doesn't have.
"""

from __future__ import annotations

import datetime as dt
import threading

import pandas as pd

from ..config import (
    MARKET_LAWS,
    RADAR_LOOKBACKS,
    ROLES_AS_OF,
    WATCHLIST,
    WATCHLIST_ROLES,
    display_name,
    settings,
)
from ..models import BasketMember, BasketResponse
from . import analytics
from . import archetypes
from . import flags as flags_service
from .metrics import (
    StockMetrics,
    correlation_matrix,
    mds_layout,
    moving_average,
    mst_edges,
)
from .radar import _analyze_one

# A member needs at least this many sessions to (a) sit on the risk map and
# (b) enter the correlation matrix. The matrix uses a common-window dropna, so a
# single thin series (XE at ~83 sessions) would otherwise collapse the window
# for everyone — the thin name is excluded and named in ``correlation_note``.
_MIN_HISTORY = 200
_SERIES_POINTS = 60  # downsampled 1-year path for the underwater/race charts

_lock = threading.Lock()
_basket_cache: dict = {"key": None, "value": None}


def _downsample_series(series: pd.Series, n: int = _SERIES_POINTS) -> pd.Series:
    """Evenly-spaced sample of the last ~year (index preserved), oldest → newest.
    Empty when there's no data. Shared by the race line and its trend barcode so
    they land on the same x-positions."""
    window = series.tail(252).dropna()
    if window.empty or len(window) <= n:
        return window
    idx = [round(i * (len(window) - 1) / (n - 1)) for i in range(n)]
    return window.iloc[idx]


def _downsample(series: pd.Series, n: int = _SERIES_POINTS) -> list[float]:
    return [round(float(x), 2) for x in _downsample_series(series, n)]


def _regime_1y(adj: pd.Series | None, sampled: pd.Series) -> list[bool]:
    """Above (True) / below its 200-day line at each ``sampled`` point — the trend
    barcode under the race chart. Aligned to series_1y's x-positions for free."""
    if adj is None or sampled.empty:
        return []
    ma200 = moving_average(adj, 200).reindex(sampled.index)
    return [bool(px > ma) if pd.notna(ma) else False for px, ma in zip(sampled, ma200)]


def _rain(adj: pd.Series | None, rain_dates: list[pd.Timestamp]) -> list[float | None]:
    """Daily % returns reindexed onto the shared rain calendar — None on days this
    name didn't trade. Raw (unclipped); the chart pins extreme dots at its edge so
    a hover still shows the true move."""
    if adj is None or len(adj) < 2 or not rain_dates:
        return []
    rets = adj.pct_change() * 100.0
    aligned = rets.reindex(pd.DatetimeIndex(rain_dates))
    return [None if pd.isna(v) else round(float(v), 2) for v in aligned]


def _since_added(series: pd.Series | None, added_at: dt.date | None) -> float | None:
    """% return from the first close on/after ``added_at`` to the latest. None if
    the window is under two sessions (or we have no data). Computed from the price
    series, never the possibly-NULL stored added_price, so a hide/restore never
    resets it flatteringly."""
    if series is None or added_at is None:
        return None
    window = series[series.index >= pd.Timestamp(added_at)].dropna()
    if len(window) < 2:
        return None
    return round((float(window.iloc[-1]) / float(window.iloc[0]) - 1.0) * 100.0, 1)


def _member(ticker: str, m: StockMetrics | None, adj: pd.Series | None,
            benchmark: pd.Series | None, entry=None,
            ticker_events: list | None = None,
            rain_dates: list | None = None) -> BasketMember:
    curated = WATCHLIST_ROLES.get(ticker)
    if curated is not None:
        base = dict(
            ticker=ticker,
            name=display_name(ticker),
            role=curated["role"],
            group=curated["group"],
            role_story=curated["story"],
            role_lesson=curated["lesson"],
            role_source="curated",
        )
    else:
        # Uncurated (user-added): derive a character from the numbers.
        arch = archetypes.assign(m, len(adj) if adj is not None else 0)
        base = dict(
            ticker=ticker,
            name=display_name(ticker),
            role=arch["role"],
            group=arch["group"],
            role_story=arch["story"],
            role_lesson=arch["lesson"],
            role_source="archetype",
        )
    added_at = getattr(entry, "added_at", None)
    base["source"] = getattr(entry, "source", "seed")
    base["added_at"] = added_at

    # Study-viz payloads (computed once; shared by both return paths). The race
    # line, its trend barcode, and the rain strip all derive from here.
    sampled = _downsample_series(adj) if adj is not None else pd.Series(dtype=float)
    base["series_1y"] = [round(float(x), 2) for x in sampled]
    first = sampled.index[0] if not sampled.empty else None
    base["series_start"] = first.date() if hasattr(first, "date") else None
    base["regime_1y"] = _regime_1y(adj, sampled)
    base["rain"] = _rain(adj, rain_dates or [])

    evts = ticker_events or []
    attention_base = 6 * max((e.severity for e in evts), default=0) + 2 * len(evts)

    has_history = adj is not None and len(adj) >= _MIN_HISTORY
    measurable = m is not None and m.ret_1y is not None and has_history
    if m is None:
        return BasketMember(**base, attention=float(attention_base), measurable=False)

    depth_pct: float | None = None
    echo = None
    if adj is not None:
        analyzed = _analyze_one(m, adj, RADAR_LOOKBACKS["3m"], benchmark)
        if analyzed is not None:
            depth_pct, _rank, echo = analyzed

    found = flags_service.evaluate(m, depth_pct)
    attention = attention_base + flags_service.risk_score(found)

    return BasketMember(
        **base,
        price=m.price,
        change_pct=m.change_pct,
        vol_90d=m.vol_90d,
        ret_1y=m.ret_1y,
        above_ma200=m.above_ma200,
        depth_pct=round(depth_pct, 1) if depth_pct is not None else None,
        max_drawdown_1y=m.max_drawdown_1y,
        range_52w_position=m.range_52w_position,
        since_added_pct=_since_added(adj, added_at),
        since_added_voo_pct=_since_added(benchmark, added_at),
        spark=m.spark,
        echo=echo,
        flag_codes=[f.code for f in found],
        attention=round(attention, 1),
        measurable=measurable,
    )


def _build(
    metrics: dict[str, StockMetrics],
    closes: dict[str, pd.Series],
    latest: dt.date,
    tickers: list[str] | None = None,
    entries: dict | None = None,
    events: list | None = None,
) -> BasketResponse:
    order = tickers if tickers is not None else WATCHLIST
    entries = entries or {}
    events = events or []
    by_ticker: dict[str, list] = {}
    for ev in events:
        by_ticker.setdefault(ev.ticker, []).append(ev)

    benchmark = closes.get(settings.benchmark)
    # The shared trading calendar every rain strip aligns to: the benchmark's last
    # 60 sessions (the canonical market days). Members reindex onto it.
    rain_dates = list(benchmark.dropna().index[-60:]) if benchmark is not None else []
    members = [
        _member(t, metrics.get(t), closes.get(t), benchmark,
                entry=entries.get(t), ticker_events=by_ticker.get(t),
                rain_dates=rain_dates)
        for t in order
    ]

    # Correlation only over members with enough history — a thin series would
    # collapse the common window for the whole matrix (see _MIN_HISTORY).
    corr_input: dict[str, pd.Series] = {}
    excluded: list[str] = []
    for member in members:
        s = closes.get(member.ticker)
        if s is not None and len(s) >= _MIN_HISTORY:
            corr_input[member.ticker] = s
        elif s is not None:
            # Has data but too little of it — the lottery-ticket case. A member
            # with NO series yet (mid warm-up) is silently skipped, not named.
            excluded.append(member.ticker)

    correlation = correlation_matrix(corr_input) if corr_input else {"labels": [], "matrix": []}
    note = ""
    if excluded:
        names = ", ".join(excluded)
        note = (
            f"{names} left out of the grid: too little history to correlate, "
            "another face of the lottery-ticket lesson — a blank past can't be measured."
        )

    # The constellation: MDS coordinates place the names, the minimum spanning
    # tree draws the skeleton linking each to its nearest relative.
    constellation = {"nodes": mds_layout(correlation), "mst": mst_edges(correlation)}

    return BasketResponse(
        as_of=latest,
        roles_as_of=ROLES_AS_OF,
        laws=list(MARKET_LAWS),
        members=members,
        correlation=correlation,
        correlation_note=note,
        benchmark_ticker=settings.benchmark,
        events=list(events),
        rain_dates=[d.date() if hasattr(d, "date") else d for d in rain_dates],
        constellation=constellation,
    )


def build_basket() -> BasketResponse:
    """Cached per analytics metrics-cache generation (rebuilds as warm-up streams
    or the watchlist changes)."""
    from . import events as events_service
    from . import watchlist as watchlist_service

    metrics, latest = analytics.universe_metrics()
    closes = analytics.universe_closes()
    tickers = watchlist_service.tickers()
    entries = {e.ticker: e for e in watchlist_service.entries()}
    evts = events_service.build_events(tickers)
    key = analytics._cache["key"]
    with _lock:
        if _basket_cache["key"] == key and _basket_cache["value"] is not None:
            return _basket_cache["value"]
    value = _build(metrics, closes, latest, tickers=tickers, entries=entries, events=evts)
    with _lock:
        _basket_cache.update(key=key, value=value)
    return value
