# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Tests for the living watchlist service — CRUD, seeding, and cache invalidation."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from app.config import WATCHLIST
from app.services import market, watchlist
from app.services.market import MarketDataError


def _frame(last_close: float = 100.0, n: int = 30) -> pd.DataFrame:
    idx = pd.bdate_range(end=dt.date.today(), periods=n)
    close = [last_close] * n
    return pd.DataFrame(
        {"open": close, "high": close, "low": close, "close": close,
         "adj_close": close, "volume": [1_000_000] * n},
        index=idx,
    )


@pytest.fixture
def patched_fetch(monkeypatch):
    """Make add() offline: a known synthetic frame, no yfinance."""
    def fake(ticker: str) -> pd.DataFrame:
        return _frame(last_close=42.5)

    monkeypatch.setattr(watchlist, "_fetch_history", fake)
    return fake


@pytest.fixture
def spy_invalidate(monkeypatch):
    calls = {"n": 0}
    from app.services import analytics

    monkeypatch.setattr(analytics, "invalidate_metrics_cache",
                        lambda: calls.__setitem__("n", calls["n"] + 1))
    return calls


# --------------------------------------------------------------------------- #
# Seeding
# --------------------------------------------------------------------------- #
def test_seed_is_idempotent_and_ordered(db):
    first = watchlist.tickers()
    second = watchlist.tickers()
    assert first == second
    # 16 curated seeds, in WATCHLIST order, then DVA appended.
    assert first == [*WATCHLIST, "DVA"]
    assert db.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0] == len(WATCHLIST) + 1


def test_seed_sources(db):
    watchlist.tickers()
    by = {e.ticker: e for e in watchlist.entries()}
    assert by["DVA"].source == "user"
    assert by[WATCHLIST[0]].source == "seed"
    assert all(e.active for e in by.values())


# --------------------------------------------------------------------------- #
# Add / remove / restore
# --------------------------------------------------------------------------- #
def test_add_records_price_and_appends(db, patched_fetch, spy_invalidate):
    entry = watchlist.add("ko")  # lower-case in
    assert entry.ticker == "KO"
    assert entry.source == "user"
    assert entry.added_price == 42.5
    # added_at is the last TRADING day in the fetched history, not calendar today.
    assert entry.added_at == _frame().index.max().date()
    assert "KO" in watchlist.tickers()
    assert watchlist.tickers()[-1] == "KO"  # appended last
    assert spy_invalidate["n"] == 1


def test_add_is_idempotent_for_active_ticker(db, patched_fetch, spy_invalidate):
    watchlist.add("KO")
    n_after_first = spy_invalidate["n"]
    again = watchlist.add("KO")
    assert again.ticker == "KO"
    assert watchlist.tickers().count("KO") == 1
    assert spy_invalidate["n"] == n_after_first  # no-op add doesn't invalidate


def test_add_rejects_malformed(db):
    for bad in ["", "NOT A TICKER", "TOOLONGSYMBOL", "a b"]:
        with pytest.raises(ValueError):
            watchlist.add(bad)


def test_add_bogus_symbol_raises_and_stores_nothing(db, monkeypatch):
    def boom(ticker: str):
        raise MarketDataError("no data")

    monkeypatch.setattr(watchlist, "_fetch_history", boom)
    with pytest.raises(MarketDataError):
        watchlist.add("ZZZZZZ")
    assert "ZZZZZZ" not in watchlist.tickers()


def test_remove_hides_and_restore_preserves_added_at(db, patched_fetch, spy_invalidate):
    added = watchlist.add("KO")
    original_added_at = added.added_at

    watchlist.remove("KO")
    assert "KO" not in watchlist.tickers()
    assert "KO" in [e.ticker for e in watchlist.hidden()]

    # Restore via add() — added_at must NOT reset to a flattering new date.
    restored = watchlist.add("KO")
    assert restored.added_at == original_added_at
    assert "KO" in watchlist.tickers()
    assert "KO" not in [e.ticker for e in watchlist.hidden()]


def test_remove_unknown_raises(db):
    with pytest.raises(ValueError):
        watchlist.remove("NOTHERE")


def test_can_remove_a_seeded_name(db):
    watchlist.tickers()
    watchlist.remove("META")
    assert "META" not in watchlist.tickers()
    assert "META" in [e.ticker for e in watchlist.hidden()]


# --------------------------------------------------------------------------- #
# Universe plumbing
# --------------------------------------------------------------------------- #
def test_all_tickers_reflects_additions(db, patched_fetch):
    watchlist.add("KO")
    assert "KO" in market.all_tickers()
    assert "KO" in market.priority_tickers()
    # Benchmark + macro still present independently of the watchlist.
    assert "VOO" in market.priority_tickers()
    assert "^VIX" in market.priority_tickers()


def test_priority_tickers_survives_voo_removal(db):
    watchlist.tickers()
    watchlist.remove("VOO")
    assert "VOO" not in watchlist.tickers()
    assert "VOO" in market.priority_tickers()  # appended as the benchmark regardless


# --------------------------------------------------------------------------- #
# Router (the app's first mutations)
# --------------------------------------------------------------------------- #
@pytest.fixture
def client(db, patched_fetch, monkeypatch):
    from fastapi.testclient import TestClient

    from app.main import app
    from app.services import market as market_mod

    # Never kick off the background universe warm-up during a test — it would
    # fetch the whole S&P from yfinance and can outlive the in-memory DB.
    monkeypatch.setattr(market_mod, "start_background_warm", lambda: None)
    return TestClient(app)


def test_router_add_remove_restore(client):
    # Add a new name → 201.
    r = client.post("/watchlist/KO")
    assert r.status_code == 201
    assert r.json()["ticker"] == "KO"

    # Idempotent re-add → 200.
    assert client.post("/watchlist/KO").status_code == 200

    # It shows up in the active list.
    listing = client.get("/watchlist").json()
    assert "KO" in [e["ticker"] for e in listing["entries"]]

    # Remove → 204, then it appears under hidden.
    assert client.delete("/watchlist/KO").status_code == 204
    listing = client.get("/watchlist").json()
    assert "KO" not in [e["ticker"] for e in listing["entries"]]
    assert "KO" in [e["ticker"] for e in listing["hidden"]]

    # Restore via POST → back in the active list.
    assert client.post("/watchlist/KO").status_code == 201
    assert "KO" in [e["ticker"] for e in client.get("/watchlist").json()["entries"]]


def test_router_rejects_bad_and_missing(client, monkeypatch):
    assert client.post("/watchlist/NOT A TICKER").status_code == 422

    def boom(ticker: str):
        raise MarketDataError("no data")

    monkeypatch.setattr(watchlist, "_fetch_history", boom)
    assert client.post("/watchlist/ZZZZZZ").status_code == 404
    assert client.delete("/watchlist/NEVERADDED").status_code == 404
