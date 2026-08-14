"""Unit tests for technical-analysis math (no network / DB)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.services.metrics import (
    annualized_volatility,
    compute_metrics,
    correlation_matrix,
    detect_cross,
    normalized_growth,
    return_histogram,
    rsi,
    total_return_pct,
)


def _series(values, start="2024-01-02"):
    idx = pd.bdate_range(start=start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


# --------------------------------------------------------------------------- #
# RSI
# --------------------------------------------------------------------------- #
def test_rsi_all_gains_is_100():
    s = _series(list(range(1, 40)))  # strictly increasing
    assert rsi(s, 14).iloc[-1] == pytest.approx(100.0)


def test_rsi_all_losses_is_0():
    s = _series(list(range(40, 1, -1)))  # strictly decreasing
    assert rsi(s, 14).iloc[-1] == pytest.approx(0.0)


def test_rsi_bounded_and_midrange_for_choppy():
    rng = np.random.default_rng(0)
    s = _series(100 + np.cumsum(rng.normal(0, 1, 60)))
    val = rsi(s, 14).iloc[-1]
    assert 0.0 <= val <= 100.0


# --------------------------------------------------------------------------- #
# Cross detection
# --------------------------------------------------------------------------- #
def test_detect_golden_cross_recent():
    short = _series([98, 99, 101, 102, 103])
    long = _series([100, 100, 100, 100, 100])
    kind, date = detect_cross(short, long, lookback=10)
    assert kind == "golden"
    assert date == short.index[2].date()


def test_detect_death_cross_recent():
    short = _series([102, 101, 99, 98, 97])
    long = _series([100, 100, 100, 100, 100])
    kind, _ = detect_cross(short, long, lookback=10)
    assert kind == "death"


def test_detect_cross_too_old_is_none():
    short = _series([98, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112])
    long = _series([100] * 12)
    # crossover at index 1, which is 10 sessions ago → outside lookback=5
    kind, _ = detect_cross(short, long, lookback=5)
    assert kind is None


# --------------------------------------------------------------------------- #
# Returns / volatility
# --------------------------------------------------------------------------- #
def test_total_return_pct():
    s = _series([100, 110, 120, 130, 140])
    assert total_return_pct(s, trading_days=4) == pytest.approx(40.0)


def test_total_return_none_when_insufficient():
    s = _series([100, 110])
    assert total_return_pct(s, trading_days=5) is None


def test_annualized_volatility_positive():
    rng = np.random.default_rng(1)
    s = _series(100 + np.cumsum(rng.normal(0, 1, 120)))
    vol = annualized_volatility(s, 90)
    assert vol is not None and vol > 0


# --------------------------------------------------------------------------- #
# Correlation / histogram / normalization
# --------------------------------------------------------------------------- #
def test_correlation_identical_is_one():
    s = _series(100 + np.cumsum(np.ones(60)))
    out = correlation_matrix({"A": s, "B": s.copy()}, window=50)
    a = out["labels"].index("A")
    b = out["labels"].index("B")
    assert out["matrix"][a][b] == pytest.approx(1.0)


def test_correlation_anti_is_negative_one():
    base = np.cumsum(np.random.default_rng(2).normal(0, 1, 80))
    up = _series(100 + base)
    down = _series(100 - base)
    out = correlation_matrix({"U": up, "D": down}, window=70)
    assert out["matrix"][0][1] == pytest.approx(-1.0, abs=1e-6)


def test_return_histogram_counts_sum():
    s = _series(100 + np.cumsum(np.random.default_rng(3).normal(0, 1, 100)))
    hist = return_histogram(s, bins=10)
    assert sum(hist["counts"]) == len(s.pct_change().dropna())
    assert len(hist["edges"]) == 11


def test_normalized_growth_starts_at_base():
    s = _series([50, 75, 100])
    g = normalized_growth(s, base=100)
    assert g.iloc[0] == pytest.approx(100.0)
    assert g.iloc[-1] == pytest.approx(200.0)


# --------------------------------------------------------------------------- #
# compute_metrics end-to-end (synthetic uptrend)
# --------------------------------------------------------------------------- #
def _ohlcv(closes):
    idx = pd.bdate_range(start="2024-01-02", periods=len(closes))
    close = pd.Series(closes, index=idx, dtype=float)
    return pd.DataFrame(
        {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close * 1.01,
            "low": close * 0.99,
            "close": close,
            "adj_close": close,
            "volume": pd.Series([1_000_000] * len(closes), index=idx),
        }
    )


def test_compute_metrics_uptrend():
    closes = list(np.linspace(100, 260, 300))  # steady rise, >200 pts for MA200
    m = compute_metrics("TEST", _ohlcv(closes))
    assert m is not None
    assert m.above_ma50 and m.above_ma200
    assert m.ret_1y is not None and m.ret_1y > 0
    assert m.range_52w_position > 0.9  # near the highs
    assert m.is_new_high_52w
    assert 0 <= (m.rsi14 or 0) <= 100


def test_compute_metrics_too_short_returns_none():
    assert compute_metrics("X", _ohlcv([100])) is None
