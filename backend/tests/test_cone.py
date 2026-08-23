"""Tests for the cone of uncertainty — the stationary block-bootstrap forecast."""

from __future__ import annotations

import datetime as dt
import re
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from app.services import cone
from app.services.cone import (
    _bands,
    _log_returns,
    _simulate,
    _stationary_bootstrap_indices,
    build_cone,
)

FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing|dump it|avoid buying)\b",
    re.IGNORECASE,
)

_AS_OF = dt.date(2026, 8, 21)


def _adj_series(n: int = 600, seed: int = 0, sigma: float = 0.015) -> pd.Series:
    rng = np.random.default_rng(seed)
    rets = rng.normal(0.0003, sigma, n)
    prices = 100.0 * np.exp(np.cumsum(rets))
    idx = pd.bdate_range(end=_AS_OF, periods=n)
    return pd.Series(prices, index=idx)


@pytest.fixture
def patched(monkeypatch):
    """Drive the cone off synthetic closes, no DB. NVDA (rich), VOO (benchmark),
    XE (thin, < 250 sessions)."""
    closes = {
        "NVDA": _adj_series(600, seed=1, sigma=0.025),
        "VOO": _adj_series(600, seed=2, sigma=0.010),
        "XE": _adj_series(80, seed=3, sigma=0.05),
    }
    metrics = {t: SimpleNamespace(price=round(float(s.iloc[-1]), 2)) for t, s in closes.items()}
    monkeypatch.setattr(cone.analytics, "universe_closes", lambda: closes)
    monkeypatch.setattr(cone.analytics, "universe_metrics", lambda: (metrics, _AS_OF))
    cone._cone_cache.update(key=None, by_params={})
    return closes


# --------------------------------------------------------------------------- #
# Pure math
# --------------------------------------------------------------------------- #
def test_bootstrap_resamples_consecutive_runs():
    # A very long mean block ⇒ almost never restart ⇒ mostly +1 (mod n) steps.
    rng = np.random.default_rng(7)
    idx = _stationary_bootstrap_indices(rng, n_obs=100, n_paths=1, horizon=60, mean_block=10_000)
    row = idx[0]
    consecutive = sum(int(row[t] == (row[t - 1] + 1) % 100) for t in range(1, 60))
    assert consecutive >= 55  # runs of consecutive real days, not shuffled singletons


def test_bootstrap_shape_and_range():
    rng = np.random.default_rng(0)
    idx = _stationary_bootstrap_indices(rng, n_obs=250, n_paths=2000, horizon=63)
    assert idx.shape == (2000, 63)
    assert idx.min() >= 0 and idx.max() < 250


def test_simulate_starts_at_one_and_is_lognormal_positive():
    rets = _log_returns(_adj_series(600, seed=5))
    rng = np.random.default_rng(42)
    mult = _simulate(rets, rng, horizon=63)
    assert mult.shape == (2000, 64)  # horizon + 1 (session 0 included)
    assert np.allclose(mult[:, 0], 1.0)  # everyone starts at the anchor
    assert (mult > 0).all()  # multipliers of a price can never go negative


def test_bands_are_ordered_at_every_point():
    rets = _log_returns(_adj_series(600, seed=5))
    mult = _simulate(rets, np.random.default_rng(1), horizon=126)
    bands = _bands(mult, list(range(0, 127, 10)))
    for pt in bands:
        assert pt.p10 <= pt.p25 <= pt.p50 <= pt.p75 <= pt.p90


# --------------------------------------------------------------------------- #
# build_cone integration
# --------------------------------------------------------------------------- #
def test_cone_bands_start_at_one_and_widen(patched):
    resp = cone._build("NVDA", 126)
    assert resp.bands[0].session == 0
    assert resp.bands[0].p10 == resp.bands[0].p50 == resp.bands[0].p90 == 1.0
    # The envelope widens with time: the final spread beats the first.
    first_spread = resp.bands[1].p90 - resp.bands[1].p10
    last_spread = resp.bands[-1].p90 - resp.bands[-1].p10
    assert last_spread > first_spread


def test_cone_percentiles_ordered_everywhere(patched):
    resp = cone._build("NVDA", 252)
    for pt in resp.bands + [resp.end]:
        assert pt.p10 <= pt.p25 <= pt.p50 <= pt.p75 <= pt.p90


def test_cone_is_deterministic(patched):
    a = cone._build("NVDA", 126).model_dump()
    b = cone._build("NVDA", 126).model_dump()
    assert a == b


def test_horizons_differ(patched):
    short = cone._build("NVDA", 21)
    long = cone._build("NVDA", 252)
    assert short.horizon_sessions == 21 and long.horizon_sessions == 252
    assert short.end.session == 21 and long.end.session == 252
    # A longer horizon scatters wider.
    assert (long.end.p90 - long.end.p10) > (short.end.p90 - short.end.p10)


def test_benchmark_cone_present_and_distinct(patched):
    resp = cone._build("NVDA", 126)
    assert resp.benchmark is not None
    assert resp.benchmark.ticker == "VOO"
    # NVDA is the wilder ride (higher sigma) → wider terminal cone than VOO.
    nvda_spread = resp.end.p90 - resp.end.p10
    voo_spread = resp.benchmark.end.p90 - resp.benchmark.end.p10
    assert nvda_spread > voo_spread


def test_voo_cone_omits_its_own_benchmark(patched):
    resp = cone._build("VOO", 126)
    assert resp.benchmark is None  # no VOO-vs-VOO


def test_sample_paths_align_and_count(patched):
    resp = cone._build("NVDA", 63)
    assert len(resp.sample_paths) == 24
    assert all(len(p) == len(resp.bands) for p in resp.sample_paths)
    assert all(p[0] == 1.0 for p in resp.sample_paths)
    assert resp.samples_up + resp.samples_down <= len(resp.sample_paths)
    assert resp.samples_up >= 0 and resp.samples_down >= 0


def test_thin_history_raises_teaching_error(patched):
    with pytest.raises(ValueError, match="history"):
        cone._build("XE", 126)


def test_unknown_ticker_raises_keyerror(patched):
    with pytest.raises(KeyError):
        cone._build("NOPE", 126)


def test_bad_horizon_raises(patched):
    with pytest.raises(ValueError, match="Horizon"):
        cone._build("NVDA", 999)


def test_caveat_obeys_the_copy_law(patched):
    resp = cone._build("NVDA", 126)
    blob = resp.caveat.lower()
    assert FORBIDDEN.search(resp.caveat) is None
    assert "median" not in blob
    assert "http" not in blob
    assert resp.caveat.strip()


def test_start_price_and_vol_are_reported(patched):
    resp = cone._build("NVDA", 126)
    assert resp.start_price > 0
    assert resp.vol_annualized_pct > 0
    assert resp.n_paths == 2000
    assert resp.n_history_sessions >= 250


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
@pytest.fixture
def client(db, patched, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services import market as market_mod

    monkeypatch.setattr(market_mod, "start_background_warm", lambda: None)
    return TestClient(app)


def test_router_returns_cone(client):
    r = client.get("/cone", params={"ticker": "nvda", "horizon": 126})
    assert r.status_code == 200
    body = r.json()
    assert body["ticker"] == "NVDA"
    assert body["horizon_sessions"] == 126
    assert len(body["bands"]) > 1


def test_router_status_codes(client):
    assert client.get("/cone", params={"ticker": "NOPE"}).status_code == 404
    assert client.get("/cone", params={"ticker": "XE"}).status_code == 422
    assert client.get("/cone", params={"ticker": "NVDA", "horizon": 5}).status_code == 422
