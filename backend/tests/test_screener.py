# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Unit tests for the per-sector screener (no network / DB)."""

from __future__ import annotations

import dataclasses

import pytest

from app.services.metrics import StockMetrics
from app.services.screener import (
    _midrank_percentiles,
    is_eligible,
    screen_by_sector,
)


def _metrics(ticker, price, ret_3m, vol_90d, dd, adv, above_ma=True):
    """Build a StockMetrics with only the fields the screener reads."""
    return StockMetrics(
        ticker=ticker,
        price=price,
        prev_close=price,
        change_pct=0.0,
        open=price,
        gap_pct=0.0,
        ma50=price - 1,
        ma200=price - 2,
        above_ma50=above_ma,
        above_ma200=above_ma,
        rsi14=50.0,
        rsi_signal=None,
        vol_90d=vol_90d,
        ret_1m=None,
        ret_3m=ret_3m,
        ret_1y=None,
        high_52w=price,
        low_52w=price * 0.5,
        range_52w_position=0.8,
        avg_dollar_volume_20d=adv,
        volume=100,
        avg_volume_30d=100,
        volume_ratio=1.0,
        max_drawdown_1y=dd,
        is_new_high_52w=False,
        is_new_low_52w=False,
        cross=None,
        cross_date=None,
    )


# --------------------------------------------------------------------------- #
# Percentiles
# --------------------------------------------------------------------------- #
def test_midrank_percentiles_order():
    pcts = _midrank_percentiles([10.0, 20.0, 30.0, 40.0])
    assert pcts[0] < pcts[1] < pcts[2] < pcts[3]
    assert pcts[-1] > pcts[0]


def test_midrank_single_is_50():
    assert _midrank_percentiles([5.0]) == [50.0]


def test_midrank_ties_equal():
    pcts = _midrank_percentiles([10.0, 10.0, 20.0])
    assert pcts[0] == pcts[1]  # tied values get the same percentile


# --------------------------------------------------------------------------- #
# Eligibility
# --------------------------------------------------------------------------- #
def test_budget_filter_excludes_expensive():
    m = _metrics("EXP", price=500, ret_3m=10, vol_90d=20, dd=-10, adv=1e8)
    assert not is_eligible(m, budget=200)
    assert is_eligible(m, budget=None)


def test_liquidity_gate_excludes_illiquid():
    m = _metrics("THIN", price=50, ret_3m=10, vol_90d=20, dd=-10, adv=1_000)
    assert not is_eligible(m, budget=200)


def test_missing_history_excluded():
    m = _metrics("NEW", price=50, ret_3m=None, vol_90d=None, dd=-10, adv=1e8)
    assert not is_eligible(m, budget=200)


# --------------------------------------------------------------------------- #
# Ranking
# --------------------------------------------------------------------------- #
def _sector_map(tickers, sector="Technology"):
    return {t: sector for t in tickers}


def test_higher_momentum_lower_vol_ranks_first():
    strong = _metrics("STRONG", price=100, ret_3m=30, vol_90d=15, dd=-8, adv=1e8)
    weak = _metrics("WEAK", price=100, ret_3m=-5, vol_90d=45, dd=-40, adv=1e8)
    by_ticker = {"STRONG": strong, "WEAK": weak}
    result = screen_by_sector(by_ticker, _sector_map(["STRONG", "WEAK"]), budget=200)
    ranked = result["Technology"]
    assert [s.ticker for s in ranked] == ["STRONG", "WEAK"]
    assert ranked[0].score > ranked[1].score


def test_score_is_weighted_0_100():
    m = _metrics("A", price=100, ret_3m=10, vol_90d=20, dd=-10, adv=1e8)
    result = screen_by_sector({"A": m}, _sector_map(["A"]), budget=200)
    s = result["Technology"][0]
    assert 0.0 <= s.score <= 100.0
    assert set(s.factors) == {"momentum", "stability", "resilience", "liquidity"}


def test_ranking_deterministic_tiebreak_by_ticker():
    # Identical metrics → identical score → alphabetical tie-break.
    a = _metrics("AAA", price=100, ret_3m=10, vol_90d=20, dd=-10, adv=1e8)
    b = _metrics("BBB", price=100, ret_3m=10, vol_90d=20, dd=-10, adv=1e8)
    result = screen_by_sector({"BBB": b, "AAA": a}, _sector_map(["AAA", "BBB"]), budget=200)
    assert [s.ticker for s in result["Technology"]] == ["AAA", "BBB"]
