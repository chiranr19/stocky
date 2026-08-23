"""Incremental ingest of public Form 4 disclosures for tracked filers.

Bounded, idempotent, resumable (per-issuer watermark) — safe to run daily from
the digest cron. Reads SEC EDGAR only. Requires EDGAR_USER_AGENT (SEC fair-access
policy); if it's missing the script prints setup instructions and exits 0 so the
workflow guides rather than fails — the same forgiving contract as send_digest.py.

Usage:
    python -m scripts.warm_filings          # from backend/
    python backend/scripts/warm_filings.py  # from repo root
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.services import filers  # noqa: E402


def main() -> int:
    if not settings.edgar_user_agent.strip():
        print(
            "EDGAR_USER_AGENT is not set — skipping the filings ingest.\n\n"
            "SEC fair-access policy requires a descriptive User-Agent with contact\n"
            "info on every request. To enable insider-disclosure tracking:\n"
            "  • Local: add to backend/.env\n"
            '      EDGAR_USER_AGENT="Your Name your@email.com"\n'
            "  • CI: add a repository secret EDGAR_USER_AGENT and pass it through\n"
            "    in .github/workflows/daily-digest.yml.\n"
        )
        return 0  # not a failure — the rest of the pipeline still runs

    print("Stocky filings warm-up — pulling recent Form 4s for tracked issuers …")
    try:
        summary = filers.ingest_edgar()
    except filers.FilerIngestError as exc:
        print(f"Config error: {exc}")
        return 0

    health = filers.filings_health()
    print(f"\nStored {summary['stored']} new filing rows (as of {summary['as_of']}).")
    print(
        f"On record: {health['filings_total']} rows, "
        f"through {health['filings_through']}, "
        f"{health['filings_quarantined']} quarantined."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
