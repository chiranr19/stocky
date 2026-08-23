# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""The cone of uncertainty — a Monte Carlo range of plausible futures.

The only honest "forecast" in the app: instead of a single predicted price, we
resample the stock's OWN past daily moves thousands of times and read off where
those simulated futures scatter. The result is a *range*, always widening, never
a point call.

Method — the **stationary block bootstrap** (Politis & Romano, 1994): rather than
drawing single days independently (which erases the fact that calm and stormy
days come in runs), we resample *runs of consecutive real days* of random length.
That inherits the fat tails, the skew, AND the volatility clustering that a
smooth bell-curve (geometric Brownian motion) understates. Bands are pointwise
percentiles across the paths.

Read-only over the analytics price cache (the radar/learn contract): never
fetches inline. Deterministic — the RNG is seeded from (ticker, as-of, horizon)
so the same request always returns the same cone (cacheable, testable).
"""

from __future__ import annotations

import datetime as dt
import hashlib
import threading

import numpy as np
import pandas as pd

from ..config import display_name, settings
from ..models import ConeBenchmark, ConePoint, ConeResponse
from . import analytics

# The horizons the UI offers, in trading sessions (≈ 1m / 3m / 6m / 1y).
CONE_HORIZONS: tuple[int, ...] = (21, 63, 126, 252)
_DEFAULT_HORIZON = 126

_N_PATHS = 2000
_HISTORY = 504          # ~2 years of daily moves to resample from
_MIN_SESSIONS = 250     # a forecast needs at least a year of base to stand on
_MEAN_BLOCK = 10        # average run length of the resampled blocks
_MAX_BAND_POINTS = 40   # downsample the envelope to this many x-positions
_N_SAMPLES = 24         # individual futures drawn for the "run the futures" replay
_PCTS = (10, 25, 50, 75, 90)

_lock = threading.Lock()
_cone_cache: dict = {"key": None, "by_params": {}}


def _seed(ticker: str, as_of: dt.date, horizon: int) -> int:
    """A stable integer seed (Python's hash() is salted per-process; sha256 isn't)."""
    raw = f"{ticker}|{as_of.isoformat()}|{horizon}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:12], 16)


def _stationary_bootstrap_indices(
    rng: np.random.Generator, n_obs: int, n_paths: int, horizon: int,
    mean_block: int = _MEAN_BLOCK,
) -> np.ndarray:
    """Index matrix (n_paths × horizon) into the return series via the stationary
    block bootstrap: each step either continues the current run (wrapping around
    the end of the series) or, with probability 1/mean_block, jumps to a fresh
    random start. Runs therefore have a geometric length with the given mean, and
    the resampled series is stationary (Politis & Romano)."""
    p = 1.0 / mean_block
    idx = np.empty((n_paths, horizon), dtype=np.int64)
    idx[:, 0] = rng.integers(0, n_obs, size=n_paths)
    if horizon == 1:
        return idx
    restart = rng.random((n_paths, horizon)) < p          # jump at this step?
    fresh_starts = rng.integers(0, n_obs, size=(n_paths, horizon))
    for t in range(1, horizon):
        cont = (idx[:, t - 1] + 1) % n_obs                 # wrap-around continuation
        idx[:, t] = np.where(restart[:, t], fresh_starts[:, t], cont)
    return idx


def _simulate(
    log_returns: np.ndarray, rng: np.random.Generator, horizon: int,
) -> np.ndarray:
    """Return an (n_paths × horizon+1) array of price MULTIPLIERS (col 0 = 1.0)."""
    idx = _stationary_bootstrap_indices(rng, len(log_returns), _N_PATHS, horizon)
    sampled = log_returns[idx]                             # (n_paths, horizon)
    cum = np.cumsum(sampled, axis=1)
    mult = np.exp(cum)
    ones = np.ones((_N_PATHS, 1))
    return np.concatenate([ones, mult], axis=1)            # (n_paths, horizon+1)


def _band_sessions(horizon: int) -> list[int]:
    """Evenly-spaced session indices (0..horizon), always including both ends."""
    n = min(horizon + 1, _MAX_BAND_POINTS)
    if horizon + 1 <= n:
        return list(range(horizon + 1))
    return sorted({round(i * horizon / (n - 1)) for i in range(n)})


def _bands(mult: np.ndarray, sessions: list[int]) -> list[ConePoint]:
    pct = np.percentile(mult[:, sessions], _PCTS, axis=0)  # (5, len(sessions))
    return [
        ConePoint(
            session=s,
            p10=round(float(pct[0, i]), 4),
            p25=round(float(pct[1, i]), 4),
            p50=round(float(pct[2, i]), 4),
            p75=round(float(pct[3, i]), 4),
            p90=round(float(pct[4, i]), 4),
        )
        for i, s in enumerate(sessions)
    ]


def _end_point(mult: np.ndarray, horizon: int) -> ConePoint:
    pct = np.percentile(mult[:, -1], _PCTS)
    return ConePoint(
        session=horizon,
        p10=round(float(pct[0]), 4),
        p25=round(float(pct[1]), 4),
        p50=round(float(pct[2]), 4),
        p75=round(float(pct[3]), 4),
        p90=round(float(pct[4]), 4),
    )


def _log_returns(adj: pd.Series) -> np.ndarray:
    tail = adj.dropna().tail(_HISTORY + 1)
    rets = np.diff(np.log(tail.to_numpy(dtype=float)))
    return rets[np.isfinite(rets)]


def _build(ticker: str, horizon: int) -> ConeResponse:
    """Assemble the cone for one ticker. Raises KeyError (unknown ticker) or
    ValueError (thin history / bad horizon) for the router to translate."""
    if horizon not in CONE_HORIZONS:
        raise ValueError(
            f"Horizon must be one of {CONE_HORIZONS} trading days — got {horizon}."
        )

    ticker = ticker.upper()
    closes = analytics.universe_closes()
    metrics, as_of = analytics.universe_metrics()
    adj = closes.get(ticker)
    if adj is None:
        raise KeyError(ticker)

    n_sessions = int(adj.dropna().shape[0])
    if n_sessions < _MIN_SESSIONS:
        raise ValueError(
            f"{display_name(ticker)} has only {n_sessions} trading days of history — "
            f"a forecast needs at least {_MIN_SESSIONS} (about a year) to have a base "
            "to stand on. A blank past can't be simulated."
        )

    log_rets = _log_returns(adj)
    if log_rets.size < _MIN_SESSIONS - 1:
        raise ValueError(
            f"{display_name(ticker)} doesn't have enough clean daily moves to simulate yet."
        )

    m = metrics.get(ticker)
    start_price = float(m.price) if m is not None else round(float(adj.iloc[-1]), 2)
    vol_annual = round(float(np.std(log_rets, ddof=1) * np.sqrt(252) * 100.0), 1)

    rng = np.random.default_rng(_seed(ticker, as_of, horizon))
    mult = _simulate(log_rets, rng, horizon)
    sessions = _band_sessions(horizon)
    bands = _bands(mult, sessions)
    end = _end_point(mult, horizon)

    # A handful of whole paths for the theatrical replay, aligned to the band
    # x-positions so they overlay the envelope cleanly.
    step = max(1, _N_PATHS // _N_SAMPLES)
    sample_rows = mult[::step][:_N_SAMPLES]
    sample_paths = [
        [round(float(row[s]), 4) for s in sessions] for row in sample_rows
    ]
    finals = sample_rows[:, -1]
    samples_up = int((finals > 1.0).sum())
    samples_down = int((finals < 1.0).sum())

    # The benchmark's cone, drawn the same way, so every forecast answers
    # "and what would just holding VOO have looked like?".
    benchmark = None
    bench_adj = closes.get(settings.benchmark)
    if bench_adj is not None and ticker != settings.benchmark:
        bench_rets = _log_returns(bench_adj)
        if bench_rets.size >= _MIN_SESSIONS - 1:
            b_rng = np.random.default_rng(_seed(settings.benchmark, as_of, horizon))
            b_mult = _simulate(bench_rets, b_rng, horizon)
            benchmark = ConeBenchmark(
                ticker=settings.benchmark,
                name=display_name(settings.benchmark),
                bands=_bands(b_mult, sessions),
                end=_end_point(b_mult, horizon),
            )

    caveat = (
        f"These bands come from resampling {log_rets.size} of {display_name(ticker)}'s "
        "own past daily moves in short runs, 2,000 times over — not a crystal ball and "
        "not a bell curve. They show how widely the past would have scattered the next "
        f"{horizon} trading days, so read the WIDTH of the cone, not its center: two "
        "years of data can pin down the wobble but not the drift. Each band is a "
        "percentile at that day, so a single future can wander outside it and come back."
    )

    return ConeResponse(
        ticker=ticker,
        name=display_name(ticker),
        as_of=as_of,
        horizon_sessions=horizon,
        start_price=start_price,
        n_paths=_N_PATHS,
        n_history_sessions=int(log_rets.size),
        vol_annualized_pct=vol_annual,
        bands=bands,
        sample_paths=sample_paths,
        end=end,
        samples_up=samples_up,
        samples_down=samples_down,
        benchmark=benchmark,
        caveat=caveat,
    )


def build_cone(ticker: str, horizon: int = _DEFAULT_HORIZON) -> ConeResponse:
    """Cached per (metrics-cache generation, ticker, horizon)."""
    cache_key = analytics._cache["key"]
    params = (ticker.upper(), horizon)
    with _lock:
        if _cone_cache["key"] != cache_key:
            _cone_cache["key"] = cache_key
            _cone_cache["by_params"] = {}
        cached = _cone_cache["by_params"].get(params)
        if cached is not None:
            return cached
    result = _build(ticker, horizon)  # may raise; don't cache failures
    with _lock:
        if _cone_cache["key"] == cache_key:
            _cone_cache["by_params"][params] = result
    return result
