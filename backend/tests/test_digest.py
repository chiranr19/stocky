# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
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
    BasketMember,
    BasketResponse,
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
    WatchEvent,
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
                               bucket_lo=10.0, bucket_hi=15.0, n_years=4, confidence="high",
                               p25_pct=-1.1, p75_pct=6.8, n_benchmarked=9,
                               beat_benchmark=6, median_excess_pct=1.8),
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


def test_echo_shows_outcome_spread_and_voo_benchmark(digest):
    """Better math on the featured pick: quartile range, win count, and the
    same windows measured on VOO — a bounce means little if the index matched it."""
    html, txt = digest
    for out in (html, txt):
        assert "-1.10%" in out and "+6.80%" in out   # p25 / p75
        assert "6 of 9" in out                        # beat VOO count, win count
        assert "VOO" in out
        assert "+1.80%" in out                        # median edge over VOO


def test_sector_spread_lists_the_best_setup_per_sector():
    o, r, w, g, l, c = _fixtures()
    hc = RadarRow(
        row=StockRow(
            ticker="HHHH", name="HHHH Inc", sector="Health Care", price=77.0,
            change_pct=-0.5, spark=[80.0, 78.0, 77.0], range_52w_position=0.4,
            avg_dollar_volume=2e8, above_ma50=False, above_ma200=True, rsi14=38.0,
            vol_90d=22.0, ret_1m=-3.0, ret_3m=-6.0, ret_1y=12.0,
            max_drawdown_1y=-18.0, volume_ratio=1.0, gap_pct=0.0,
            cross=None, cross_date=None, rsi_signal=None,
        ),
        depth_pct=9.0, depth_rank=70.0, falling_knife=False, entry_score=66.0,
        entry_factors={"depth": 70.0, "trend": 100.0, "rsi": 60.0, "quality": 50.0},
        echo=None, flags=[],
    )
    sector_best = [r.rows[0], hc]
    html = build_html(o, r, w, g, l, c, sector_best=sector_best)
    txt = build_text(o, r, w, g, l, c, sector_best=sector_best)
    for out in (html, txt):
        assert "Across the sectors" in out
        assert "Information Technology" in out
        assert "Health Care" in out and "HHHH" in out


def test_flags_glossary_explains_every_label_shown(digest):
    """The legend must cover the flags actually used — and only those."""
    html, txt = digest
    for out in (html, txt):
        assert "Flags explained" in out or "FLAGS EXPLAINED" in out
        # BBBB carries broken_trend; CCCC carries falling_knife + value_trap.
        assert "most-watched line separating" in out       # broken_trend meaning
        assert "market verdict, not a discount" in out     # value_trap meaning
        assert "cheap has been getting cheaper" in out     # falling_knife meaning
        # golden_cross appears nowhere in the fixtures — no orphan legend rows.
        assert "Recent golden cross" not in out


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


# --------------------------------------------------------------------------- #
# v0.8 — metaphor analogies + the watchlist "cast" section
# --------------------------------------------------------------------------- #
def _basket(events=None) -> BasketResponse:
    def _member(ticker, group, role, **over):
        base = dict(
            ticker=ticker, name=f"{ticker} Inc", role=role, group=group,
            role_story="A short curated story.", role_lesson="The transferable law.",
            spark=[1.0, 2.0], series_1y=[1.0, 2.0], flag_codes=[], measurable=True,
        )
        base.update(over)
        return BasketMember(**base)

    members = [
        _member("AAAA", "mega", "The anchor tenant", price=123.45, change_pct=-1.2,
                vol_90d=30.0, ret_1y=15.0, above_ma200=True),
        _member("FE", "umbrella", "One of four umbrellas", price=45.0, change_pct=-2.5),
        _member("AEP", "umbrella", "One of four umbrellas", price=120.0, change_pct=-1.0),
        _member("DTE", "umbrella", "One of four umbrellas", price=135.0, change_pct=-0.8),
        _member("XE", "wildcard", "The lottery ticket", measurable=False),
    ]
    correlation = {
        "labels": ["FE", "AEP", "DTE"],
        "matrix": [[1.0, 0.73, 0.61], [0.73, 1.0, 0.88], [0.61, 0.88, 1.0]],
    }
    return BasketResponse(
        as_of=AS_OF, roles_as_of="2026-08-21",
        laws=["Ceiling and floor travel together.", "Always ask what VOO did."],
        members=members, correlation=correlation, correlation_note="",
        benchmark_ticker="VOO", events=events or [],
    )


def _events():
    return [
        WatchEvent(ticker="DTE", name="DTE Inc", code="ma200_break", tone="caution", severity=5,
                   headline="DTE crossed below its 200-day: its dip just became a verdict.",
                   detail="The long average gave way at 135.00."),
        WatchEvent(ticker="AAAA", name="AAAA Inc", code="big_move", tone="constructive", severity=2,
                   headline="AAAA moved +5.1% today.", detail="A move this size usually means news."),
    ]


