# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Shared pytest fixtures.

``db`` swaps the shared DuckDB connection for a throwaway in-memory one (schema
applied) so DB-touching tests never pollute the real cache file, and resets the
filers/analytics caches around each test.
"""

from __future__ import annotations

import threading

import duckdb
import pytest

from app import db as db_module


@pytest.fixture
def db():
    """An isolated in-memory DuckDB with the full schema, wired into app.db."""
    con = duckdb.connect(":memory:")
    con.execute(db_module._SCHEMA)
    saved = db_module._con
    db_module._con = con

    # Start every DB-touching test with a pristine connection lock. `db_lock`
    # reads the module global each call, so rebinding here is safe — and it
    # immunizes tests that run on worker threads (e.g. TestClient endpoints)
    # against any earlier test that left the RLock held by a since-dead thread.
    db_module._lock = threading.RLock()

    # Reset cross-request memoization so a fresh in-memory DB is never shadowed
    # by a cache generation computed against a different DB.
    from app.services import analytics, filers, learn

    def _reset() -> None:
        analytics._cache.update(key=None, metrics={}, latest=None, closes={}, stale={})
        filers._cache.update(key=None, by_params={})
        learn._basket_cache.update(key=None, value=None)
        try:
            from app.services import events

            events._events_cache.update(key=None, value=None)
        except (ImportError, AttributeError):
            pass  # events module lands in a later phase

    _reset()
    try:
        yield con
    finally:
        db_module._con = saved
        con.close()
        _reset()
