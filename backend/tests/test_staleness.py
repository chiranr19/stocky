# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Stopped feeds: a ticker whose last bar trails the universe must not be ranked.

Reproduces the WBD case seen 2026-11-01: its last bar was a junk 2026-10-05 print
(open 0, volume 40) while the rest of the universe ran to 2026-10-30, yet it
ranked #1 in its sector, fired a "+10.8% today" event, and could be added to the
watchlist. Every test builds real price rows in the in-memory DuckDB — no mocks;
ingest_meta rows mark the windows as freshly fetched so nothing hits yfinance.
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.services import analytics, cone, events, learn, market, radar, watchlist
from app.services.market import MarketDataError, StaleDataError
from app.services.screener import is_stale

UNIVERSE_END = dt.date(2026, 10, 30)  # Friday — the universe's newest session
WBD_END = dt.date(2026, 10, 5)  # 19 trading sessions behind it
FRESH = ["CMCSA", "T", "VZ", "VOO"]  # three Communication Services peers + benchmark

FORBIDDEN = re.compile(
    r"\b(you should|we recommend|recommended|buy it|sell it|must buy|must sell|"
    r"guaranteed|will rise|will fall|sure thing|dump it|avoid buying)\b",
    re.IGNORECASE,
)


def _bars(end: dt.date, seed: int, n: int = 300, jump: float = 0.0,
          junk_last: bool = False) -> pd.DataFrame:
    """A deterministic ~$30 random walk ending on ``end``. ``jump`` sets the last
    day's move; ``junk_last`` makes the last bar a placeholder print like WBD's."""
    rng = np.random.default_rng(seed)
    close = 30.0 * np.cumprod(1.0 + rng.normal(0.0005, 0.01, n))
    close[-1] = close[-2] * (1.0 + jump)
    volume = np.full(n, 1_000_000)
    open_ = close.copy()
    if junk_last:
        open_[-1], volume[-1] = 0.0, 40
    return pd.DataFrame(
        {"open": open_, "high": close * 1.002, "low": close * 0.998,
         "close": close, "adj_close": close, "volume": volume},
        index=pd.bdate_range(end=end, periods=n),
    )


def _store(con, ticker: str, df: pd.DataFrame) -> None:
    """Insert the bars and mark the window freshly fetched (get_history won't fetch)."""
    rows = df.reset_index(names="date").assign(ticker=ticker)
    rows["date"] = rows["date"].dt.date
    con.register("incoming", rows)
    con.execute(
        "INSERT INTO prices (ticker, date, open, high, low, close, adj_close, volume) "
        "SELECT ticker, date, open, high, low, close, adj_close, volume FROM incoming"
    )
    con.unregister("incoming")
    con.execute(
        "INSERT INTO ingest_meta VALUES (?, ?, ?, ?)",
        [ticker, dt.date(2000, 1, 1), dt.date(2100, 1, 1), market._utcnow()],
    )


def _wbd(end: dt.date) -> pd.DataFrame:
    # Same values either way; only the end date differs — the control proves the
    # date alone is what removes it.
    return _bars(end, seed=7, jump=0.108, junk_last=True)


@pytest.fixture
def universe(db):
    """Fresh peers to UNIVERSE_END; returns a callable that stores WBD to a date."""
    for i, t in enumerate(FRESH):
        _store(db, t, _bars(UNIVERSE_END, seed=i))

    def add_wbd(end: dt.date) -> None:
        _store(db, "WBD", _wbd(end))
        # New generation → every derived cache (screen, radar, watchouts) misses.
        analytics.invalidate_metrics_cache()

    return add_wbd


