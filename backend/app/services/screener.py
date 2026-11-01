# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Transparent per-sector stock screener.

Ranks the *affordable* (≤ budget), *liquid* members of each sector by a 0–100
score built from four percentile factors. Every input and weight is exposed to
the UI — this is a "here's a defensible starting point to learn from", **not** a
recommendation.

Pure and deterministic (ties break by ticker) so it unit-tests cleanly.
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict
from dataclasses import dataclass

from ..config import MIN_DOLLAR_VOLUME, SCORE_WEIGHTS, STALE_SESSIONS
from .metrics import StockMetrics
from .trading_calendar import sessions_behind


@dataclass(frozen=True)
class ScoredStock:
    ticker: str
    score: float
    factors: dict[str, float]  # momentum, stability, resilience, liquidity (0-100)
    metrics: StockMetrics


def _midrank_percentiles(values: list[float]) -> list[float]:
    """Percentile rank (0–100) of each value, ties averaged (midrank)."""
    n = len(values)
    if n == 0:
        return []
    if n == 1:
        return [50.0]
    order = sorted(range(n), key=lambda i: values[i])
    pct = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0  # 0-based average rank of the tie block
        p = (avg_rank + 0.5) / n * 100.0
        for k in range(i, j + 1):
            pct[order[k]] = p
        i = j + 1
    return pct


def _score_group(members: list[StockMetrics]) -> list[ScoredStock]:
    mom_pct = _midrank_percentiles([m.ret_3m for m in members])  # type: ignore[misc]
    vol_pct = _midrank_percentiles([m.vol_90d for m in members])  # type: ignore[misc]
    dd_pct = _midrank_percentiles([m.max_drawdown_1y for m in members])
    liq_pct = _midrank_percentiles([m.avg_dollar_volume_20d for m in members])

    scored: list[ScoredStock] = []
    for i, m in enumerate(members):
        # Momentum: 3m-return percentile + small trend-confirmation bonuses.
        momentum = min(
            100.0,
            mom_pct[i] + (5.0 if m.above_ma50 else 0.0) + (5.0 if m.above_ma200 else 0.0),
        )
        stability = 100.0 - vol_pct[i]  # lower volatility → more stable
        resilience = dd_pct[i]  # shallower (less negative) drawdown → higher
        liquidity = liq_pct[i]

        factors = {
            "momentum": round(momentum, 1),
            "stability": round(stability, 1),
            "resilience": round(resilience, 1),
            "liquidity": round(liquidity, 1),
        }
        score = (
            SCORE_WEIGHTS["momentum"] * momentum
            + SCORE_WEIGHTS["stability"] * stability
            + SCORE_WEIGHTS["resilience"] * resilience
            + SCORE_WEIGHTS["liquidity"] * liquidity
        )
        scored.append(
            ScoredStock(ticker=m.ticker, score=round(score, 1), factors=factors, metrics=m)
        )

    scored.sort(key=lambda s: (-s.score, s.ticker))
    return scored


def is_stale(
    last_bar: dt.date, universe_latest: dt.date, max_sessions: int = STALE_SESSIONS
) -> bool:
    """True when a ticker's newest bar trails the universe's newest bar by more
    than ``max_sessions`` trading sessions — a stopped feed whose last bar would
    otherwise be ranked as if it were today's."""
    return sessions_behind(last_bar, universe_latest) > max_sessions


def is_eligible(m: StockMetrics, budget: float | None) -> bool:
    """Affordable, liquid, and with enough history to score."""
    if budget is not None and m.price > budget:
        return False
    if m.avg_dollar_volume_20d < MIN_DOLLAR_VOLUME:
        return False
    return m.ret_3m is not None and m.vol_90d is not None


def screen_by_sector(
    metrics_by_ticker: dict[str, StockMetrics],
    sector_by_ticker: dict[str, str],
    budget: float | None,
) -> dict[str, list[ScoredStock]]:
    """Return {sector: [ScoredStock ranked best→worst]} over eligible members."""
    groups: dict[str, list[StockMetrics]] = defaultdict(list)
    for ticker, m in metrics_by_ticker.items():
        sector = sector_by_ticker.get(ticker)
        if sector is None:
            continue
        if not is_eligible(m, budget):
            continue
        groups[sector].append(m)

    return {sector: _score_group(members) for sector, members in groups.items()}
