"""Unit tests for the trading calendar."""

from __future__ import annotations

import datetime as dt

from app.services.trading_calendar import (
    is_trading_day,
    most_recent_session,
    previous_trading_day,
    sessions_behind,
)


def test_weekend_is_not_trading():
    assert not is_trading_day(dt.date(2026, 8, 1))  # Saturday
    assert not is_trading_day(dt.date(2026, 8, 2))  # Sunday
    assert is_trading_day(dt.date(2026, 8, 3))  # Monday


def test_holiday_is_not_trading():
    assert not is_trading_day(dt.date(2026, 7, 3))  # Independence Day (observed)
    assert not is_trading_day(dt.date(2025, 12, 25))  # Christmas


def test_previous_trading_day_skips_weekend():
    # Monday's previous session is Friday.
    assert previous_trading_day(dt.date(2026, 8, 3)) == dt.date(2026, 7, 31)


def test_most_recent_session_on_weekend():
    assert most_recent_session(dt.date(2026, 8, 2)) == dt.date(2026, 7, 31)


def test_sessions_behind():
    today = dt.date(2026, 8, 3)  # Monday
    assert sessions_behind(dt.date(2026, 8, 3), today) == 0
    assert sessions_behind(dt.date(2026, 7, 31), today) == 1  # Friday: fresh
    assert sessions_behind(dt.date(2026, 7, 30), today) == 2
