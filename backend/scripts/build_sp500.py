"""Regenerate app/data/sp500_constituents.json from a public constituents CSV.

Run manually when you want to refresh the S&P 500 membership snapshot:

    python scripts/build_sp500.py

It is deliberately a maintenance script (not imported at runtime) — the app reads
the committed JSON so it works offline and doesn't depend on a live source.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/datasets/"
    "s-and-p-500-companies/main/data/constituents.csv"
)

OUT_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "sp500_constituents.json"


def normalize_ticker(symbol: str) -> str:
    """Yahoo Finance uses '-' for class shares (BRK.B -> BRK-B)."""
    return symbol.strip().upper().replace(".", "-")


def main() -> None:
    print(f"Fetching {SOURCE_URL} ...")
    with urllib.request.urlopen(SOURCE_URL, timeout=30) as resp:
        text = resp.read().decode("utf-8")

    reader = csv.DictReader(io.StringIO(text))
    constituents: list[dict[str, str]] = []
    for row in reader:
        constituents.append(
            {
                "ticker": normalize_ticker(row["Symbol"]),
                "name": row["Security"].strip(),
                "sector": row["GICS Sector"].strip(),
                "sub_industry": row["GICS Sub-Industry"].strip(),
            }
        )

    constituents.sort(key=lambda c: c["ticker"])
    payload = {
        "snapshot_date": dt.date.today().isoformat(),
        "source": SOURCE_URL,
        "count": len(constituents),
        "constituents": constituents,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(constituents)} constituents to {OUT_PATH}")

    sectors = sorted({c["sector"] for c in constituents})
    print(f"{len(sectors)} sectors: {', '.join(sectors)}")


if __name__ == "__main__":
    main()