def _all_ranked_tickers(budget: float = 200.0) -> dict[str, set[str]]:
    sectors = analytics.build_sectors(budget)
    signals = analytics.build_signals(budget)
    return {
        "sectors": {r.ticker for p in sectors.sectors for r in p.top},
        **{
            f"movers:{kind}": {r.ticker for r in analytics.build_movers(kind, budget, 100)}
            for kind in ("gainers", "losers", "volume", "highs", "lows", "gaps")
        },
        "signals": {
            r.ticker
            for rows in (signals.golden_crosses, signals.death_crosses,
                         signals.overbought, signals.oversold)
            for r in rows
        },
        "watchouts": {r.row.ticker for r in analytics.build_watchouts(budget, 100).rows},
        "radar": {
            r.row.ticker
            for lb in ("1m", "2m", "3m")
            for r in radar.build_radar(budget, lb, 100).rows
        },
        "riskmap": {p.ticker for p in analytics.build_riskmap(budget).points},
    }


# --------------------------------------------------------------------------- #
# The rule itself (pure)
# --------------------------------------------------------------------------- #
def test_is_stale_counts_trading_sessions_not_calendar_days():
    assert not is_stale(UNIVERSE_END, UNIVERSE_END)
    assert not is_stale(dt.date(2026, 10, 23), UNIVERSE_END)  # 5 sessions: still fresh
    assert is_stale(dt.date(2026, 10, 22), UNIVERSE_END)  # 6 sessions: stale
    # A weekend between them is zero sessions, not two days.
    assert not is_stale(UNIVERSE_END, dt.date(2026, 11, 2))
    assert is_stale(WBD_END, UNIVERSE_END)
    assert not is_stale(WBD_END, UNIVERSE_END, max_sessions=19)
    assert is_stale(WBD_END, UNIVERSE_END, max_sessions=18)


# --------------------------------------------------------------------------- #
# Screens and scans
# --------------------------------------------------------------------------- #
def test_control_a_fresh_wbd_does_rank(universe):
    universe(UNIVERSE_END)
    ranked = _all_ranked_tickers()
    assert "WBD" in ranked["sectors"]
    assert analytics.build_movers("gainers", 200.0, 5)[0].ticker == "WBD"
    assert analytics.stale_tickers() == {}


def test_stale_ticker_is_held_out_of_the_metrics_cache(universe):
    universe(WBD_END)
    metrics, latest = analytics.universe_metrics()
    assert latest == UNIVERSE_END
    assert "WBD" not in metrics and "WBD" not in analytics.universe_closes()
    assert set(FRESH) <= set(metrics)
    assert analytics.stale_tickers() == {"WBD": WBD_END}


def test_stale_ticker_is_excluded_from_every_ranking(universe):
    universe(WBD_END)
    for view, tickers in _all_ranked_tickers().items():
        assert "WBD" not in tickers, view
    # The fresh peers still rank — exclusion is targeted, not a blanket wipe.
    assert {"CMCSA", "T", "VZ"} <= _all_ranked_tickers()["sectors"]


# --------------------------------------------------------------------------- #
# What-changed events + the basket
# --------------------------------------------------------------------------- #
def test_control_a_fresh_wbd_fires_its_big_move(universe):
    universe(UNIVERSE_END)
    evs = events.build_events(["CMCSA", "WBD"], as_of=UNIVERSE_END)
    assert any(e.ticker == "WBD" and e.code == "big_move" for e in evs)


def test_stale_ticker_emits_no_events(universe):
    universe(WBD_END)
    assert not [e for e in events.build_events(["CMCSA", "WBD"], as_of=UNIVERSE_END)
                if e.ticker == "WBD"]
    # Without as_of the newest frame is the reference — still caught.
    assert not [e for e in events.build_events(["CMCSA", "WBD"]) if e.ticker == "WBD"]


