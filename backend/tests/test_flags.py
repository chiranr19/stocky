"""Tests for the risk/strength flag engine — the good-picks/bad-picks showcase."""

from __future__ import annotations

import re

import pytest

from app.services.flags import SEVERITY_WEIGHT, evaluate, risk_score
from app.services.metrics import StockMetrics

# Same house rule as the reading layer: describe hazards, never instruct.
FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|dump it|avoid buying)\b",
    re.IGNORECASE,
)


def _m(**over) -> StockMetrics:
    base = dict(
        ticker="TEST", price=100.0, prev_close=99.0, change_pct=1.0, open=99.5,
        gap_pct=0.5, ma50=95.0, ma200=90.0, above_ma50=True, above_ma200=True,
        rsi14=50.0, rsi_signal=None, vol_90d=22.0, ret_1m=1.0, ret_3m=6.0,
        ret_1y=18.0, high_52w=120.0, low_52w=80.0, range_52w_position=0.6,
        avg_dollar_volume_20d=2e8, volume=1_000_000, avg_volume_30d=1_000_000,
        volume_ratio=1.0, max_drawdown_1y=-12.0, is_new_high_52w=False,
        is_new_low_52w=False, cross=None, cross_date=None, spark=[],
    )
    base.update(over)
    return StockMetrics(**base)


def codes(m: StockMetrics, depth_pct=None) -> set[str]:
    return {f.code for f in evaluate(m, depth_pct)}


# --------------------------------------------------------------------------- #
# Risk patterns
# --------------------------------------------------------------------------- #
def test_falling_knife_needs_broken_trend_and_a_real_decline():
    knife = _m(above_ma200=False, above_ma50=False, ret_3m=-25.0)
    assert "falling_knife" in codes(knife, depth_pct=22.0)
    # Same decline but trend intact → a pullback, not a knife.
    assert "falling_knife" not in codes(_m(ret_3m=-25.0), depth_pct=22.0)


def test_broken_trend_flagged_when_not_a_knife():
    c = codes(_m(above_ma200=False, ret_3m=-2.0), depth_pct=3.0)
    assert "broken_trend" in c and "falling_knife" not in c


def test_value_trap_requires_lows_broken_trend_and_losing_year():
    trap = _m(range_52w_position=0.05, above_ma200=False, ret_1y=-35.0)
    assert "value_trap" in codes(trap, depth_pct=30.0)
    # Near the lows but trend intact and a positive year → not a trap.
    assert "value_trap" not in codes(_m(range_52w_position=0.05, ret_1y=10.0))


def test_volatility_trap_is_the_bad_quadrant():
    assert "volatility_trap" in codes(_m(vol_90d=55.0, ret_1y=-12.0))
    # High vol but rewarded → not the trap, though still flagged as volatile.
    c = codes(_m(vol_90d=65.0, ret_1y=40.0))
    assert "volatility_trap" not in c and "very_high_volatility" in c


def test_overextended_needs_both_hot_rsi_and_top_of_range():
    assert "overextended" in codes(_m(rsi14=80.0, range_52w_position=0.98))
    assert "overextended" not in codes(_m(rsi14=80.0, range_52w_position=0.5))


def test_thin_liquidity_and_severe_drawdown():
    assert "thin_liquidity" in codes(_m(avg_dollar_volume_20d=1e6))
    assert "severe_drawdown" in codes(_m(max_drawdown_1y=-52.0))


def test_death_cross_flagged():
    assert "death_cross" in codes(_m(cross="death"))


# --------------------------------------------------------------------------- #
# Strength patterns
# --------------------------------------------------------------------------- #
def test_healthy_stock_shows_strengths_and_no_risks():
    found = evaluate(_m(), depth_pct=10.0)
    kinds = {f.kind for f in found}
    assert "strength" in kinds and "risk" not in kinds
    c = {f.code for f in found}
    assert "trend_intact" in c and "constructive_pullback" in c


def test_calm_compounder_and_liquidity_strengths():
    c = codes(_m(vol_90d=18.0, ret_1y=22.0, avg_dollar_volume_20d=1e9))
    assert "calm_compounder" in c and "deep_liquidity" in c and "shallow_drawdown" in c


def test_constructive_pullback_requires_intact_trend():
    assert "constructive_pullback" not in codes(_m(above_ma200=False), depth_pct=12.0)


# --------------------------------------------------------------------------- #
# Scoring + invariants
# --------------------------------------------------------------------------- #
def test_risk_score_counts_only_risks_and_scales_with_severity():
    healthy = evaluate(_m(), depth_pct=10.0)
    assert risk_score(healthy) == 0.0

    bad = evaluate(
        _m(above_ma200=False, above_ma50=False, ret_3m=-30.0, ret_1y=-40.0,
           range_52w_position=0.03, vol_90d=70.0, max_drawdown_1y=-55.0),
        depth_pct=40.0,
    )
    assert risk_score(bad) >= SEVERITY_WEIGHT["high"] * 3


def test_risks_are_ordered_before_strengths():
    found = evaluate(_m(above_ma200=False, cross="death"), depth_pct=5.0)
    kinds = [f.kind for f in found]
    if "strength" in kinds and "risk" in kinds:
        assert kinds.index("risk") < kinds.index("strength")


def test_every_flag_explains_itself():
    samples = [
        evaluate(_m(), depth_pct=10.0),
        evaluate(_m(above_ma200=False, ret_3m=-30.0), depth_pct=25.0),
        evaluate(_m(vol_90d=70.0, ret_1y=-20.0)),
        evaluate(_m(rsi14=80.0, range_52w_position=0.99)),
        evaluate(_m(avg_dollar_volume_20d=1e6, cross="death", max_drawdown_1y=-50.0)),
        evaluate(_m(range_52w_position=0.04, above_ma200=False, ret_1y=-30.0), depth_pct=35.0),
    ]
    for group in samples:
        for f in group:
            assert f.why.strip() and f.what_vets_do.strip()
            assert f.kind in ("risk", "strength")
            assert f.severity in SEVERITY_WEIGHT
            blob = f"{f.label} {f.why} {f.what_vets_do}"
            match = FORBIDDEN.search(blob)
            assert match is None, f"advice phrasing in {f.code}: {match.group(0)!r}"


@pytest.mark.parametrize("depth", [None, 0.0, 5.0, 50.0])
def test_missing_or_extreme_depth_never_crashes(depth):
    assert isinstance(evaluate(_m(), depth), list)
    assert isinstance(evaluate(_m(rsi14=None, vol_90d=None, ret_1y=None), depth), list)
