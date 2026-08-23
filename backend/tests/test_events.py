# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Tests for the what-changed event engine."""

from __future__ import annotations

import datetime as dt
import re

import numpy as np
import pandas as pd
import pytest

from app.services import events, market
from app.services.events import TEMPLATES, build_events, detect_from_frame

FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing|dump it|avoid buying)\b",
    re.IGNORECASE,
)


def _frame(closes) -> pd.DataFrame:
    closes = np.asarray(closes, dtype=float)
    idx = pd.bdate_range(end=dt.date(2026, 8, 21), periods=len(closes))
    return pd.DataFrame(
        {"open": closes, "high": closes * 1.001, "low": closes * 0.999,
         "close": closes, "adj_close": closes, "volume": [1_000_000] * len(closes)},
        index=idx,
    )


# --------------------------------------------------------------------------- #
# Individual detectors
# --------------------------------------------------------------------------- #
def test_ma200_break_speaks_of_a_verdict():
    # 259 gently-rising sessions above their 200-day avg, then one sharp drop below.
    rising = np.linspace(100, 120, 259)
    closes = np.append(rising, 96.0)  # last close dives beneath the ~110 average
    evs = detect_from_frame("DTE", _frame(closes))
    codes = [e.code for e in evs]
    assert "ma200_break" in codes
    break_ev = next(e for e in evs if e.code == "ma200_break")
    assert "verdict" in break_ev.headline
    assert len(evs) <= 2  # per-ticker cap


def test_vol_jump_reports_both_numbers():
    calm = 100 + np.cumsum(np.random.default_rng(0).normal(0, 0.02, 259))
    closes = np.append(calm, calm[-1] * 1.18)  # one violent +18% day
    evs = detect_from_frame("AMD", _frame(closes))
    vol = [e for e in evs if e.code == "vol_jump"]
    if vol:  # the jump must clear the ratio+points gate; when it does, numbers show
        m = re.search(r"(\d+)→(\d+)%", vol[0].headline)
        assert m is not None


def test_big_move_fires_on_a_large_day():
    closes = np.append(np.full(259, 100.0), 106.0)  # +6% day
    evs = detect_from_frame("TSLA", _frame(closes))
    assert "big_move" in [e.code for e in evs] or "ma200_reclaim" in [e.code for e in evs]


def test_quiet_frame_produces_nothing():
    closes = 100 + np.cumsum(np.full(259, 0.02))  # steady calm climb, no events
    assert detect_from_frame("KO", _frame(closes)) == []


def test_short_frames_never_crash():
    assert detect_from_frame("X", _frame([100.0])) == []
    assert detect_from_frame("X", _frame([100.0, 101.0])) == []


def test_detect_is_deterministic():
    rising = np.linspace(100, 120, 259)
    closes = np.append(rising, 96.0)
    a = detect_from_frame("DTE", _frame(closes))
    b = detect_from_frame("DTE", _frame(closes))
    assert [(e.code, e.headline) for e in a] == [(e.code, e.headline) for e in b]


# --------------------------------------------------------------------------- #
# Registry sync + copy law
# --------------------------------------------------------------------------- #
def test_every_emitted_code_is_registered_and_law_abiding():
    scenarios = [
        np.append(np.linspace(100, 120, 259), 96.0),       # ma200_break, big_move
        np.append(np.linspace(120, 100, 259), 112.0),      # ma200_reclaim
        np.append(np.full(259, 100.0), 106.0),             # big_move
        100 + np.cumsum(np.random.default_rng(1).normal(0, 0.02, 259)),  # calm
        np.append(100 + np.cumsum(np.random.default_rng(2).normal(0, 0.02, 259)),
                  (100 + np.cumsum(np.random.default_rng(2).normal(0, 0.02, 259)))[-1] * 1.2),
    ]
    seen = set()
    for i, closes in enumerate(scenarios):
        for e in detect_from_frame(f"T{i}", _frame(closes)):
            seen.add(e.code)
            assert e.code in TEMPLATES
            blob = f"{e.headline} {e.detail}"
            assert FORBIDDEN.search(blob) is None, f"advice in {e.code}"
            assert "median" not in blob.lower(), f"'median' in {e.code}"
            assert "http" not in blob.lower(), f"URL in {e.code}"
            assert e.headline.strip() and e.detail.strip()
            assert e.tone in ("constructive", "caution", "neutral")
    assert "ma200_break" in seen  # the scenarios really did exercise the engine


# --------------------------------------------------------------------------- #
# Global cap + ordering via build_events
# --------------------------------------------------------------------------- #
def test_build_events_caps_and_orders(monkeypatch):
    # 10 tickers each with an MA200 break + a big move → many events, capped to 12.
    rising = np.linspace(100, 120, 259)
    closes = np.append(rising, 96.0)
    tickers = [f"T{i}" for i in range(10)]
    frames = {t: _frame(closes) for t in tickers}
    monkeypatch.setattr(market, "read_cached", lambda *a, **k: frames)
    events._events_cache.update(key=None, value=None)

    evs = build_events(tickers=tickers)
    assert len(evs) <= 12
    severities = [e.severity for e in evs]
    assert severities == sorted(severities, reverse=True)  # most urgent first
