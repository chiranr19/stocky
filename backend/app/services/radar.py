"""Entry Radar: pullback setups ranked and validated against each stock's history.

For every eligible stock, measure how far it trades below its recent 1M/2M/3M
high, whether the long trend is intact (above MA200), and how unusual today's
pullback is *for that stock*. Then find every past episode that looked like
today (same depth bucket, same trend state) and report the actual forward
outcomes — median next-month move, win rate, worst case, sample size.

Descriptive statistics, fully inspectable weights, never a buy signal.
"""

from __future__ import annotations

import threading

import pandas as pd

from ..config import (
    RADAR_DEPTH_BUCKETS,
    RADAR_EPISODE_GAP,
    RADAR_FORWARD_DAYS,
    RADAR_LOOKBACKS,
    RADAR_MIN_DEPTH_PCT,
    RADAR_MIN_EPISODES,
    RADAR_WEIGHTS,
    sector_of,
)
from ..models import EchoStats as EchoStatsModel
from ..models import RadarResponse, RadarRow, RiskFlag
from . import analytics
from . import flags as flags_service
from .metrics import (
    StockMetrics,
    depth_bucket,
    echo_stats,
    find_setup_episodes,
    moving_average,
    pullback_series,
)
from .screener import _midrank_percentiles, is_eligible

_lock = threading.Lock()
_radar_cache: dict = {"key": None, "by_params": {}}


def _rsi_factor(rsi14: float | None) -> float:
    """Lower RSI → more washed-out → higher factor. RSI 30 → 100, RSI 70 → 0."""
    if rsi14 is None:
        return 50.0
    return float(min(100.0, max(0.0, (70.0 - rsi14) / 40.0 * 100.0)))


def _analyze_one(
    m: StockMetrics, adj: pd.Series, lookback_days: int,
    benchmark: pd.Series | None = None,
) -> tuple[float, float, EchoStatsModel | None] | None:
    """(depth_pct, depth_rank, echo) for one stock, or None if not a setup."""
    if len(adj) < lookback_days + 5:
        return None
    depth = pullback_series(adj, lookback_days)
    today_depth = float(depth.iloc[-1]) if not pd.isna(depth.iloc[-1]) else None
    if today_depth is None or today_depth < RADAR_MIN_DEPTH_PCT:
        return None

    # How unusual is today's dip for THIS stock? Percentile within its own
    # historical depth distribution (same window).
    hist = depth.dropna()
    depth_rank = float((hist < today_depth).mean() * 100.0)

    bucket = depth_bucket(today_depth, RADAR_DEPTH_BUCKETS)
    echo = None
    if bucket is not None:
        ma200 = moving_average(adj, 200)
        above = adj > ma200
        trend = bool(m.above_ma200)

        # Tier 1: dips in the same depth bucket AND same trend state.
        episodes = find_setup_episodes(
            depth, above, bucket, trend_state=trend, min_gap=RADAR_EPISODE_GAP
        )
        stats = echo_stats(
            adj, episodes, RADAR_FORWARD_DAYS, RADAR_MIN_EPISODES,
            kind="exact", min_depth_pct=bucket[0], benchmark=benchmark,
        )
        if stats is None:
            # Tier 2: widen to "any dip at least this deep", stepping the floor
            # down one bucket edge at a time until the sample is usable. Each
            # step is a strict superset, and the UI labels the floor actually
            # used ("dips ≥15%"), so the comparison stays honest — a 25% dip is
            # rare, but the family of ≥15% dips still says something.
            floors = sorted(
                {lo for lo, _ in RADAR_DEPTH_BUCKETS if lo <= bucket[0]}, reverse=True
            )
            for floor in floors:
                if floor < RADAR_MIN_DEPTH_PCT:
                    break
                episodes = find_setup_episodes(
                    depth, above, (floor, 1000.0), trend_state=trend,
                    min_gap=RADAR_EPISODE_GAP,
                )
                stats = echo_stats(
                    adj, episodes, RADAR_FORWARD_DAYS, RADAR_MIN_EPISODES,
                    kind="at_least", min_depth_pct=floor, benchmark=benchmark,
                )
                if stats is not None:
                    break

        if stats is not None:
            echo = EchoStatsModel(
                n=stats.n,
                median_fwd_pct=stats.median_fwd_pct,
                win_rate=stats.win_rate,
                worst_pct=stats.worst_pct,
                best_pct=stats.best_pct,
                kind=stats.kind,
                min_depth_pct=stats.min_depth_pct,
                bucket_lo=bucket[0],
                bucket_hi=bucket[1],
                n_years=stats.n_years,
                confidence=stats.confidence,
                p25_pct=stats.p25_pct,
                p75_pct=stats.p75_pct,
                n_benchmarked=stats.n_benchmarked,
                beat_benchmark=stats.beat_benchmark,
                median_excess_pct=stats.median_excess_pct,
            )
    return today_depth, depth_rank, echo


