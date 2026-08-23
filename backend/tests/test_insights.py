# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Tests for the reading layer — every branch fires, and nothing gives advice."""

from __future__ import annotations

import re

import pytest

from app.services.insights import (
    TONES,
    breadth_reading,
    stock_readings,
    vix_reading,
    yield_reading,
)
from app.services.metrics import StockMetrics

# Words that would turn an interpretation into financial advice.
FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing)\b",
    re.IGNORECASE,
)


def _m(**over) -> StockMetrics:
    base = dict(
        ticker="TEST", price=100.0, prev_close=99.0, change_pct=1.0, open=99.5,
        gap_pct=0.5, ma50=95.0, ma200=90.0, above_ma50=True, above_ma200=True,
        rsi14=50.0, rsi_signal=None, vol_90d=28.0, ret_1m=2.0, ret_3m=8.0,
        ret_1y=20.0, high_52w=120.0, low_52w=70.0, range_52w_position=0.6,
        avg_dollar_volume_20d=1e8, volume=1_000_000, avg_volume_30d=1_000_000,
        volume_ratio=1.0, max_drawdown_1y=-15.0, is_new_high_52w=False,
        is_new_low_52w=False, cross=None, cross_date=None, spark=[],
    )
    base.update(over)
    return StockMetrics(**base)


def _all_readings():
    """A sample spanning every branch, for the invariant checks."""
    out = []
    out += stock_readings(_m())                                            # rising
    out += stock_readings(_m(), depth_pct=12.0)                            # rising + dip
    out += stock_readings(_m(above_ma50=False))                            # wobble
    out += stock_readings(_m(above_ma200=False))                           # bounce in downtrend
    out += stock_readings(_m(above_ma50=False, above_ma200=False, ret_3m=-20.0))  # falling
    out += stock_readings(_m(rsi14=78.0))
    out += stock_readings(_m(rsi14=22.0))
    out += stock_readings(_m(range_52w_position=0.99))
    out += stock_readings(_m(range_52w_position=0.02))
    out += stock_readings(_m(vol_90d=60.0))
    out += stock_readings(_m(vol_90d=15.0))
    out += stock_readings(_m(volume_ratio=3.2))
    out += stock_readings(_m(cross="golden"))
    out += stock_readings(_m(cross="death"))
    out += [vix_reading(12.0), vix_reading(18.0), vix_reading(32.0)]
    out += [breadth_reading(70, 350, 150), breadth_reading(50, 250, 250), breadth_reading(30, 150, 350)]
    out += [yield_reading(4.2, 1.1), yield_reading(4.2, -1.1)]
    return out


# --------------------------------------------------------------------------- #
# Invariants — the house rules
# --------------------------------------------------------------------------- #
def test_every_reading_has_a_caveat():
    for r in _all_readings():
        assert r.caveat.strip(), f"{r.aspect}/{r.headline} has no caveat"


def test_every_reading_has_headline_and_detail():
    for r in _all_readings():
        assert len(r.headline) > 5
        assert len(r.detail) > 30


def test_tone_taxonomy_is_closed():
    for r in _all_readings():
        assert r.tone in TONES, f"unexpected tone {r.tone!r}"


def test_no_advice_language_anywhere():
    for r in _all_readings():
        blob = f"{r.headline} {r.detail} {r.caveat} {r.analogy}"
        match = FORBIDDEN.search(blob)
        assert match is None, f"advice-like phrasing in {r.aspect}: {match.group(0)!r}"


def test_every_reading_has_an_analogy():
    """Metaphor-first teaching: every branch ships an everyday-life picture."""
    for r in _all_readings():
        assert len(r.analogy.strip()) > 20, f"{r.aspect}/{r.headline} has no analogy"
        assert r.analogy != r.detail, f"{r.aspect} analogy just repeats the detail"


def test_no_reading_copy_says_median():
    """Protects the digest's ``txt.count('median') <= 2`` budget at the source."""
    for r in _all_readings():
        blob = f"{r.headline} {r.detail} {r.caveat} {r.analogy}".lower()
        assert "median" not in blob, f"the word 'median' leaked into {r.aspect}"


# --------------------------------------------------------------------------- #
# Branch behavior — the user's actual question
# --------------------------------------------------------------------------- #
def test_rising_chart_reads_constructive_but_flags_the_risk():
    trend = stock_readings(_m())[0]
    assert trend.aspect == "trend"
    assert trend.tone == "constructive"
    assert "uptrend" in trend.detail.lower()
    assert "downside" in trend.caveat.lower() or "full price" in trend.caveat.lower()


def test_rising_with_pullback_mentions_the_dip():
    trend = stock_readings(_m(), depth_pct=12.0)[0]
    assert trend.tone == "constructive"
    assert "12%" in trend.headline


def test_falling_chart_reads_caution_and_names_the_knife():
    trend = stock_readings(_m(above_ma50=False, above_ma200=False, ret_3m=-25.0))[0]
    assert trend.tone == "caution"
    assert "falling knife" in trend.detail.lower()


def test_broken_trend_bounce_is_neutral_not_constructive():
    trend = stock_readings(_m(above_ma200=False, above_ma50=True))[0]
    assert trend.tone == "neutral"


def test_rsi_extremes_produce_matching_readings():
    hot = [r for r in stock_readings(_m(rsi14=80.0)) if r.aspect == "rsi"][0]
    cold = [r for r in stock_readings(_m(rsi14=20.0)) if r.aspect == "rsi"][0]
    assert hot.tone == "caution" and "stretched" in hot.headline
    assert "washed out" in cold.headline


def test_volatility_translates_to_a_weekly_swing():
    r = [x for x in stock_readings(_m(vol_90d=52.0)) if x.aspect == "volatility"][0]
    assert "±" in r.detail
    assert r.tone == "caution"


def test_quiet_volume_produces_no_volume_reading():
    aspects = [r.aspect for r in stock_readings(_m(volume_ratio=1.0))]
    assert "volume" not in aspects


def test_unusual_volume_produces_a_reading():
    aspects = [r.aspect for r in stock_readings(_m(volume_ratio=2.5))]
    assert "volume" in aspects


def test_drawdown_reading_always_present_and_scales_tone():
    calm = [r for r in stock_readings(_m(max_drawdown_1y=-8.0)) if r.aspect == "drawdown"][0]
    rough = [r for r in stock_readings(_m(max_drawdown_1y=-45.0)) if r.aspect == "drawdown"][0]
    assert calm.tone == "neutral"
    assert rough.tone == "caution"
    assert "45%" in rough.headline


def test_missing_metrics_are_skipped_gracefully():
    aspects = [r.aspect for r in stock_readings(_m(rsi14=None, vol_90d=None))]
    assert "rsi" not in aspects and "volatility" not in aspects
    assert "trend" in aspects  # the essential reading still renders


def test_market_readings_cover_the_vix_zones():
    assert vix_reading(11.0).tone == "constructive"
    assert vix_reading(20.0).tone == "neutral"
    assert vix_reading(35.0).tone == "caution"


def test_breadth_zones():
    assert breadth_reading(65, 300, 200).tone == "constructive"
    assert breadth_reading(50, 250, 250).tone == "neutral"
    assert breadth_reading(35, 150, 350).tone == "caution"
    assert "narrow" in breadth_reading(35, 150, 350).headline.lower()


@pytest.mark.parametrize("chg,word", [(1.5, "rising"), (-1.5, "falling"), (0.0, "flat")])
def test_yield_direction_wording(chg, word):
    assert word in yield_reading(4.3, chg).headline
