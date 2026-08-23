# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Tests for Followed Filers — parsing, the integrity pipeline, the math, the law.

Zero network: every test drives real fixture files or synthetic data. The bars
this suite holds:
  * a hostile filing can't parse into an exploit (XXE forbidden) and can't crash
    the ingest (malformed → raises, caller quarantines);
  * every enriched number traces to the price cache;
  * base rates never hide a thin sample;
  * dollar *ranges* never collapse into a fake-precise point;
  * no surface gives advice (same law as insights/flags/digest);
  * model fields survive the round-trip (the v0.5 silent-drop lesson).
"""

from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from defusedxml.common import EntitiesForbidden

from app.models import DisclosedTrade, FilerBaseRate, FilerNotice, FilersResponse
from app.services import filers
from app.services.filers import ParsedTx

FIX = Path(__file__).parent / "fixtures"

# Same forbidden-phrasing law as the insights / flags / digest suites.
FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing)\b",
    re.IGNORECASE,
)


def _xml(name: str) -> bytes:
    return (FIX / name).read_bytes()


def _series(start: str, values: list[float]) -> pd.Series:
    idx = pd.bdate_range(start=start, periods=len(values))
    return pd.Series(values, index=idx, dtype=float)


# --------------------------------------------------------------------------- #
# Parsing — real + synthetic + hostile
# --------------------------------------------------------------------------- #
def test_parses_a_real_form4():
    ticker, txs = filers.parse_form4(_xml("form4_real_exercise.xml"))
    assert ticker == "TSLA"
    assert txs and all(t.filer == "Musk Elon" for t in txs)
    assert "Director" in txs[0].filer_role and "CEO" in txs[0].filer_role


def test_parses_a_clean_open_market_buy():
    ticker, txs = filers.parse_form4(_xml("form4_buy.xml"))
    assert ticker == "EXMP"
    buy = [t for t in txs if t.action == "buy"][0]
    assert buy.filer == "Doe Jane"
    assert "CFO" in buy.filer_role
    assert buy.shares == 1000.0 and buy.price == 50.25
    assert buy.asset_class == "equity" and buy.scheduled is False


def test_detects_10b5_1_scheduled_plan_from_footnote():
    _, txs = filers.parse_form4(_xml("form4_scheduled_sale.xml"))
    sell = [t for t in txs if t.action == "sell"][0]
    assert sell.scheduled is True  # footnote names the Rule 10b5-1 plan


def test_tranches_aggregate_to_a_weighted_average():
    # One purchase filled in three tranches at different prices must combine into
    # a single honest total, not collapse to one arbitrary line.
    txs = [
        _tx(shares=100.0, price=10.0),
        _tx(shares=300.0, price=12.0),
        _tx(shares=100.0, price=20.0),
    ]
    out = filers.aggregate_txs(txs)
    assert len(out) == 1
    assert out[0].shares == 500.0
    # weighted avg = (100*10 + 300*12 + 100*20) / 500 = 6600/500 = 13.2
    assert out[0].price == pytest.approx(13.2, abs=0.001)


def test_aggregate_keeps_different_actions_separate():
    txs = [_tx(action="buy", shares=100.0), _tx(action="sell", shares=50.0)]
    out = filers.aggregate_txs(txs)
    assert len(out) == 2
    assert {t.action for t in out} == {"buy", "sell"}


def test_malformed_xml_raises_not_crashes():
    with pytest.raises(Exception):
        filers.parse_form4(_xml("form4_malformed.xml"))


def test_xxe_entity_is_forbidden():
    """A filing with an external entity must never resolve it (no file reads)."""
    with pytest.raises(EntitiesForbidden):
        filers.parse_form4(_xml("form4_xxe.xml"))


def test_injection_names_are_carried_as_inert_text():
    _, txs = filers.parse_form4(_xml("form4_injection.xml"))
    name = txs[0].filer
    # The parser preserves the literal text; the point is it's data, not markup —
    # an HTML surface must escape it. Prove escaping renders it inert.
    from html import escape

    assert "<script>" in name  # decoded entity is literal text, not a tag node
    assert "<script>" not in escape(name)
    assert "&lt;script&gt;" in escape(name)


# --------------------------------------------------------------------------- #
# Integrity pipeline
# --------------------------------------------------------------------------- #
def _tx(**over) -> ParsedTx:
    base = dict(
        ticker="EXMP", filer="Doe Jane", filer_role="CFO", asset_class="equity",
        action="buy", trade_date=dt.date(2025, 3, 10), shares=100.0, price=50.0,
        scheduled=False,
    )
    base.update(over)
    return ParsedTx(**base)


def test_temporal_gate_rejects_filed_before_traded(db):
    tx = _tx(price=None)  # price None skips the DB band check
    bad = filers._validated_row(
        tx, "ACC-1", filed_date=dt.date(2025, 3, 1),  # before the trade
        url="u", today=dt.date(2025, 4, 1),
    )
    assert bad is None


def test_temporal_gate_rejects_future_filing(db):
    tx = _tx(price=None)
    bad = filers._validated_row(
        tx, "ACC-1", filed_date=dt.date(2025, 5, 1),
        url="u", today=dt.date(2025, 4, 1),  # filed in the "future"
    )
    assert bad is None


def test_good_row_passes_and_computes_value(db):
    tx = _tx(price=None, shares=None, action="grant")  # no band check
    row = filers._validated_row(
        tx, "ACC-2", filed_date=dt.date(2025, 3, 12),
        url="http://sec.gov/x", today=dt.date(2025, 4, 1),
    )
    assert row is not None
    assert row["filed_date"] == dt.date(2025, 3, 12)
    assert row["value_lo"] == row["value_hi"]  # a point, but still a [lo, hi]


def test_price_band_quarantines_a_parse_slip(db):
    # Our own bar says EXMP traded ~50 that day; a filing claiming $5000 is a
    # decimal/units slip and must be quarantined, not trusted.
    db.execute(
        "INSERT INTO prices VALUES ('EXMP', DATE '2025-03-10', 49, 51, 48, 50, 50, 1000)"
    )
    good = filers._validated_row(
        _tx(price=50.5), "ACC-3", dt.date(2025, 3, 11), "u", dt.date(2025, 4, 1)
    )
    assert good is not None  # within ±20% band
    slip = filers._validated_row(
        _tx(price=5000.0), "ACC-4", dt.date(2025, 3, 11), "u", dt.date(2025, 4, 1)
    )
    assert slip is None
    q = db.execute(
        "SELECT COUNT(*) FROM ingest_log WHERE kind = 'suspect_value'"
    ).fetchone()[0]
    assert q == 1


def test_exercise_price_is_not_band_checked(db):
    # An option exercise prices at the strike, far from market — gating it would
    # wrongly delete a real filing. Only P/S are cross-validated.
    db.execute(
        "INSERT INTO prices VALUES ('EXMP', DATE '2025-03-10', 400, 410, 395, 405, 405, 1000)"
    )
    row = filers._validated_row(
        _tx(action="other", price=23.34), "ACC-5", dt.date(2025, 3, 11), "u", dt.date(2025, 4, 1)
    )
    assert row is not None  # strike price accepted, not quarantined


def test_store_is_idempotent(db):
    rows = [filers._validated_row(_tx(price=None), "ACC-9", dt.date(2025, 3, 12), "u", dt.date(2025, 4, 1))]
    filers._store_rows(rows)
    filers._store_rows(rows)  # same natural key → replace, not duplicate
    n = db.execute("SELECT COUNT(*) FROM disclosed_trades").fetchone()[0]
    assert n == 1


# --------------------------------------------------------------------------- #
# Enrichment — every number from the price cache
# --------------------------------------------------------------------------- #
def test_enrichment_lag_tax_and_since_windows():
    # A stock that ran up between the trade and the disclosure: the lag tax is
    # the built-in cost of only learning about it late.
    adj = _series("2025-01-01", [100.0] * 5 + [110.0] * 5 + [121.0] * 5)
    trade = dict(
        source="edgar", filing_id="F1", filer="Doe Jane", filer_role="CFO",
        ticker="EXMP", asset_class="equity", action="buy",
        trade_date=dt.date(2025, 1, 1), filed_date=dt.date(2025, 1, 9),
        shares=10.0, price=100.0, value_lo=1000.0, value_hi=1000.0,
        scheduled=False, url="u",
    )
    voo = _series("2025-01-01", [400.0] * 15)
    out = filers._enrich(trade, {"EXMP": adj}, voo)
    assert out.priceable is True
    # bought at 100, disclosed at 110, latest 121
    assert out.since_trade_pct == pytest.approx(21.0, abs=0.01)
    assert out.since_filed_pct == pytest.approx(10.0, abs=0.01)
    assert out.lag_tax_pct == pytest.approx(10.0, abs=0.01)   # 100 → 110 during the lag
    assert out.voo_since_filed_pct == pytest.approx(0.0, abs=0.01)  # VOO flat
    assert out.lag_days == 8


def test_non_equity_is_not_priceable():
    trade = dict(
        source="edgar", filing_id="F2", filer="X", filer_role="", ticker="EXMP",
        asset_class="option", action="other", trade_date=dt.date(2025, 1, 1),
        filed_date=dt.date(2025, 1, 3), shares=1.0, price=0.0, value_lo=0.0,
        value_hi=0.0, scheduled=False, url="u",
    )
    out = filers._enrich(trade, {"EXMP": _series("2025-01-01", [1.0] * 10)}, None)
    assert out.priceable is False
    assert out.since_filed_pct is None


# --------------------------------------------------------------------------- #
# Base rates — pooled, honest about sample size
# --------------------------------------------------------------------------- #
def _buy(ticker: str, filed: dt.date) -> dict:
    return dict(
        source="edgar", filing_id=f"{ticker}-{filed}", filer="Star Filer",
        filer_role="CEO", ticker=ticker, asset_class="equity", action="buy",
        trade_date=filed - dt.timedelta(days=30), filed_date=filed,
        shares=1.0, price=1.0, value_lo=1.0, value_hi=1.0, scheduled=False, url="u",
    )


def test_base_rate_pools_across_tickers_and_labels_thin_sample():
    # One filer, four buys → meets the min-episodes floor but stays low-confidence
    # (single year, small N). The number must never pretend to be strong.
    up = _series("2024-01-01", list(np.linspace(100, 200, 200)))  # steady climb
    series = {"AAA": up, "BBB": up.copy()}
    trades = [
        _buy("AAA", dt.date(2024, 2, 1)),
        _buy("AAA", dt.date(2024, 3, 1)),
        _buy("BBB", dt.date(2024, 4, 1)),
        _buy("BBB", dt.date(2024, 5, 1)),
    ]
    voo = _series("2024-01-01", [400.0] * 200)
    rates = filers.filer_base_rates(trades, series, voo)
    one_month = [r for r in rates if r.window_days == 21]
    assert one_month, "expected a 1-month base rate"
    r = one_month[0]
    assert r.n == 4
    assert r.confidence == "low"          # thin sample, single year
    assert r.median_fwd_pct > 0           # a rising series → positive forward
    assert r.median_lag_days == 30
    assert r.beat_benchmark >= 0 and r.n_benchmarked == r.n


def test_base_rate_suppressed_below_min_episodes():
    up = _series("2024-01-01", list(np.linspace(100, 120, 100)))
    trades = [_buy("AAA", dt.date(2024, 2, 1)), _buy("AAA", dt.date(2024, 2, 15))]
    rates = filers.filer_base_rates(trades, {"AAA": up}, None)
    assert rates == []  # 2 < FILER_MIN_EPISODES → say nothing rather than mislead


# --------------------------------------------------------------------------- #
# Range arithmetic — a disclosed range must never collapse to a point
# --------------------------------------------------------------------------- #
def test_value_range_sum_stays_a_range():
    trades = [
        {"value_lo": 1000.0, "value_hi": 15000.0},
        {"value_lo": 15000.0, "value_hi": 50000.0},
    ]
    lo, hi = filers.sum_value_range(trades)
    assert lo == 16000.0 and hi == 65000.0
    assert lo != hi  # the whole point: honest uncertainty, not a fake total


# --------------------------------------------------------------------------- #
# Notices — signal hygiene + the no-advice law
# --------------------------------------------------------------------------- #
def test_cluster_buying_needs_two_distinct_filers():
    trades = [
        dict(action="buy", scheduled=False, ticker="DJT", filer="Insider A",
             trade_date=dt.date(2025, 5, 1)),
        dict(action="buy", scheduled=False, ticker="DJT", filer="Insider B",
             trade_date=dt.date(2025, 5, 5)),
    ]
    notices = filers.build_notices(trades)
    clusters = [n for n in notices if n.code == "cluster_buying"]
    assert len(clusters) == 1
    assert set(clusters[0].filers) == {"Insider A", "Insider B"}


def test_cluster_ignores_a_single_filer_buying_twice():
    trades = [
        dict(action="buy", scheduled=False, ticker="DJT", filer="Solo",
             trade_date=dt.date(2025, 5, 1)),
        dict(action="buy", scheduled=False, ticker="DJT", filer="Solo",
             trade_date=dt.date(2025, 5, 4)),
    ]
    assert not [n for n in filers.build_notices(trades) if n.code == "cluster_buying"]


def test_scheduled_sale_notice_for_a_famous_owner():
    trades = [
        dict(action="sell", scheduled=True, ticker="NVDA", filer="Huang Jen-Hsun",
             trade_date=dt.date(2025, 6, 2)),
    ]
    notices = filers.build_notices(trades)
    sched = [n for n in notices if n.code == "scheduled_sale"]
    assert len(sched) == 1
    assert "10b5-1" in sched[0].detail


def test_no_advice_language_anywhere():
    trades = [
        dict(action="buy", scheduled=False, ticker="DJT", filer="A", trade_date=dt.date(2025, 5, 1)),
        dict(action="buy", scheduled=False, ticker="DJT", filer="B", trade_date=dt.date(2025, 5, 3)),
        dict(action="sell", scheduled=True, ticker="NVDA", filer="Huang Jen-Hsun", trade_date=dt.date(2025, 6, 2)),
    ]
    blobs = [filers._HONESTY_NOTE]
    for n in filers.build_notices(trades):
        blobs.append(f"{n.headline} {n.detail} {n.caveat}")
    for b in blobs:
        m = FORBIDDEN.search(b)
        assert m is None, f"advice-like phrasing: {m.group(0)!r}"


def test_every_notice_has_a_caveat():
    trades = [
        dict(action="buy", scheduled=False, ticker="DJT", filer="A", trade_date=dt.date(2025, 5, 1)),
        dict(action="buy", scheduled=False, ticker="DJT", filer="B", trade_date=dt.date(2025, 5, 3)),
    ]
    for n in filers.build_notices(trades):
        assert n.caveat.strip()
        assert n.tone in ("constructive", "caution", "neutral")


# --------------------------------------------------------------------------- #
# Model pass-through — nothing silently dropped (the v0.5 lesson)
# --------------------------------------------------------------------------- #
def test_base_rate_model_round_trips_every_field():
    r = FilerBaseRate(
        filer="X", window_days=21, n=13, median_fwd_pct=3.1, win_rate=0.62,
        worst_pct=-9.0, best_pct=18.0, p25_pct=-1.0, p75_pct=7.5, n_years=3,
        confidence="high", n_benchmarked=13, beat_benchmark=8,
        median_excess_pct=1.2, median_lag_days=34,
    )
    back = FilerBaseRate(**r.model_dump())
    assert back == r
    assert back.median_excess_pct == 1.2 and back.median_lag_days == 34


def test_disclosed_trade_round_trips():
    t = DisclosedTrade(
        source="edgar", filing_id="F", filer="X", filer_role="CEO", ticker="AAA",
        name="Alpha", asset_class="equity", action="buy", trade_date=dt.date(2025, 1, 1),
        filed_date=dt.date(2025, 1, 3), lag_days=2, shares=1.0, price=1.0,
        value_lo=1.0, value_hi=1.0, scheduled=False, url="u", priceable=True,
        since_trade_pct=5.0, since_filed_pct=3.0, lag_tax_pct=2.0, voo_since_filed_pct=1.0,
    )
    assert DisclosedTrade(**t.model_dump()) == t


# --------------------------------------------------------------------------- #
# Build orchestration — amendments, emptiness
# --------------------------------------------------------------------------- #
def test_empty_db_does_not_crash(db):
    resp = filers.build_filers("all", 60)
    assert isinstance(resp, FilersResponse)
    assert resp.trades == [] and resp.base_rates == [] and resp.filings_through is None
    assert resp.note  # the honesty note is always present


def test_amendment_supersedes_the_original(db):
    # Same economic event filed twice (a 4 then a 4/A). The view keeps the later
    # filing, not both.
    common = dict(
        filer="Doe Jane", filer_role="CFO", ticker="EXMP", asset_class="equity",
        action="buy", trade_date=dt.date(2025, 3, 10), shares=1000.0, price=50.0,
        value_lo=50000.0, value_hi=50000.0, scheduled=False,
    )
    filers._store_rows([
        dict(source="edgar", filing_id="ORIG", filed_date=dt.date(2025, 3, 12),
             url="orig", **common),
        dict(source="edgar", filing_id="AMEND", filed_date=dt.date(2025, 3, 20),
             url="amend", **common),
    ])
    resp = filers.build_filers("all", 60)
    exmp = [t for t in resp.trades if t.ticker == "EXMP"]
    assert len(exmp) == 1
    assert exmp[0].filed_date == dt.date(2025, 3, 20)  # the amendment won
    assert exmp[0].url == "amend"