def test_watchlist_events_render_since_yesterday_block():
    o, r, w, g, l, c = _fixtures()
    b = _basket(events=_events())
    html = build_html(o, r, w, g, l, c, basket=b)
    txt = build_text(o, r, w, g, l, c, basket=b)
    for out in (html, txt):
        assert "Since yesterday on your watchlist" in out
        assert "its dip just became a verdict" in out          # headline verbatim
        assert "The long average gave way at 135.00." in out   # detail verbatim


def test_events_block_absent_when_no_events():
    o, r, w, g, l, c = _fixtures()
    for b in (_basket(events=[]), None):
        html = build_html(o, r, w, g, l, c, basket=b)
        txt = build_text(o, r, w, g, l, c, basket=b)
        assert "Since yesterday on your watchlist" not in html
        assert "Since yesterday on your watchlist" not in txt


def test_events_block_is_capped_and_law_abiding():
    o, r, w, g, l, c = _fixtures()
    many = [
        WatchEvent(ticker=f"T{i}", name=f"T{i}", code="big_move", tone="neutral", severity=2,
                   headline=f"T{i} moved +4.0% today.", detail="A move this size usually means news.")
        for i in range(10)
    ]
    txt = build_text(o, r, w, g, l, c, basket=_basket(events=many))
    assert txt.count("moved +4.0% today") <= 6            # capped at 6 lines
    html = build_html(o, r, w, g, l, c, basket=_basket(events=many))
    assert FORBIDDEN.search(txt) is None and FORBIDDEN.search(html) is None
    assert txt.count("median") <= 2
    assert "http://" not in html


def test_reading_analogies_render_in_both_formats():
    o, r, w, g, l, c = _fixtures()
    o = o.model_copy(update={"readings": [
        Reading(aspect="vix", headline="VIX 14.2 — calm", detail="d", tone="constructive",
                caveat="cv", analogy="Umbrella insurance is cheapest on a sunny day."),
    ]})
    html = build_html(o, r, w, g, l, c)
    txt = build_text(o, r, w, g, l, c)
    for out in (html, txt):
        assert "Think of it like" in out
        assert "Umbrella insurance is cheapest on a sunny day." in out


def test_flags_legend_carries_analogies(digest):
    """Each explained flag now shows its everyday-life picture."""
    html, txt = digest
    for out in (html, txt):
        assert "Think of it like" in out
        # falling_knife is in play (CCCC) → its GLOSSARY analogy must appear.
        assert "kitchen knife slipping off the counter" in out


def test_watchlist_cast_lists_every_member_with_role():
    o, r, w, g, l, c = _fixtures()
    b = _basket()
    html = build_html(o, r, w, g, l, c, sector_best=None, basket=b)
    txt = build_text(o, r, w, g, l, c, sector_best=None, basket=b)
    for out in (html, txt):
        assert "the cast" in out
        for m in b.members:
            assert m.ticker in out
            assert m.role in out
        # The unmeasurable member is labeled, not invented.
        assert "too little history to measure" in out


def test_watchlist_correlation_callout_traces_to_input():
    o, r, w, g, l, c = _fixtures()
    b = _basket()  # umbrella off-diagonals: 0.61, 0.73, 0.88 → min-max 0.61-0.88
    for out in (build_html(o, r, w, g, l, c, basket=b), build_text(o, r, w, g, l, c, basket=b)):
        assert "0.61-0.88" in out


def test_law_of_the_day_is_deterministic_for_the_date():
    o, r, w, g, l, c = _fixtures()
    b = _basket()
    expected = b.laws[AS_OF.toordinal() % len(b.laws)]
    for out in (build_html(o, r, w, g, l, c, basket=b), build_text(o, r, w, g, l, c, basket=b)):
        assert expected in out


def test_cast_section_adds_no_new_median_language():
    """Belt-and-braces: the 'median' budget survives with a basket attached."""
    o, r, w, g, l, c = _fixtures()
    txt = build_text(o, r, w, g, l, c, basket=_basket())
    assert txt.count("median") <= 2


def test_digest_with_basket_stays_advice_free_and_email_safe():
    o, r, w, g, l, c = _fixtures()
    b = _basket()
    html = build_html(o, r, w, g, l, c, basket=b)
    txt = build_text(o, r, w, g, l, c, basket=b)
    for out in (html, txt):
        assert FORBIDDEN.search(out) is None
    assert "<script" not in html.lower()
    assert "http://" not in html


def test_basket_none_skips_the_cast_section():
    o, r, w, g, l, c = _fixtures()
    txt = build_text(o, r, w, g, l, c, basket=None)
    assert "the cast" not in txt
