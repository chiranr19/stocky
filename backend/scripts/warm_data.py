"""Synchronous full-universe ingest for CI / digest pipeline.

Reuses the same chunked yfinance download + DuckDB upsert that the FastAPI
warm-up thread does, but runs synchronously and exits non-zero if fewer than
90% of tickers loaded.

Usage:
    python -m scripts.warm_data          # from backend/
    python backend/scripts/warm_data.py  # from repo root
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend package is importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.market import warm_universe, warm_state  # noqa: E402


def main() -> int:
    print("Stocky data warm-up — ingesting S&P 500 universe …")
    warm_universe()
    state = warm_state()
    loaded = state.loaded - len(state.failed)
    total = state.total
    pct = loaded / total * 100 if total else 0

    print(f"\nDone: {loaded}/{total} tickers ({pct:.0f}%)")
    if state.failed:
        print(f"Failed ({len(state.failed)}): {', '.join(state.failed[:20])}")

    if pct < 90:
        print("FAIL: <90% loaded — data quality too low for a digest.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
