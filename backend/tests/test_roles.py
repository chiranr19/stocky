# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Tests for the curated watchlist roles + the /learn basket builder.

Covers: role coverage and taxonomy, the no-advice copy law over every curated
string, provenance, and that ``learn._build`` degrades honestly (never crashes,
never invents a risk picture) across empty and adversarial inputs.
"""

from __future__ import annotations

import datetime as dt
import re

import numpy as np
import pandas as pd
import pytest

from app.config import MARKET_LAWS, ROLES_AS_OF, WATCHLIST, WATCHLIST_ROLES
from app.services import learn
from app.services.metrics import StockMetrics

# Both house-rule regexes at once (the reading layer's + the flag layer's extras).
FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing|dump it|avoid buying)\b",
    re.IGNORECASE,
)
GROUPS = {"mega", "umbrella", "wildcard", "benchmark"}


def _all_role_strings() -> list[str]:
    out = list(MARKET_LAWS)
    for r in WATCHLIST_ROLES.values():
        out += [r["role"], r["story"], r["lesson"]]
    return out


def _series(values, start="2021-01-04") -> pd.Series:
    idx = pd.bdate_range(start=start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


def _metrics(ticker="TEST", **over) -> StockMetrics:
    base = dict(
        ticker=ticker, price=100.0, prev_close=99.0, change_pct=1.0, open=99.5,
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
# Curated data: coverage, taxonomy, provenance
# --------------------------------------------------------------------------- #
def test_every_watchlist_ticker_has_a_role():
    assert set(WATCHLIST_ROLES) == set(WATCHLIST)


def test_group_taxonomy_is_closed():
    for t, r in WATCHLIST_ROLES.items():
        assert r["group"] in GROUPS, f"{t} has unknown group {r['group']!r}"


def test_role_fields_are_substantive():
    for t, r in WATCHLIST_ROLES.items():
        assert r["role"].strip() and len(r["role"]) <= 40, t
        assert len(r["story"]) > 80, f"{t} story is too thin"
        assert r["lesson"].strip(), t


def test_there_are_exactly_five_laws():
    assert len(MARKET_LAWS) == 5
    for law in MARKET_LAWS:
        assert law.strip()


def test_provenance_parses_as_a_date():
    dt.date.fromisoformat(ROLES_AS_OF)  # raises if malformed


# --------------------------------------------------------------------------- #
# The copy law — same bar as insights/flags/digest
# --------------------------------------------------------------------------- #
def test_role_copy_obeys_the_house_rules():
    for s in _all_role_strings():
        match = FORBIDDEN.search(s)
        assert match is None, f"advice-like phrasing in a role: {match.group(0)!r}"
        assert "median" not in s.lower(), "the word 'median' leaked into a role"
        assert "http" not in s.lower(), "a URL leaked into a role (breaks the email)"


# --------------------------------------------------------------------------- #
# The builder: degradation + population + adversarial inputs
# --------------------------------------------------------------------------- #
def test_builder_degrades_without_any_metrics():
    b = learn._build({}, {}, dt.date(2026, 8, 21))
    assert len(b.members) == len(WATCHLIST)
    assert all(not m.measurable for m in b.members)
    assert b.correlation == {"labels": [], "matrix": []}
    assert [m.ticker for m in b.members] == WATCHLIST  # order preserved
    # roles still attach even with no market data
    assert all(m.role for m in b.members)


def test_builder_populates_from_synthetic_inputs_and_keeps_order():
    rng = np.random.default_rng(0)
    tickers = ["AMZN", "VOO", "FE"]
    metrics = {t: _metrics(t) for t in tickers}
    closes = {
        t: _series(100 + np.cumsum(rng.normal(0.05, 1.0, 300))) for t in tickers
    }
    b = learn._build(metrics, closes, dt.date(2026, 8, 21))

    assert [m.ticker for m in b.members] == WATCHLIST
    by = {m.ticker: m for m in b.members}
    assert by["AMZN"].measurable and by["AMZN"].vol_90d == 25.0
    assert by["AMZN"].series_1y and len(by["AMZN"].series_1y) <= 60
    # a ticker with no synthetic data degrades, not crashes
    assert not by["NVDA"].measurable
    # correlation only spans the members we gave history for, plus is well-formed
    assert set(b.correlation["labels"]) == set(tickers)
    n = len(b.correlation["labels"])
    for i in range(n):
        assert b.correlation["matrix"][i][i] == pytest.approx(1.0)
        for j in range(n):
            assert abs(b.correlation["matrix"][i][j]) <= 1.0 + 1e-9
            assert b.correlation["matrix"][i][j] == pytest.approx(
                b.correlation["matrix"][j][i]
            )


def test_thin_history_member_is_excluded_from_correlation_with_a_note():
    """XE's real failure mode: too few sessions would collapse the shared window."""
    metrics = {"VOO": _metrics("VOO"), "XE": _metrics("XE", ret_1y=None)}
    closes = {
        "VOO": _series(100 + np.cumsum(np.ones(300) * 0.1)),
        "XE": _series(100 + np.cumsum(np.ones(80) * 0.1)),  # only 80 sessions
    }
    b = learn._build(metrics, closes, dt.date(2026, 8, 21))
    by = {m.ticker: m for m in b.members}
    assert not by["XE"].measurable
    assert "XE" not in b.correlation["labels"]
    assert "VOO" in b.correlation["labels"]
    assert "XE" in b.correlation_note


@pytest.mark.parametrize(
    "closes",
    [
        {},  # no series at all
        {"AMZN": _series(100 + np.cumsum(np.ones(260) * 0.1))},  # single member, no VOO
        {"AMZN": _series([np.nan] * 260)},  # all-NaN series
        {"AMZN": _series(np.ones(260) * 100.0)},  # constant prices → zero variance
        {"AMZN": _series(100 + np.cumsum(np.ones(10) * 0.1))},  # 10-session history
    ],
)
def test_builder_survives_adversarial_series(closes):
    metrics = {t: _metrics(t) for t in closes}
    b = learn._build(metrics, closes, dt.date(2026, 8, 21))
    assert len(b.members) == len(WATCHLIST)
    for m in b.members:
        if m.echo is not None:
            assert 0.0 <= m.echo.win_rate <= 1.0
    labels = b.correlation["labels"]
    n = len(labels)
    for i in range(n):
        for j in range(n):
            v = b.correlation["matrix"][i][j]
            # NaN correlations (constant series) are allowed to exist but must
            # never be a crash; a real number stays inside [-1, 1].
            if v == v:  # not NaN
                assert -1.0 - 1e-9 <= v <= 1.0 + 1e-9
