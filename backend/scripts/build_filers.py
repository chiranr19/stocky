# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Regenerate app/data/tracked_filers.json — the committed list of filers to track.

Resolves the *issuer* CIK for each tracked company from SEC EDGAR's official
`company_tickers.json` map, so the numbers are verified against the primary
source rather than hand-typed. Tracking by issuer CIK (not person CIK) catches
*every* insider of a company and is strictly more robust — a Form 4's XML names
the reporting owner, so per-person views fall out of parsing, not out of the
snapshot.

Run manually when the tracked set changes:

    python scripts/build_filers.py

Like build_sp500.py this is a maintenance script, not imported at runtime — the
app reads the committed JSON so it works offline. SEC fair-access policy wants a
descriptive User-Agent with contact info; set EDGAR_USER_AGENT in the
environment (falls back to a generic descriptor).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import urllib.request
from pathlib import Path

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
OUT_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "tracked_filers.json"

# Companies whose Form 4 insider filings we follow, and *why* each earns a slot.
# The `famous` name (when set) is the reporting owner we spotlight on the page;
# the company's other insiders still ingest and appear.
TRACKED_ISSUERS: list[dict[str, str]] = [
    {"ticker": "TSLA", "famous": "Musk Elon", "note": "Elon Musk — fully trackable via Form 4."},
    {"ticker": "NVDA", "famous": "Huang Jen-Hsun", "note": "Jensen Huang — the canonical 10b5-1 scheduled-sale teaching case."},
    {"ticker": "META", "famous": "Zuckerberg Mark", "note": "Mark Zuckerberg."},
    {"ticker": "AMD", "famous": "Su Lisa T", "note": "Lisa Su."},
    {"ticker": "AAPL", "famous": "Cook Timothy D", "note": "Tim Cook."},
    {"ticker": "MSFT", "famous": "Nadella Satya", "note": "Satya Nadella."},
    {"ticker": "AMZN", "famous": "Jassy Andrew R", "note": "Andy Jassy."},
    {"ticker": "DJT", "famous": "", "note": "Trump Media & Technology Group — the honest closest-to-Trump proxy. Presidents file only an annual OGE 278e; there is no per-trade Trump data."},
]

# Members of Congress we spotlight once STOCK Act PTR ingestion lands (Phase B/C).
# No CIK needed — the House Clerk / Senate eFD indices key on filer name.
FEATURED_CONGRESS: list[dict[str, str]] = [
    {"name": "Pelosi, Nancy", "chamber": "house", "note": "High-profile; large tech options via spouse."},
    {"name": "Tuberville, Tommy", "chamber": "senate", "note": "One of the most active Senate filers."},
    {"name": "Khanna, Ro", "chamber": "house", "note": "Very high filing volume in blind trusts — teaches volume != signal."},
    {"name": "McCaul, Michael", "chamber": "house", "note": "Large, wide-ranging portfolio."},
    {"name": "Gottheimer, Josh", "chamber": "house", "note": "Frequent, broad trading."},
    {"name": "Greene, Marjorie Taylor", "chamber": "house", "note": "Active individual-stock filer."},
    {"name": "Crenshaw, Dan", "chamber": "house", "note": "Active filer."},
]


def _user_agent() -> str:
    return os.environ.get(
        "EDGAR_USER_AGENT",
        "Stocky learning-app (personal, non-commercial) contact@example.com",
    )


def _fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": _user_agent()})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    print(f"Fetching {COMPANY_TICKERS_URL} ...")
    raw = _fetch_json(COMPANY_TICKERS_URL)
    # company_tickers.json is {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}, ...}
    by_ticker = {row["ticker"].upper(): row for row in raw.values()}

    issuers: list[dict] = []
    for spec in TRACKED_ISSUERS:
        ticker = spec["ticker"].upper()
        row = by_ticker.get(ticker)
        if row is None:
            print(f"  WARNING: {ticker} not found in company_tickers.json — skipping")
            continue
        issuers.append(
            {
                "ticker": ticker,
                "cik": int(row["cik_str"]),
                "issuer_name": row["title"],
                "famous_owner": spec["famous"],
                "note": spec["note"],
            }
        )
        print(f"  {ticker:6s} CIK {int(row['cik_str']):>10d}  {row['title']}")

    payload = {
        "snapshot_date": dt.date.today().isoformat(),
        "source": COMPANY_TICKERS_URL,
        "issuers": issuers,
        "featured_congress": FEATURED_CONGRESS,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(issuers)} issuers + {len(FEATURED_CONGRESS)} congress to {OUT_PATH}")


if __name__ == "__main__":
    main()
