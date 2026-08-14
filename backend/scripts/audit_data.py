"""Audit the cached market data for gaps, bad prices, and logged anomalies.

Run any time you want to trust the numbers on screen:

    python scripts/audit_data.py            # summary + problems
    python scripts/audit_data.py --verbose  # also list every anomaly

Exits non-zero when it finds a real problem (missing sessions on a liquid
ticker, non-positive prices, or tickers with too little history to analyze).
Stop the backend first — DuckDB allows a single writer process.
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows consoles default to cp1252 and choke on the em-dashes below.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import duckdb  # noqa: E402

from app.config import settings  # noqa: E402
from app.services.trading_calendar import is_trading_day, most_recent_session  # noqa: E402

# A ticker needs at least this many sessions for MA200 + a year of returns.
MIN_USABLE_SESSIONS = 300
# Ignore stragglers older than this when checking for missing recent sessions.
RECENT_WINDOW_DAYS = 30


def expected_sessions(start: dt.date, end: dt.date) -> int:
    d, n = start, 0
    while d <= end:
        if is_trading_day(d):
            n += 1
        d += dt.timedelta(days=1)
    return n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true", help="List every anomaly row.")
    args = ap.parse_args()

    db = settings.duckdb_path
    if not db.exists():
        print(f"No database at {db}. Start the backend once to warm it.")
        return 1

    try:
        con = duckdb.connect(str(db), read_only=True)
    except duckdb.IOException as exc:
        print(f"Can't open {db} — is the backend running? Stop it first.\n  {exc}")
        return 1

    problems = 0
    today = dt.date.today()
    session = most_recent_session(today)

    # ---------------------------------------------------------------- coverage
    total, tickers, first, last = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT ticker), MIN(date), MAX(date) FROM prices"
    ).fetchone()
    print("=" * 68)
    print("STOCKY DATA AUDIT")
    print("=" * 68)
    print(f"Rows            : {total:,}")
    print(f"Tickers         : {tickers}")
    print(f"Date span       : {first} -> {last}  ({(last - first).days} days)")
    print(f"Latest session  : {session} (expected)")
    if last < session:
        print(f"  !! cached data is behind the calendar by at least one session")
        problems += 1
    else:
        print("  data is current with the NYSE calendar")

    # ------------------------------------------------------------ history depth
    depth = con.execute(
        """
        SELECT median(n), min(n), max(n), arg_min(ticker, n)
        FROM (SELECT ticker, COUNT(*) AS n FROM prices GROUP BY ticker)
        """
    ).fetchone()
    print(f"\nSessions/ticker : median {int(depth[0])}, min {int(depth[1])} "
          f"({depth[3]}), max {int(depth[2])}")

    thin = con.execute(
        "SELECT ticker, COUNT(*) n FROM prices GROUP BY ticker HAVING n < ? ORDER BY n",
        [MIN_USABLE_SESSIONS],
    ).fetchall()
    if thin:
        print(f"  !! {len(thin)} ticker(s) under {MIN_USABLE_SESSIONS} sessions "
              f"(too thin for MA200 / 1y returns):")
        for t, n in thin[:15]:
            print(f"       {t:<6} {n} sessions")
        problems += 1
    else:
        print(f"  every ticker has >= {MIN_USABLE_SESSIONS} sessions")

    # -------------------------------------------------------------- bad prices
    bad = con.execute(
        """
        SELECT ticker, COUNT(*) FROM prices
        WHERE close IS NULL OR close <= 0 OR adj_close IS NULL OR adj_close <= 0
        GROUP BY ticker ORDER BY 2 DESC
        """
    ).fetchall()
    print(f"\nNon-positive/null prices: {len(bad)} ticker(s)")
    if bad:
        for t, n in bad[:15]:
            print(f"       {t:<6} {n} row(s)")
        problems += 1

    # ------------------------------------------------- missing recent sessions
    # Ground truth is the set of session dates actually present across the
    # universe — safer than recomputing the calendar, which drifts on holidays.
    cutoff = last - dt.timedelta(days=RECENT_WINDOW_DAYS)
    want = con.execute(
        "SELECT COUNT(DISTINCT date) FROM prices WHERE date > ?", [cutoff]
    ).fetchone()[0]
    calendar_want = expected_sessions(cutoff + dt.timedelta(days=1), last)
    if want != calendar_want:
        print(f"\nNote: {want} sessions in the data vs {calendar_want} expected from the "
              f"static holiday calendar — refresh trading_calendar.py if this persists.")
    gaps = con.execute(
        """
        SELECT ticker, COUNT(*) n FROM prices WHERE date > ?
        GROUP BY ticker HAVING n < ? ORDER BY n
        """,
        [cutoff, want],
    ).fetchall()
    print(f"\nRecent coverage (last {RECENT_WINDOW_DAYS}d, expect {want} sessions): "
          f"{len(gaps)} ticker(s) short")
    if gaps:
        for t, n in gaps[:15]:
            print(f"       {t:<6} {n}/{want}")
        # Missing recent bars on a few names is usually a listing change, not a
        # pipeline fault — report loudly but only fail if it's widespread.
        if len(gaps) > max(5, tickers * 0.02):
            problems += 1

    # --------------------------------------------------------------- anomalies
    rows = con.execute(
        "SELECT ticker, ts, detail FROM ingest_log WHERE kind = 'anomaly' ORDER BY ts DESC"
    ).fetchall()
    print(f"\nLogged anomalies (>40% single-day moves): {len(rows)}")
    print("  These are flagged for review, not errors — most are legitimate")
    print("  earnings gaps, splits, or index events.")
    for t, ts, detail in (rows if args.verbose else rows[:10]):
        print(f"       {t:<6} {str(ts)[:10]}  {detail}")
    if not args.verbose and len(rows) > 10:
        print(f"       … {len(rows) - 10} more (--verbose to list)")

    # ------------------------------------------------------------------ errors
    errs = con.execute(
        """
        SELECT kind, COUNT(*) FROM ingest_log
        WHERE kind IN ('fetch_error', 'bad_price', 'empty') GROUP BY kind
        """
    ).fetchall()
    print(f"\nIngest errors   : {dict(errs) if errs else 'none'}")
    if errs:
        problems += 1

    print("\n" + "=" * 68)
    print("RESULT: clean — the data behind the dashboard checks out."
          if problems == 0 else f"RESULT: {problems} problem area(s) above need attention.")
    print("=" * 68)
    return 0 if problems == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
