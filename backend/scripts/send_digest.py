# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Send the Stocky daily digest via Gmail SMTP.

Reads GMAIL_USER, GMAIL_APP_PASSWORD, DIGEST_TO from env (GitHub repo secrets
in CI). If any are missing, prints setup instructions and exits 0 — the
workflow guides instead of failing.

Usage:
    python -m scripts.send_digest [digest_dir] [snapshot.html]

    digest_dir   defaults to scripts/  (expects digest.html + digest.txt)
    snapshot     optional path to the HTML snapshot to attach
"""

from __future__ import annotations

import os
import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
DIGEST_TO = os.environ.get("DIGEST_TO", "")


def _setup_instructions() -> str:
    return """\
Daily digest email secrets are not configured yet.

One-time setup (takes ~2 minutes):
  1. Go to https://myaccount.google.com/apppasswords
     (requires 2-Step Verification to be enabled on your Google account)
  2. Create an app password - name it "Stocky" or anything you like
  3. Set the three secrets on your GitHub repo:

     gh secret set GMAIL_USER          # your Gmail address
     gh secret set GMAIL_APP_PASSWORD   # the 16-char app password
     gh secret set DIGEST_TO            # recipient email address

  Then re-run the workflow - the digest will be sent automatically.
"""


def main() -> int:
    if not GMAIL_USER or not GMAIL_APP_PASSWORD or not DIGEST_TO:
        print(_setup_instructions())
        return 0  # exit 0 so the workflow stays green

    digest_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    snapshot_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    html_path = digest_dir / "digest.html"
    txt_path = digest_dir / "digest.txt"

    if not html_path.exists():
        print(f"ERROR: {html_path} not found — run build_digest.py first.", file=sys.stderr)
        return 1

    html_body = html_path.read_text(encoding="utf-8")
    txt_body = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""

    # Date-stamp the subject: Gmail threads identical subjects together, which
    # would bury each new digest under the previous one. The builder's first
    # line is "STOCKY DAILY DIGEST — <date>"; reuse that date.
    subject = "Stocky Daily Digest"
    first_line = txt_body.split("\n", 1)[0] if txt_body else ""
    if "—" in first_line:
        subject = f"Stocky Daily Digest — {first_line.split('—', 1)[1].strip()}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = GMAIL_USER
    msg["To"] = DIGEST_TO

    if txt_body:
        msg.attach(MIMEText(txt_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Attach the snapshot HTML if provided.
    if snapshot_path and snapshot_path.exists():
        attachment = MIMEText(snapshot_path.read_text(encoding="utf-8"), "html", "utf-8")
        attachment.add_header("Content-Disposition", "attachment",
                              filename="stocky_snapshot.html")
        msg.attach(attachment)

    print(f"Sending digest to {DIGEST_TO} via {GMAIL_USER} …")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)
    print("Sent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
