"""Tests for the v1.0 study-viz backend: constellation math + basket study fields.

The v0.5 lesson — every pass-through seam gets a regression test — so rain,
regime, series_start, rain_dates and the constellation all survive to the model.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

from app.config import WATCHLIST
from app.services import learn
from app.services.metrics import mds_layout, mst_edges


def _series(values, start="2021-01-04") -> pd.Series:
    idx = pd.bdate_range(start=start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def _corr(labels, matrix) -> dict:
    return {"labels": list(labels), "matrix": [[float(x) for x in row] for row in matrix]}


# --------------------------------------------------------------------------- #
# MDS layout
# --------------------------------------------------------------------------- #
def test_mds_places_correlated_names_closer():
    # A,B move together (0.95); C is their opposite (-0.9).
    corr = _corr(
        ["A", "B", "C"],
        [[1.0, 0.95, -0.9], [0.95, 1.0, -0.88], [-0.9, -0.88, 1.0]],
    )
    pts = {p["ticker"]: (p["x"], p["y"]) for p in mds_layout(corr)}

    def d(u, v):
        return ((pts[u][0] - pts[v][0]) ** 2 + (pts[u][1] - pts[v][1]) ** 2) ** 0.5

    assert d("A", "B") < d("A", "C")


def test_mds_is_deterministic_and_normalized():
    corr = _corr(
        ["A", "B", "C", "D"],
        [
            [1.0, 0.8, 0.1, -0.3],
            [0.8, 1.0, 0.2, -0.2],
            [0.1, 0.2, 1.0, 0.4],
            [-0.3, -0.2, 0.4, 1.0],
        ],
    )
    a = mds_layout(corr)
    b = mds_layout(corr)
    assert a == b  # no sign-flip wobble
    for p in a:
        assert -1.0 <= p["x"] <= 1.0 and -1.0 <= p["y"] <= 1.0


def test_mds_degenerate_inputs_dont_crash():
    assert mds_layout({"labels": [], "matrix": []}) == []
    single = mds_layout(_corr(["A"], [[1.0]]))
    assert single == [{"ticker": "A", "x": 0.0, "y": 0.0}]


# --------------------------------------------------------------------------- #
# Minimum spanning tree
# --------------------------------------------------------------------------- #
def test_mst_has_n_minus_one_edges_and_is_connected():
    corr = _corr(
        ["A", "B", "C", "D"],
        [
            [1.0, 0.9, 0.3, 0.1],
            [0.9, 1.0, 0.4, 0.2],
            [0.3, 0.4, 1.0, 0.5],
            [0.1, 0.2, 0.5, 1.0],
        ],
    )
    edges = mst_edges(corr)
    assert len(edges) == 3  # n - 1
    nodes = set()
    for e in edges:
        nodes.update([e["a"], e["b"]])
    assert nodes == {"A", "B", "C", "D"}  # spans everyone


def test_mst_contains_the_closest_pair():
    # A-B is the strongest correlation ⇒ the shortest distance ⇒ always an edge.
    corr = _corr(
        ["A", "B", "C", "D"],
        [
            [1.0, 0.98, 0.2, 0.1],
            [0.98, 1.0, 0.3, 0.2],
            [0.2, 0.3, 1.0, 0.4],
            [0.1, 0.2, 0.4, 1.0],
        ],
    )
    pairs = {frozenset([e["a"], e["b"]]) for e in mst_edges(corr)}
    assert frozenset(["A", "B"]) in pairs


def test_mst_edge_carries_the_correlation():
    corr = _corr(["A", "B"], [[1.0, 0.77], [0.77, 1.0]])
    edges = mst_edges(corr)
    assert edges == [{"a": "A", "b": "B", "r": 0.77}]


# --------------------------------------------------------------------------- #
# _regime_1y / _rain unit behavior
# --------------------------------------------------------------------------- #
def test_regime_true_in_an_uptrend_false_in_a_downtrend():
    up = _series(np.linspace(50, 150, 300))
    sampled_up = learn._downsample_series(up)
    reg_up = learn._regime_1y(up, sampled_up)
    assert reg_up[-1] is True  # last price sits above its trailing 200-day line

    down = _series(np.linspace(150, 50, 300))
    sampled_down = learn._downsample_series(down)
    reg_down = learn._regime_1y(down, sampled_down)
    assert reg_down[-1] is False
    assert len(reg_up) == len(sampled_up)  # aligns to the race x-axis


def test_rain_aligns_to_the_shared_calendar():
    dates = list(_series(np.zeros(60)).index)
    adj = _series(100 + np.cumsum(np.ones(300) * 0.1))
    rain = learn._rain(adj, dates)
    assert len(rain) == 60
    assert all(v is None or isinstance(v, float) for v in rain)


def test_rain_marks_missing_days_as_none():
    dates = list(pd.bdate_range(start="2021-01-04", periods=60))
    # A name whose history starts much later misses the early calendar days.
    adj = _series(100 + np.cumsum(np.ones(20) * 0.1), start=dates[40].strftime("%Y-%m-%d"))
    rain = learn._rain(adj, dates)
    assert len(rain) == 60
    assert rain[0] is None  # didn't trade on the earliest shared day


# --------------------------------------------------------------------------- #
# _build integration + model pass-through
# --------------------------------------------------------------------------- #
def test_build_attaches_rain_regime_and_constellation():
    rng = np.random.default_rng(3)
    tickers = ["AMZN", "VOO", "FE"]
    from app.services.metrics import StockMetrics

    def _m(t):
        return StockMetrics(
            ticker=t, price=100.0, prev_close=99.0, change_pct=1.0, open=99.5,
            gap_pct=0.5, ma50=95.0, ma200=90.0, above_ma50=True, above_ma200=True,
            rsi14=50.0, rsi_signal=None, vol_90d=25.0, ret_1m=2.0, ret_3m=6.0,
            ret_1y=18.0, high_52w=120.0, low_52w=70.0, range_52w_position=0.6,
            avg_dollar_volume_20d=1e8, volume=1_000_000, avg_volume_30d=1_000_000,
            volume_ratio=1.0, max_drawdown_1y=-15.0, is_new_high_52w=False,
            is_new_low_52w=False, cross=None, cross_date=None, spark=[],
        )

    metrics = {t: _m(t) for t in tickers}
    closes = {t: _series(100 + np.cumsum(rng.normal(0.05, 1.0, 300))) for t in tickers}
    b = learn._build(metrics, closes, dt.date(2026, 8, 21))

    assert len(b.rain_dates) == 60
    assert set(b.constellation.keys()) == {"nodes", "mst"}
    assert {n["ticker"] for n in b.constellation["nodes"]} == set(tickers)
    assert len(b.constellation["mst"]) == len(tickers) - 1

    by = {m.ticker: m for m in b.members}
    amzn = by["AMZN"]
    assert len(amzn.rain) == len(b.rain_dates)
    assert len(amzn.regime_1y) == len(amzn.series_1y)
    assert amzn.series_start is not None

    # Pass-through survives serialization (the v0.5 silent-drop guard).
    dumped = b.model_dump()
    assert "rain_dates" in dumped and "constellation" in dumped
    member0 = dumped["members"][0]
    assert {"rain", "regime_1y", "series_start"} <= set(member0)


def test_build_without_benchmark_has_empty_rain_calendar():
    b = learn._build({}, {}, dt.date(2026, 8, 21))
    assert b.rain_dates == []
    assert b.constellation == {"nodes": [], "mst": []}
    assert all(m.rain == [] for m in b.members)
    assert [m.ticker for m in b.members] == WATCHLIST  # order still intact