def _build(budget: float | None, lookback: str, limit: int) -> RadarResponse:
    metrics, latest = analytics.universe_metrics()
    closes = analytics.universe_closes()
    lookback_days = RADAR_LOOKBACKS[lookback]
    benchmark = closes.get("VOO")  # opportunity-cost yardstick for every echo

    candidates: list[tuple[StockMetrics, float, float, EchoStatsModel | None]] = []
    for ticker, m in metrics.items():
        if sector_of(ticker) is None or not is_eligible(m, budget):
            continue
        adj = closes.get(ticker)
        if adj is None:
            continue
        analyzed = _analyze_one(m, adj, lookback_days, benchmark)
        if analyzed is None:
            continue
        depth_pct, depth_rank, echo = analyzed
        candidates.append((m, depth_pct, depth_rank, echo))

    # Quality factor: 1-year return percentile among the candidates themselves —
    # "a dip in a stock that had been strong" ranks above a dip in a laggard.
    ret_1y_values = [(m.ret_1y if m.ret_1y is not None else 0.0) for m, *_ in candidates]
    quality_pcts = _midrank_percentiles(ret_1y_values)

    rows: list[RadarRow] = []
    for i, (m, depth_pct, depth_rank, echo) in enumerate(candidates):
        factors = {
            "depth": round(depth_rank, 1),
            "trend": 100.0 if m.above_ma200 else 0.0,
            "rsi": round(_rsi_factor(m.rsi14), 1),
            "quality": round(quality_pcts[i], 1),
        }
        score = sum(RADAR_WEIGHTS[k] * v for k, v in factors.items())
        # Surface the risks even on a high-scoring setup — a good score must
        # never hide a hazard the flags engine can name.
        risks = [f for f in flags_service.evaluate(m, depth_pct) if f.kind == "risk"]
        rows.append(
            RadarRow(
                row=analytics.to_row(m),
                depth_pct=round(depth_pct, 1),
                depth_rank=round(depth_rank, 1),
                falling_knife=not m.above_ma200,
                entry_score=round(score, 1),
                entry_factors=factors,
                echo=echo,
                flags=[
                    RiskFlag(**vars(f), analogy=flags_service.flag_analogy(f.code))
                    for f in risks
                ],
            )
        )

    rows.sort(key=lambda r: (-r.entry_score, r.row.ticker))
    return RadarResponse(
        as_of=latest,
        budget=budget,
        lookback=lookback,
        horizon_days=RADAR_FORWARD_DAYS,
        weights=RADAR_WEIGHTS,
        rows=rows[:limit],
    )


def build_radar(budget: float | None, lookback: str, limit: int) -> RadarResponse:
    """Cached per (metrics-cache generation, budget, lookback, limit)."""
    cache_key = analytics._cache["key"]
    params = (budget, lookback, limit)
    with _lock:
        if _radar_cache["key"] != cache_key:
            _radar_cache["key"] = cache_key
            _radar_cache["by_params"] = {}
        cached = _radar_cache["by_params"].get(params)
        if cached is not None:
            return cached
    result = _build(budget, lookback, limit)
    with _lock:
        _radar_cache["by_params"][params] = result
    return result


def radar_for_ticker(ticker: str) -> RadarRow | None:
    """The 3M entry-position row for one ticker (deep-dive card), budget-free."""
    ticker = ticker.upper()
    metrics, _ = analytics.universe_metrics()
    m = metrics.get(ticker)
    closes = analytics.universe_closes()
    adj = closes.get(ticker)
    if m is None or adj is None:
        return None
    analyzed = _analyze_one(m, adj, RADAR_LOOKBACKS["3m"], closes.get("VOO"))
    if analyzed is None:
        return None
    depth_pct, depth_rank, echo = analyzed
    factors = {
        "depth": round(depth_rank, 1),
        "trend": 100.0 if m.above_ma200 else 0.0,
        "rsi": round(_rsi_factor(m.rsi14), 1),
        "quality": 50.0,  # cross-sectional percentile is meaningless for one name
    }
    score = sum(RADAR_WEIGHTS[k] * v for k, v in factors.items())
    return RadarRow(
        row=analytics.to_row(m),
        depth_pct=round(depth_pct, 1),
        depth_rank=round(depth_rank, 1),
        falling_knife=not m.above_ma200,
        entry_score=round(score, 1),
        entry_factors=factors,
        echo=echo,
    )
