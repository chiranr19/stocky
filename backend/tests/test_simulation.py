"""Unit tests for the Time Machine simulation math (no network / DB)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.services.simulation import (
    max_drawdown,
    simulate_investment,
)


def _series(values: list[float], start: str = "2023-01-02") -> pd.Series:
    idx = pd.bdate_range(start=start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


# --------------------------------------------------------------------------- #
# max_drawdown
# --------------------------------------------------------------------------- #
def test_max_drawdown_basic_dip():
    # peak 1200 at idx 1, trough 600 at idx 2 -> -50%
    dd = max_drawdown([1000, 1200, 600, 900])
    assert dd.peak_idx == 1
    assert dd.trough_idx == 2
    assert dd.peak_value == 1200
    assert dd.trough_value == 600
    assert dd.drawdown_pct == pytest.approx(-50.0)


def test_max_drawdown_monotonic_increase_is_zero():
    dd = max_drawdown([100, 110, 121, 133])
    assert dd.drawdown_pct == pytest.approx(0.0)


def test_max_drawdown_picks_deepest_of_multiple():
    # dip to -20% then recover, then dip to -40%
    values = [100, 80, 120, 72]  # running max: 100,100,120,120
    dd = max_drawdown(values)
    assert dd.trough_idx == 3
    assert dd.drawdown_pct == pytest.approx(-40.0)


def test_max_drawdown_empty_raises():
    with pytest.raises(ValueError):
        max_drawdown(np.array([]))


# --------------------------------------------------------------------------- #
# simulate_investment
# --------------------------------------------------------------------------- #
def test_simulate_shares_and_end_value():
    prices = _series([100, 120, 60, 90])
    inv = simulate_investment(prices, amount=1000)

    assert inv.shares == pytest.approx(10.0)  # 1000 / 100
    assert inv.start_value == 1000
    assert inv.end_value == pytest.approx(900.0)  # 10 shares * 90
    assert inv.total_return_pct == pytest.approx(-10.0)


def test_simulate_path_tracks_value_over_time():
    prices = _series([50, 75, 100])
    inv = simulate_investment(prices, amount=500)
    # 10 shares -> [500, 750, 1000]
    assert list(inv.path.round(2)) == [500.0, 750.0, 1000.0]


def test_simulate_drawdown_uses_value_path():
    prices = _series([100, 120, 60, 90])
    inv = simulate_investment(prices, amount=1000)
    assert inv.max_drawdown.drawdown_pct == pytest.approx(-50.0)
    assert inv.max_drawdown.peak_value == pytest.approx(1200.0)
    assert inv.max_drawdown.trough_value == pytest.approx(600.0)


def test_simulate_annualized_positive_over_one_year():
    # exactly one calendar year, doubling -> ~100% annualized
    idx = pd.to_datetime(["2022-01-03", "2023-01-03"])
    prices = pd.Series([100.0, 200.0], index=idx)
    inv = simulate_investment(prices, amount=1000)
    assert inv.total_return_pct == pytest.approx(100.0)
    assert inv.annualized_return_pct == pytest.approx(100.0, abs=0.5)


def test_simulate_rejects_short_series():
    with pytest.raises(ValueError):
        simulate_investment(_series([100]), amount=1000)


def test_simulate_rejects_nonpositive_amount():
    with pytest.raises(ValueError):
        simulate_investment(_series([100, 110]), amount=0)


def test_simulate_ignores_leading_nans():
    prices = _series([np.nan, 100, 200])
    inv = simulate_investment(prices, amount=1000)
    # first valid price is 100 -> 10 shares -> ends at 2000
    assert inv.shares == pytest.approx(10.0)
    assert inv.end_value == pytest.approx(2000.0)
