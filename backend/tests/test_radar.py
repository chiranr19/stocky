"""Unit tests for the Entry Radar math (pullbacks, episodes, echoes, scoring)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.config import RADAR_DEPTH_BUCKETS, RADAR_WEIGHTS
from app.services.metrics import (
    StockMetrics,
    depth_bucket,
    echo_stats,
    find_setup_episodes,
    forward_returns,
    pullback_series,
    rolling_high,
)
from app.services.radar import _analyze_one, _rsi_factor


def _series(values, start="2023-01-02") -> pd.Series:
    idx = pd.bdate_range(start=start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def _metrics(ticker="TEST", price=100.0, above_ma200=True, rsi14=50.0) -> StockMetrics:
    return StockMetrics(
        ticker=ticker, price=price, prev_close=price, change_pct=0.0, open=price,
        gap_pct=0.0, ma50=price, ma200=price * 0.9, above_ma50=True,
        above_ma200=above_ma200, rsi14=rsi14, rsi_signal=None, vol_90d=25.0,
        ret_1m=1.0, ret_3m=5.0, ret_1y=20.0, high_52w=price * 1.2, low_52w=price * 0.7,
        range_52w_position=0.6, avg_dollar_volume_20d=1e8, volume=1_000_000,
        avg_volume_30d=1_000_000, volume_ratio=1.0, max_drawdown_1y=-15.0,
        is_new_high_52w=False, is_new_low_52w=False, cross=None, cross_date=None,
        spark=[],
    )


# --------------------------------------------------------------------------- #
# Building blocks
# --------------------------------------------------------------------------- #
def test_rolling_high_and_pullback():
    s = _series([100, 90, 80, 100])
    high = rolling_high(s, 2)
    assert np.isnan(high.iloc[0])
    assert list(high.iloc[1:]) == [100, 90, 100]

    depth = pullback_series(s, 2)
    assert depth.iloc[1] == pytest.approx(10.0)          # 90 vs high 100
    assert depth.iloc[2] == pytest.approx(100 * 10 / 90) # 80 vs high 90
    assert depth.iloc[3] == pytest.approx(0.0)           # new high → no pullback


def test_forward_returns_shift():
    s = _series([100, 110, 121])
    fwd = forward_returns(s, 1)
    assert fwd.iloc[0] == pytest.approx(10.0)
    assert fwd.iloc[1] == pytest.approx(10.0)
    assert np.isnan(fwd.iloc[2])  # nothing ahead of the last day


def test_depth_bucket_edges():
    assert depth_bucket(3.0, RADAR_DEPTH_BUCKETS) is None      # below min
    assert depth_bucket(5.0, RADAR_DEPTH_BUCKETS) == (5.0, 10.0)
    assert depth_bucket(9.99, RADAR_DEPTH_BUCKETS) == (5.0, 10.0)
    assert depth_bucket(12.0, RADAR_DEPTH_BUCKETS) == (10.0, 15.0)
    assert depth_bucket(45.0, RADAR_DEPTH_BUCKETS) == (30.0, 100.0)


def test_find_setup_episodes_two_dips():
    # depth: two separate runs in bucket [10,15), separated by >gap sessions.
    depth_vals = [0] * 10 + [12, 13, 12] + [0] * 20 + [11, 12] + [0] * 10
    depth = _series(depth_vals)
    above = pd.Series(True, index=depth.index)
    eps = find_setup_episodes(depth, above, (10.0, 15.0), True, min_gap=10)
    assert len(eps) == 2
    assert eps[0] == depth.index[10]
    assert eps[1] == depth.index[33]


def test_find_setup_episodes_gap_collapses_choppy_reentries():
    # Two runs only 3 sessions apart → gap rule counts them once.
    depth_vals = [0] * 10 + [12, 12] + [0] * 3 + [13, 13] + [0] * 10
    depth = _series(depth_vals)
    above = pd.Series(True, index=depth.index)
    eps = find_setup_episodes(depth, above, (10.0, 15.0), True, min_gap=10)
    assert len(eps) == 1


def test_find_setup_episodes_respects_trend_state():
    depth_vals = [0] * 5 + [12, 12] + [0] * 5
    depth = _series(depth_vals)
    above = pd.Series(False, index=depth.index)  # everything below MA200
    assert find_setup_episodes(depth, above, (10.0, 15.0), True, min_gap=5) == []
    assert len(find_setup_episodes(depth, above, (10.0, 15.0), False, min_gap=5)) == 1


def test_echo_stats_known_values():
    # Price path where forward-5 returns from the chosen episodes are known.
    vals = list(np.linspace(100, 200, 60))
    s = _series(vals)
    episodes = [s.index[0], s.index[10], s.index[20], s.index[30], s.index[40], s.index[45]]
    stats = echo_stats(s, episodes, horizon=5, min_episodes=6)
    assert stats is not None
    assert stats.n == 6
    assert stats.win_rate == 1.0  # monotonic rise → every forward return positive
    assert stats.worst_pct > 0
    assert stats.median_fwd_pct > 0


def test_echo_stats_insufficient_sample_returns_none():
    s = _series(list(np.linspace(100, 200, 60)))
    stats = echo_stats(s, [s.index[0], s.index[10]], horizon=5, min_episodes=6)
    assert stats is None


def test_echo_stats_excludes_unresolved_recent_episodes():
    s = _series(list(np.linspace(100, 200, 100)))
    episodes = [s.index[i] for i in (0, 10, 20, 30, 40, 96)]  # last one < horizon from end
    stats = echo_stats(s, episodes, horizon=21, min_episodes=5)
    assert stats is not None
    assert stats.n == 5  # the unresolved one dropped


# --------------------------------------------------------------------------- #
# Scoring pieces
# --------------------------------------------------------------------------- #
def test_radar_weights_sum_to_one():
    assert sum(RADAR_WEIGHTS.values()) == pytest.approx(1.0)
    assert set(RADAR_WEIGHTS) == {"depth", "trend", "rsi", "quality"}


def test_rsi_factor_bounds():
    assert _rsi_factor(30.0) == pytest.approx(100.0)
    assert _rsi_factor(70.0) == pytest.approx(0.0)
    assert _rsi_factor(50.0) == pytest.approx(50.0)
    assert _rsi_factor(10.0) == pytest.approx(100.0)  # clipped
    assert _rsi_factor(None) == pytest.approx(50.0)   # unknown → neutral


def test_analyze_one_gates_shallow_pullbacks():
    # Monotonic rise → depth 0 today → not a setup.
    adj = _series(list(np.linspace(100, 200, 300)))
    assert _analyze_one(_metrics(), adj, 63) is None


def test_echo_stats_labels_kind_and_min_depth():
    s = _series(list(np.linspace(100, 200, 60)))
    eps = [s.index[i] for i in (0, 10, 20, 30, 40, 45)]
    exact = echo_stats(s, eps, horizon=5, min_episodes=6, kind="exact", min_depth_pct=10.0)
    wide = echo_stats(s, eps, horizon=5, min_episodes=6, kind="at_least", min_depth_pct=10.0)
    assert exact.kind == "exact" and exact.min_depth_pct == 10.0
    assert wide.kind == "at_least"


def test_widened_bucket_is_a_superset_of_the_exact_bucket():
    # Dips of ~12% and ~22%: the exact [10,15) bucket sees one run, the widened
    # "at least 10%" bucket must see at least as many episodes.
    depth_vals = [0] * 10 + [12, 12] + [0] * 20 + [22, 22] + [0] * 10
    depth = _series(depth_vals)
    above = pd.Series(True, index=depth.index)
    exact = find_setup_episodes(depth, above, (10.0, 15.0), True, min_gap=10)
    wide = find_setup_episodes(depth, above, (10.0, 1000.0), True, min_gap=10)
    assert len(wide) >= len(exact)
    assert len(exact) == 1 and len(wide) == 2


def test_analyze_one_detects_dip():
    # Long rise then a ~12% dip over the last sessions.
    rise = list(np.linspace(100, 200, 280))
    dip = list(np.linspace(200, 176, 12))  # -12%
    adj = _series(rise + dip)
    analyzed = _analyze_one(_metrics(), adj, 63)
    assert analyzed is not None
    depth_pct, depth_rank, echo = analyzed
    assert depth_pct == pytest.approx(12.0, abs=0.5)
    assert depth_rank > 90  # deepest dip this stock has seen → high own-history rank
    assert echo is None     # no similar historical episodes in a monotonic rise
