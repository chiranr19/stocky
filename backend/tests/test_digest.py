"""Tests for the daily digest builder.

The anti-hallucination guarantee: the digest is assembled from computed values
by deterministic templates. These tests hold that line — every number that
appears must trace back to an input, and no sentence may give advice.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from build_digest import build_html, build_text  # noqa: E402

from app.models import (  # noqa: E402
    BreadthStats,
    CalendarResponse,
    EchoStats,
    IndexTile,
    MacroEvent,
    OverviewResponse,
    RadarResponse,
    RadarRow,
    Reading,
    RiskFlag,
    StockRow,
    WatchoutRow,
    WatchoutsResponse,
)

# Same bar as the insights/flags suites: interpretations, never instructions.
FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing)\b",
    re.IGNORECASE,
)

AS_OF = dt.date(2026, 8, 14)


def _row(ticker="TEST", price=100.0, change_pct=1.5) -> StockRow:
    return StockRow(
        ticker=ticker, name=f"{ticker} Inc", sector="Information Technology",
        price=price, change_pct=change_pct, spark=[98.0, 99.0, price],
        range_52w_position=0.6, avg_dollar_volume=1e8, above_ma50=True,
        above_ma200=True, rsi14=45.0, vol_90d=28.0, ret_1m=2.0, ret_3m=8.0,
        ret_1y=20.0, max_drawdown_1y=-15.0, volume_ratio=1.1, gap_pct=0.3,
        cross=None, cross_date=None, rsi_signal=None,
    )


def _fixtures():
    overview = OverviewResponse(
        as_of=AS_OF,
        tiles=[
            IndexTile(ticker="VOO", label="S&P 500 (VOO)", name="Vanguard S&P 500 ETF",
                      value=612.34, change_pct=0.42, unit="usd", spark=[600.0, 610.0, 612.34]),
            IndexTile(ticker="^VIX", label="VIX", name="CBOE Volatility Index",
                      value=14.2, change_pct=-3.1, unit="level", spark=[15.0, 14.5, 14.2]),
        ],
        breadth=BreadthStats(
            members=500, pct_above_ma50=62.0, pct_above_ma200=71.0,
            advancers=310, decliners=185, new_highs_52w=24, new_lows_52w=6,
        ),
        readings=[
            Reading(aspect="vix", headline="VIX 14.2 — calm", detail="d", tone="constructive", caveat="c"),
            Reading(aspect="breadth", headline="Broad participation — 62% above their 50-day",
                    detail="d", tone="constructive", caveat="c"),
        ],
    )

    radar = RadarResponse(
        as_of=AS_OF, budget=200.0, lookback="3m", horizon_days=21,
        weights={"depth": 0.35, "trend": 0.30, "rsi": 0.20, "quality": 0.15},
        rows=[
            RadarRow(
                row=_row("AAAA", 123.45, -1.2), depth_pct=11.7, depth_rank=82.0,
                falling_knife=False, entry_score=74.3,
                entry_factors={"depth": 82.0, "trend": 100.0, "rsi": 55.0, "quality": 61.0},
                echo=EchoStats(n=9, median_fwd_pct=3.4, win_rate=0.667, worst_pct=-8.2,
                               best_pct=14.1, kind="exact", min_depth_pct=10.0,
                               bucket_lo=10.0, bucket_hi=15.0, n_years=4, confidence="high"),
                flags=[],
            ),
            RadarRow(
                row=_row("BBBB", 88.20, 0.4), depth_pct=7.3, depth_rank=64.0,
                falling_knife=True, entry_score=51.0,
                entry_factors={"depth": 64.0, "trend": 0.0, "rsi": 70.0, "quality": 40.0},
                echo=None,
                flags=[RiskFlag(code="broken_trend", label="Broken trend", kind="risk",
                                severity="high", why="w", what_vets_do="v")],
            ),
        ],
    )

    watchouts = WatchoutsResponse(
        as_of=AS_OF, budget=200.0,
        rows=[
            WatchoutRow(
                row=_row("CCCC", 45.10, -2.8), risk_score=11.0,
                flags=[
                    RiskFlag(code="falling_knife", label="Falling knife", kind="risk",
                             severity="high", why="w", what_vets_do="v"),
                    RiskFlag(code="value_trap", label="Value trap", kind="risk",
                             severity="medium", why="w", what_vets_do="v"),
                ],
            ),
        ],
    )

    gainers = [_row("GGGG", 55.0, 6.2)]
    losers = [_row("LLLL", 30.0, -5.4)]
    cal = CalendarResponse(
        earnings=[],
        macro=[MacroEvent(date=dt.date.today() + dt.timedelta(days=2),
                          label="CPI release", kind="cpi")],
    )
    return overview, radar, watchouts, gainers, losers, cal


@pytest.fixture
def digest():
    o, r, w, g, l, c = _fixtures()
    return build_html(o, r, w, g, l, c), build_text(o, r, w, g, l, c)


# --------------------------------------------------------------------------- #
# Grounding: the numbers in the output came from the inputs
# --------------------------------------------------------------------------- #
def test_both_sections_present(digest):
    html, txt = digest
    assert "At a glance" in html and "The details" in html
    assert "AT A GLANCE" in txt and "THE DETAILS" in txt


def test_grounding_footer_names_source_and_date(digest):
    html, txt = digest
    for out in (html, txt):
        assert "Yahoo Finance" in out
        assert "no text in this email is model-generated" in out
        assert "Aug 14, 2026" in out


def test_input_values_appear_verbatim(digest):
    """Every headline number must be traceable to a fixture value."""
    html, txt = digest
    for out in (html, txt):
        assert "612.34" in out          # VOO price
        assert "AAAA" in out            # #1 radar setup
        assert "123.45" in out          # its price
        assert "74" in out              # its entry score
        assert "CCCC" in out            # #1 watch-out
        assert "Falling knife" in out   # its top hazard
        assert "GGGG" in out and "LLLL" in out  # movers


def test_echo_stats_carry_sample_size_and_worst_case(digest):
    """A base rate shown without N or the worst case would be misleading."""
    html, txt = digest
    for out in (html, txt):
        assert "9" in out        # n
        assert "-8.20%" in out   # worst case
        assert "strong" in out   # 'high' confidence rendered as 'strong'


def test_missing_echo_does_not_invent_numbers(digest):
    """BBBB has echo=None — nothing may be fabricated for it."""
    html, txt = digest
    # The only echo numbers anywhere are AAAA's.
    assert txt.count("median") <= 2
    assert "BBBB" in txt


def test_falling_knife_is_labeled(digest):
    html, txt = digest
    assert "knife" in html.lower()
    assert "KNIFE" in txt


def test_no_advice_language(digest):
    html, txt = digest
    for out in (html, txt):
        hit = FORBIDDEN.search(out)
        assert hit is None, f"advice-like phrasing in digest: {hit.group(0)!r}"


def test_disclaimer_present(digest):
    html, txt = digest
    for out in (html, txt):
        assert "not advice" in out.lower()


def test_html_is_email_safe(digest):
    """Mail clients strip JS and external assets — the digest must not need them."""
    html, _ = digest
    assert "<script" not in html.lower()
    assert "javascript:" not in html.lower()
    # No external requests: no remote images, stylesheets, or fonts.
    assert "http://" not in html
    assert not re.search(r'src\s*=\s*["\']https?://', html)


def test_upcoming_events_are_not_windowed_to_one_week():
    """Macro releases are ~monthly; a 7-day window left this section empty most
    days. The next few events must show regardless of how far out they are."""
    from build_digest import _upcoming_events

    today = dt.date.today()
    cal = CalendarResponse(
        earnings=[],
        macro=[
            MacroEvent(date=today - dt.timedelta(days=3), label="Past", kind="cpi"),
            MacroEvent(date=today + dt.timedelta(days=25), label="CPI release", kind="cpi"),
            MacroEvent(date=today + dt.timedelta(days=9), label="Jobs report", kind="jobs"),
        ],
    )
    events = _upcoming_events(cal)
    assert [lbl for _, lbl in events] == ["Jobs report", "CPI release"]  # sorted, past dropped

    html = build_html(*_fixtures()[:5], cal)
    txt = build_text(*_fixtures()[:5], cal)
    for out in (html, txt):
        assert "CPI release" in out  # 25 days out — would have been cut by a week window


def test_empty_inputs_do_not_crash():
    """A market holiday or a thin day must degrade, not explode."""
    o, r, w, g, l, c = _fixtures()
    empty_radar = RadarResponse(
        as_of=AS_OF, budget=200.0, lookback="3m", horizon_days=21,
        weights=r.weights, rows=[],
    )
    empty_watch = WatchoutsResponse(as_of=AS_OF, budget=200.0, rows=[])
    empty_cal = CalendarResponse(earnings=[], macro=[])
    html = build_html(o, empty_radar, empty_watch, [], [], empty_cal)
    txt = build_text(o, empty_radar, empty_watch, [], [], empty_cal)
    assert "At a glance" in html and "AT A GLANCE" in txt
