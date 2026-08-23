"""Tests for the archetype engine — total, exclusive, and law-abiding."""

from __future__ import annotations

import datetime as dt
import itertools
import re

import numpy as np
import pandas as pd
import pytest

from app.services import archetypes
from app.services.archetypes import ARCHETYPES, assign, classify
from app.services.metrics import StockMetrics

FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing|dump it|avoid buying)\b",
    re.IGNORECASE,
)


def _m(**over) -> StockMetrics:
    base = dict(
        ticker="TEST", price=100.0, prev_close=99.0, change_pct=1.0, open=99.5,
        gap_pct=0.5, ma50=95.0, ma200=90.0, above_ma50=True, above_ma200=True,
        rsi14=50.0, rsi_signal=None, vol_90d=25.0, ret_1m=2.0, ret_3m=6.0,
        ret_1y=18.0, high_52w=120.0, low_52w=70.0, range_52w_position=0.6,
        avg_dollar_volume_20d=1e8, volume=1_000_000, avg_volume_30d=1_000_000,
        volume_ratio=1.0, max_drawdown_1y=-15.0, is_new_high_52w=False,
        is_new_low_52w=False, cross=None, cross_date=None, spark=[],
    )
    base.update(over)
    return StockMetrics(**base)


# --------------------------------------------------------------------------- #
# Totality + uniqueness
# --------------------------------------------------------------------------- #
_KNOWN = {a.code for a in ARCHETYPES}


@pytest.mark.parametrize(
    "vol,ret,ma,pos,rsi,sessions",
    list(itertools.product(
        [10.0, 30.0, 50.0, 70.0, None],
        [-40.0, -10.0, 0.0, 15.0, 60.0, None],
        [True, False],
        [0.05, 0.5, 0.99],
        [25.0, 50.0, 80.0],
        [50, 300],
    )),
)
def test_classify_is_total_and_returns_a_registered_archetype(vol, ret, ma, pos, rsi, sessions):
    if vol is None or ret is None:
        m = _m(vol_90d=vol, ret_1y=ret)
    else:
        m = _m(vol_90d=vol, ret_1y=ret, above_ma200=ma, range_52w_position=pos, rsi14=rsi)
    a = classify(m, sessions)
    assert a.code in _KNOWN


def test_none_and_thin_history_are_unwritten():
    assert classify(None, 0).code == "unwritten_story"
    assert classify(_m(), 100).code == "unwritten_story"          # < 200 sessions
    assert classify(_m(ret_1y=None), 300).code == "unwritten_story"
    assert classify(_m(vol_90d=None), 300).code == "unwritten_story"


def test_representative_archetypes_fire_as_expected():
    assert classify(_m(vol_90d=70.0), 300).code == "lottery_ticket"
    assert classify(_m(vol_90d=46.0), 300).code == "rollercoaster"
    assert classify(_m(above_ma200=False, ret_1y=-30.0, vol_90d=30.0), 300).code == "fallen_star"
    assert classify(_m(above_ma200=True, vol_90d=18.0, ret_1y=20.0), 300).code == "calm_compounder"
    assert classify(_m(range_52w_position=0.99, rsi14=75.0, vol_90d=30.0), 300).code == "hot_hand"
    assert classify(_m(vol_90d=18.0, ret_1y=-5.0, above_ma200=False), 300).code == "sleeping_giant"


# --------------------------------------------------------------------------- #
# Copy law
# --------------------------------------------------------------------------- #
def test_every_archetype_obeys_the_house_rules():
    # Render each archetype's story with a metric that actually classifies to it
    # (a story is only ever called when its own predicate matched), plus None for
    # the unwritten case. This checks every REACHABLE (archetype, metric) pairing.
    samples = [
        None,
        _m(vol_90d=70.0, ret_1y=20.0), _m(above_ma200=False, ret_1y=-30.0),
        _m(vol_90d=46.0, ret_1y=10.0), _m(range_52w_position=0.99, rsi14=78.0, vol_90d=30.0),
        _m(vol_90d=18.0, ret_1y=22.0), _m(vol_90d=18.0, ret_1y=-4.0, above_ma200=False),
        _m(above_ma200=True, ret_1y=8.0), _m(above_ma200=False, ret_1y=5.0, vol_90d=30.0),
    ]
    # Every archetype has a non-empty role ≤ 40 chars and a lesson.
    for a in ARCHETYPES:
        assert len(a.role) <= 40, a.code
        assert a.role.strip() and a.lesson.strip()
    # Every reachable rendering is compliant.
    for m in samples:
        sessions = 100 if m is None else 300
        a = classify(m, sessions)
        story = a.story(m, sessions)
        blob = f"{a.role} {a.lesson} {story}"
        assert FORBIDDEN.search(blob) is None, f"advice phrasing in {a.code}"
        assert "median" not in blob.lower(), f"'median' in {a.code}"
        assert "http" not in blob.lower(), f"URL in {a.code}"
        assert story.strip()


def test_assign_shape():
    got = assign(_m(vol_90d=70.0), 300)
    assert set(got) == {"role", "group", "story", "lesson"}
    assert got["group"] == archetypes.ARCHETYPE_GROUP == "scout"


# --------------------------------------------------------------------------- #
# Integration with learn._build
# --------------------------------------------------------------------------- #
def test_curated_wins_and_uncurated_gets_an_archetype():
    from app.services import learn

    rng = np.random.default_rng(1)
    tickers = ["NVDA", "DVA"]
    metrics = {
        "NVDA": _m(ticker="NVDA"),
        "DVA": _m(ticker="DVA", vol_90d=18.0, ret_1y=12.0, above_ma200=True),
    }
    closes = {t: pd.Series(100 + np.cumsum(rng.normal(0.05, 1.0, 300))) for t in tickers}
    b = learn._build(metrics, closes, dt.date(2026, 8, 21), tickers=tickers)
    by = {m.ticker: m for m in b.members}
    assert by["NVDA"].role_source == "curated"
    assert by["NVDA"].role == "The headline act"
    assert by["DVA"].role_source == "archetype"
    assert by["DVA"].group == "scout"
    assert by["DVA"].role_story.strip()
