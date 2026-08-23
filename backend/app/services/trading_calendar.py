# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Minimal US (NYSE) trading calendar for data-freshness checks.

Pure and dependency-free so it unit-tests cleanly. Holiday list is static and
covers the range this app cares about — refresh it yearly.
"""

from __future__ import annotations

import datetime as dt

# NYSE full-day closures (regular sessions only; half-days still trade).
US_MARKET_HOLIDAYS: set[dt.date] = {
    # 2025
    dt.date(2025, 1, 1), dt.date(2025, 1, 20), dt.date(2025, 2, 17),
    dt.date(2025, 4, 18), dt.date(2025, 5, 26), dt.date(2025, 6, 19),
    dt.date(2025, 7, 4), dt.date(2025, 9, 1), dt.date(2025, 11, 27),
    dt.date(2025, 12, 25),
    # 2026
    dt.date(2026, 1, 1), dt.date(2026, 1, 19), dt.date(2026, 2, 16),
    dt.date(2026, 4, 3), dt.date(2026, 5, 25), dt.date(2026, 6, 19),
    dt.date(2026, 7, 3), dt.date(2026, 9, 7), dt.date(2026, 11, 26),
    dt.date(2026, 12, 25),
    # 2027 (early, for the year boundary)
    dt.date(2027, 1, 1), dt.date(2027, 1, 18), dt.date(2027, 2, 15),
}


def is_trading_day(d: dt.date) -> bool:
    return d.weekday() < 5 and d not in US_MARKET_HOLIDAYS


def previous_trading_day(d: dt.date) -> dt.date:
    cur = d - dt.timedelta(days=1)
    while not is_trading_day(cur):
        cur -= dt.timedelta(days=1)
    return cur


def most_recent_session(today: dt.date) -> dt.date:
    """The latest trading day on or before ``today``."""
    cur = today
    while not is_trading_day(cur):
        cur -= dt.timedelta(days=1)
    return cur


def sessions_behind(latest: dt.date, today: dt.date) -> int:
    """How many trading sessions ``latest`` is behind the most recent one.

    0 = fully current, 1 = today's bar not published yet (still considered fresh).
    """
    target = most_recent_session(today)
    if latest >= target:
        return 0
    count = 0
    cur = target
    while cur > latest:
        cur = previous_trading_day(cur)
        count += 1
    return count