def test_stale_watchlist_member_reads_as_a_stopped_clock(universe, db):
    universe(WBD_END)
    watchlist.tickers()  # seed, then slip WBD in as if added before the guard
    db.execute(
        "INSERT INTO watchlist VALUES ('WBD', ?, 30.95, 'user', TRUE, 99)", [WBD_END]
    )
    basket = learn.build_basket()
    wbd = next(m for m in basket.members if m.ticker == "WBD")
    assert wbd.data_ends == WBD_END
    assert wbd.role == "The stopped clock"
    assert "2026-10-05" in wbd.role_story
    assert not wbd.measurable and wbd.price is None and wbd.flag_codes == []
    assert all(e.ticker != "WBD" for e in basket.events)
    blob = f"{wbd.role} {wbd.role_story} {wbd.role_lesson}"
    assert FORBIDDEN.search(blob) is None and "median" not in blob.lower()
    # Survives the API model round-trip (the v0.5 silent-drop lesson).
    assert wbd.model_dump()["data_ends"] == WBD_END


# --------------------------------------------------------------------------- #
# /stock stays viewable with a note; the cone declines
# --------------------------------------------------------------------------- #
def test_stock_detail_keeps_a_stale_ticker_visible_with_a_data_ends_note(universe):
    universe(WBD_END)
    detail = analytics.build_stock_detail("WBD")
    assert detail.candles[-1].date == WBD_END  # still shown
    assert detail.data_ends == WBD_END
    assert detail.data_note.startswith("Data ends 2026-10-05.")
    assert "19 trading sessions" in detail.data_note
    assert FORBIDDEN.search(detail.data_note) is None
    assert "median" not in detail.data_note.lower()
    assert detail.row.score is None  # no Stocky score off a frozen bar
    assert detail.entry is None

    fresh = analytics.build_stock_detail("CMCSA")
    assert fresh.data_ends is None and fresh.data_note is None


def test_cone_declines_a_stale_ticker_with_its_date(universe):
    universe(WBD_END)
    with pytest.raises(ValueError, match="2026-10-05"):
        cone.build_cone("WBD", 126)


# --------------------------------------------------------------------------- #
# Watchlist add()
# --------------------------------------------------------------------------- #
def test_add_refuses_a_stale_ticker_naming_its_last_date(universe):
    universe(WBD_END)  # add()'s history fetch reads these rows back from DuckDB
    with pytest.raises(StaleDataError, match="ends 2026-10-05") as exc:
        watchlist.add("WBD")
    assert isinstance(exc.value, MarketDataError)  # the router's 404 family
    assert "19 trading sessions" in str(exc.value)
    assert "WBD" not in watchlist.tickers()
    assert "WBD" not in [e.ticker for e in watchlist.hidden()]


def test_restoring_a_hidden_stale_ticker_is_refused_too(universe, db):
    universe(WBD_END)
    watchlist.tickers()
    db.execute(
        "INSERT INTO watchlist VALUES ('WBD', ?, 28.0, 'user', FALSE, 99)",
        [dt.date(2026, 9, 1)],
    )
    with pytest.raises(StaleDataError):
        watchlist.add("WBD")
    assert "WBD" in [e.ticker for e in watchlist.hidden()]


def test_add_accepts_a_fresh_ticker(universe):
    universe(UNIVERSE_END)
    entry = watchlist.add("WBD")
    assert entry.active and entry.added_at == UNIVERSE_END


def test_router_maps_a_stale_add_to_404_with_the_date(universe, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app

    monkeypatch.setattr(market, "start_background_warm", lambda: None)
    universe(WBD_END)
    r = TestClient(app).post("/watchlist/WBD")
    assert r.status_code == 404
    assert "2026-10-05" in r.json()["detail"]


# --------------------------------------------------------------------------- #
# scripts/audit_data.py junk-bar check
# --------------------------------------------------------------------------- #
def test_audit_flags_junk_bars_but_not_index_volume(db):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import audit_data

    _store(db, "WBD", _wbd(WBD_END))  # one junk bar: open 0, volume 40
    _store(db, "CMCSA", _bars(UNIVERSE_END, seed=1))  # clean
    vix = _bars(UNIVERSE_END, seed=2, n=5).assign(volume=0)  # indices carry no volume
    _store(db, "^VIX", vix)

    assert audit_data.junk_bars(db) == [("WBD", 1, WBD_END)]
