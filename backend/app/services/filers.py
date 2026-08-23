"""Followed Filers (v0.8): study public insider & congressional disclosures.

What this is, precisely: corporate insiders must file **SEC Form 4** within two
business days of a trade, and members of Congress must file **STOCK Act PTRs**
within 30–45 days. Both are legally-required public records. This module ingests
them from **official primary sources only** (SEC EDGAR here; House Clerk / Senate
eFD in later phases), never a third-party aggregator, and turns them into a
teaching surface — with the disclosure *lag* and the historical *base rates* in
the same breath as any famous name. Nothing here is advice or a copy-trade
signal.

Design spine (mirrors the rest of the app):
  * **Two layers.** The *notice layer* (a filing exists — who, when, official
    link) is near-unbreakable and always shown. The *parse layer* (extracting
    the transactions) is best-effort behind a strict integrity pipeline; a
    filing that won't parse still surfaces with its original URL.
  * **Every number traces to a source** or to our own price cache — the same law
    the digest already enforces by test.
  * **Bounded, idempotent, resumable** ingestion — like market.py: INSERT OR
    REPLACE on a natural key, a per-source watermark, a hard per-run cap.
  * **Read-only enrichment** over cached prices (never fetches inline), like
    analytics.py.
"""

from __future__ import annotations

import datetime as dt
import threading
import time
from dataclasses import dataclass

import numpy as np
import pandas as pd
import requests
from defusedxml import ElementTree as DefusedET

from ..config import (
    DEFAULT_BUDGET,
    EDGAR_INITIAL_LOOKBACK_DAYS,
    EDGAR_MAX_FILINGS_PER_RUN,
    EDGAR_MIN_REQUEST_INTERVAL,
    EDGAR_REQUEST_TIMEOUT,
    FAMOUS_OWNER_BY_TICKER,
    FILER_CLUSTER_WINDOW_DAYS,
    FILER_FORWARD_WINDOWS,
    FILER_MIN_EPISODES,
    FILER_PRICE_TOLERANCE,
    TRACKED_ISSUERS,
    display_name,
    settings,
)
from ..db import db_lock
from ..models import DisclosedTrade, FilerBaseRate, FilerNotice, FilersResponse
from . import market

# SEC Form 4 transaction codes → our coarse action. Only open-market *purchases*
# (P) count as conviction "buys" for base rates and cluster notices; awards (A),
# option exercises (M), tax withholding (F) and gifts (G) are shown but not
# treated as discretionary buys — the honest classification.
_ACTION_BY_CODE = {"P": "buy", "S": "sell", "A": "grant"}

_HONESTY_NOTE = (
    "These are legally-required public disclosures, studied for learning — not "
    "advice or a signal to copy. Insider Form 4s are public within two business "
    "days; congressional trades can lag 30–45 days. Presidents file only an "
    "annual summary, so there is no per-trade Trump data — the closest public "
    "proxy is Form 4 activity by Trump Media (DJT) insiders."
)


# --------------------------------------------------------------------------- #
# EDGAR HTTP (rate-limited, declared UA, bounded)
# --------------------------------------------------------------------------- #
_net_lock = threading.Lock()
_last_request_at = 0.0


class FilerIngestError(RuntimeError):
    """Raised only for configuration problems (e.g. missing EDGAR_USER_AGENT)."""


def _log(kind: str, key: str, detail: str) -> None:
    """Quarantine/telemetry trail — same ingest_log table market.py writes to."""
    with db_lock() as con:
        con.execute(
            "INSERT INTO ingest_log (ts, ticker, kind, detail) VALUES (?, ?, ?, ?)",
            [dt.datetime.now(dt.UTC).replace(tzinfo=None), key, kind, detail[:180]],
        )


def _edgar_get(url: str) -> requests.Response | None:
    """One rate-limited GET with a declared User-Agent and a single backoff retry.

    Returns None on any failure (logged) — the caller degrades to the notice
    layer rather than crashing.
    """
    global _last_request_at
    if not settings.edgar_user_agent.strip():
        raise FilerIngestError(
            "EDGAR_USER_AGENT is not set. SEC fair-access policy requires a "
            "descriptive User-Agent with contact info. Set it in backend/.env."
        )
    headers = {"User-Agent": settings.edgar_user_agent, "Accept-Encoding": "gzip, deflate"}
    for attempt in (1, 2):
        with _net_lock:  # serialize + space out requests across threads
            gap = time.monotonic() - _last_request_at
            if gap < EDGAR_MIN_REQUEST_INTERVAL:
                time.sleep(EDGAR_MIN_REQUEST_INTERVAL - gap)
            _last_request_at = time.monotonic()
        try:
            resp = requests.get(url, headers=headers, timeout=EDGAR_REQUEST_TIMEOUT)
            if resp.status_code == 200:
                return resp
            if resp.status_code in (429, 503) and attempt == 1:
                time.sleep(1.5)
                continue
            _log("fetch_error", url[:60], f"HTTP {resp.status_code}")
            return None
        except Exception as exc:  # network hiccup — log and (maybe) retry
            if attempt == 2:
                _log("fetch_error", url[:60], f"{exc}")
                return None
            time.sleep(1.0)
    return None


# --------------------------------------------------------------------------- #
# Form 4 XML parsing (defused; defensive)
# --------------------------------------------------------------------------- #
@dataclass
class ParsedTx:
    """One transaction line lifted from a Form 4 — pre-validation."""

    ticker: str
    filer: str
    filer_role: str
    asset_class: str
    action: str
    trade_date: dt.date
    shares: float | None
    price: float | None
    scheduled: bool


def _txt(node, path: str) -> str:
    """Text at ``path`` under ``node`` ('' if absent) — tolerant of the schema."""
    if node is None:
        return ""
    el = node.find(path)
    return el.text.strip() if el is not None and el.text else ""


def _role_from(rel) -> str:
    """Human role string from a <reportingOwnerRelationship> node."""
    if rel is None:
        return ""
    parts: list[str] = []
    if _txt(rel, "isDirector") in ("1", "true"):
        parts.append("Director")
    if _txt(rel, "isOfficer") in ("1", "true"):
        parts.append(_txt(rel, "officerTitle") or "Officer")
    if _txt(rel, "isTenPercentOwner") in ("1", "true"):
        parts.append("10% owner")
    if _txt(rel, "isOther") in ("1", "true"):
        parts.append(_txt(rel, "otherText") or "Other")
    return ", ".join(parts)


def parse_form4(xml_bytes: bytes) -> tuple[str, list[ParsedTx]]:
    """Parse a Form 4 ownership document → (ticker, transactions).

    Raises on malformed XML (caller quarantines). Uses defusedxml so a hostile
    filing can't trigger XXE/entity-expansion — filings are untrusted input.
    """
    root = DefusedET.fromstring(xml_bytes)

    issuer = root.find("issuer")
    ticker = _txt(issuer, "issuerTradingSymbol").upper()

    owner = root.find("reportingOwner")
    filer = _txt(owner, "reportingOwnerId/rptOwnerName")
    role = _role_from(owner.find("reportingOwnerRelationship") if owner is not None else None)

    # 10b5-1 pre-arranged plans are flagged either by a dedicated element or,
    # historically, only in footnote prose — scan the raw text for either.
    blob = xml_bytes.decode("utf-8", errors="ignore").lower()
    scheduled = "10b5-1" in blob or "10b5-1" in blob.replace(" ", "")

    txs: list[ParsedTx] = []
    # Non-derivative = actual shares (what we can price). Derivative = options etc.
    for table_path, asset_class in (
        ("nonDerivativeTable/nonDerivativeTransaction", "equity"),
        ("derivativeTable/derivativeTransaction", "option"),
    ):
        for tx in root.findall(table_path):
            code = _txt(tx, "transactionCoding/transactionCode")
            action = _ACTION_BY_CODE.get(code, "other")
            date_str = _txt(tx, "transactionDate/value")
            if not date_str:
                continue
            try:
                trade_date = dt.date.fromisoformat(date_str[:10])
            except ValueError:
                continue
            shares = _to_float(_txt(tx, "transactionAmounts/transactionShares/value"))
            price = _to_float(_txt(tx, "transactionAmounts/transactionPricePerShare/value"))
            txs.append(
                ParsedTx(
                    ticker=ticker,
                    filer=filer,
                    filer_role=role,
                    asset_class=asset_class,
                    action=action,
                    trade_date=trade_date,
                    shares=shares,
                    price=price,
                    scheduled=scheduled,
                )
            )
    return ticker, txs


def _to_float(s: str) -> float | None:
    try:
        return float(s.replace(",", "")) if s else None
    except ValueError:
        return None


def aggregate_txs(txs: list[ParsedTx]) -> list[ParsedTx]:
    """Combine same-(ticker, date, action, class) tranches into one honest total.

    A single Form 4 routinely reports one trade as several execution lines at
    slightly different prices (a block filled in pieces). Our natural key can't
    tell them apart, so instead of letting them collapse and lose shares, we sum
    the shares and take the *share-weighted average* price — the true "Musk
    bought 253k @ ~$373" rather than one arbitrary tranche.
    """
    groups: dict[tuple, list[ParsedTx]] = {}
    for t in txs:
        key = (t.ticker, t.trade_date, t.action, t.asset_class, t.scheduled)
        groups.setdefault(key, []).append(t)

    out: list[ParsedTx] = []
    for group in groups.values():
        if len(group) == 1:
            out.append(group[0])
            continue
        total_shares = sum(t.shares for t in group if t.shares) or None
        priced = [(t.shares, t.price) for t in group if t.shares and t.price]
        if priced and total_shares:
            avg_price = round(sum(s * p for s, p in priced) / sum(s for s, _ in priced), 4)
        else:
            avg_price = next((t.price for t in group if t.price), None)
        head = group[0]
        out.append(
            ParsedTx(
                ticker=head.ticker, filer=head.filer, filer_role=head.filer_role,
                asset_class=head.asset_class, action=head.action,
                trade_date=head.trade_date, shares=total_shares, price=avg_price,
                scheduled=head.scheduled,
            )
        )
    return out


# --------------------------------------------------------------------------- #
# Integrity pipeline: validate → sanity-gate → cross-check → upsert
# --------------------------------------------------------------------------- #
def _price_band(ticker: str, on: dt.date) -> tuple[float, float] | None:
    """(low, high) from our OWN cached bar on/near ``on`` — cross-validates a price."""
    with db_lock() as con:
        row = con.execute(
            """
            SELECT low, high FROM prices
            WHERE ticker = ? AND date BETWEEN ? AND ?
            ORDER BY abs(date_diff('day', date, ?)) LIMIT 1
            """,
            [ticker, on - dt.timedelta(days=5), on + dt.timedelta(days=5), on],
        ).fetchone()
    if row is None or row[0] is None:
        return None
    return float(row[0]), float(row[1])


def _validated_row(
    tx: ParsedTx, filing_id: str, filed_date: dt.date, url: str, today: dt.date
) -> dict | None:
    """Run one parsed transaction through the sanity gates. None ⇒ quarantined."""
    # Gate 1: temporal coherence — you can't file before you trade, or trade
    # in the future.
    if not (tx.trade_date <= filed_date <= today):
        _log("suspect_value", tx.ticker,
             f"{filing_id}: bad dates trade={tx.trade_date} filed={filed_date}")
        return None

    # Gate 2: cross-validate a stated equity price against our own market data.
    # A parse slip (units, decimal) shows up as a price far outside that day's
    # range. Only open-market buys/sells price *at market* — exercises (M),
    # grants (A) and gifts legitimately price off a strike or at zero, so gating
    # them would wrongly quarantine real filings. Restrict the band check to P/S.
    if tx.action in ("buy", "sell") and tx.asset_class == "equity" and tx.price and tx.price > 0:
        band = _price_band(tx.ticker, tx.trade_date)
        if band is not None:
            lo, hi = band
            if not (lo * (1 - FILER_PRICE_TOLERANCE) <= tx.price <= hi * (1 + FILER_PRICE_TOLERANCE)):
                _log("suspect_value", tx.ticker,
                     f"{filing_id}: price {tx.price} outside {lo:.2f}-{hi:.2f} band")
                return None

    value = (tx.shares or 0.0) * (tx.price or 0.0)
    return {
        "source": "edgar",
        "filing_id": filing_id,
        "filer": tx.filer or "Unknown",
        "filer_role": tx.filer_role,
        "ticker": tx.ticker,
        "asset_class": tx.asset_class,
        "action": tx.action,
        "trade_date": tx.trade_date,
        "filed_date": filed_date,
        "shares": tx.shares,
        "price": tx.price,
        "value_lo": value,
        "value_hi": value,
        "scheduled": tx.scheduled,
        "url": url,
    }


def _store_rows(rows: list[dict]) -> int:
    """Idempotent upsert keyed by (source, filing_id, ticker, trade_date, action)."""
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    cols = [
        "source", "filing_id", "filer", "filer_role", "ticker", "asset_class",
        "action", "trade_date", "filed_date", "shares", "price", "value_lo",
        "value_hi", "scheduled", "url",
    ]
    df = df[cols]
    with db_lock() as con:
        con.register("incoming_filings", df)
        con.execute(
            f"INSERT OR REPLACE INTO disclosed_trades ({', '.join(cols)}) "
            f"SELECT {', '.join(cols)} FROM incoming_filings"
        )
        con.unregister("incoming_filings")
    return len(rows)


# --------------------------------------------------------------------------- #
# EDGAR ingestion (incremental, watermarked, bounded)
# --------------------------------------------------------------------------- #
def _watermark(cik: int) -> dt.date | None:
    with db_lock() as con:
        row = con.execute(
            "SELECT last_filing_date FROM filer_meta WHERE source = 'edgar' AND key = ?",
            [str(cik)],
        ).fetchone()
    return row[0] if row else None


def _set_watermark(cik: int, last_filing_date: dt.date | None) -> None:
    with db_lock() as con:
        con.execute(
            """
            INSERT INTO filer_meta (source, key, last_checked, last_filing_date)
            VALUES ('edgar', ?, ?, ?)
            ON CONFLICT (source, key) DO UPDATE SET
                last_checked = EXCLUDED.last_checked,
                last_filing_date = GREATEST(
                    COALESCE(filer_meta.last_filing_date, EXCLUDED.last_filing_date),
                    EXCLUDED.last_filing_date
                )
            """,
            [str(cik), dt.datetime.now(dt.UTC).replace(tzinfo=None), last_filing_date],
        )


def _primary_form4_url(cik: int, accession: str) -> str | None:
    """Locate the ownership XML inside a filing via its directory index.json."""
    nodash = accession.replace("-", "")
    idx = _edgar_get(f"https://www.sec.gov/Archives/edgar/data/{cik}/{nodash}/index.json")
    if idx is None:
        return None
    try:
        items = idx.json()["directory"]["item"]
    except Exception:
        return None
    # The ownership doc is the .xml that isn't the XSLT-rendered wrapper.
    for it in items:
        name = it.get("name", "")
        if name.lower().endswith(".xml") and "xsl" not in name.lower():
            return f"https://www.sec.gov/Archives/edgar/data/{cik}/{nodash}/{name}"
    return None


def _ingest_issuer(cik: int, budget_left: int, today: dt.date) -> tuple[int, dt.date | None]:
    """Pull new Form 4s for one issuer CIK. Returns (rows_stored, newest_filed)."""
    subs = _edgar_get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json")
    if subs is None:
        return 0, None
    try:
        recent = subs.json()["filings"]["recent"]
    except Exception:
        _log("parse_error", str(cik), "submissions JSON missing filings.recent")
        return 0, None

    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    filing_dates = recent.get("filingDate", [])

    watermark = _watermark(cik)
    cutoff = watermark or (today - dt.timedelta(days=EDGAR_INITIAL_LOOKBACK_DAYS))

    # Collect the new Form 4s, then walk them OLDEST-FIRST. EDGAR's `recent`
    # arrays are newest-first; if we processed in that order and a run hit the
    # per-run cap mid-issuer, the watermark would jump to the newest filing and
    # silently strand the older un-processed ones. Oldest-first means a truncated
    # run leaves the watermark at the newest *completed* filing, and the next run
    # resumes with everything above it — no gaps.
    eligible: list[tuple[str, dt.date]] = []
    for form, accession, fdate in zip(forms, accessions, filing_dates):
        if form not in ("4", "4/A"):
            continue
        try:
            filed_date = dt.date.fromisoformat(fdate)
        except ValueError:
            continue
        if filed_date <= cutoff:
            continue  # already have it (watermark) or older than the initial reach
        eligible.append((accession, filed_date))
    eligible.sort(key=lambda e: e[1])  # oldest-first

    stored = 0
    newest: dt.date | None = None
    for accession, filed_date in eligible:
        if budget_left - stored <= 0:
            break
        xml_url = _primary_form4_url(cik, accession)
        if xml_url is None:
            _log("parse_error", str(cik), f"{accession}: no ownership XML found")
            continue
        resp = _edgar_get(xml_url)
        if resp is None:
            continue
        try:
            _, txs = parse_form4(resp.content)
        except Exception as exc:
            _log("parse_error", str(cik), f"{accession}: {exc}")
            continue

        rows = [
            r for tx in aggregate_txs(txs)
            if (r := _validated_row(tx, accession, filed_date, xml_url, today)) is not None
        ]
        stored += _store_rows(rows)
        newest = filed_date if newest is None else max(newest, filed_date)

    return stored, newest


def ingest_edgar() -> dict:
    """Bounded incremental pull of Form 4s for every tracked issuer.

    Returns a small summary; safe to run repeatedly (idempotent upsert).
    """
    today = dt.date.today()
    total_stored = 0
    budget = EDGAR_MAX_FILINGS_PER_RUN
    for issuer in TRACKED_ISSUERS:
        if budget <= 0:
            break
        cik = int(issuer["cik"])
        stored, newest = _ingest_issuer(cik, budget, today)
        total_stored += stored
        budget -= stored
        _set_watermark(cik, newest)
    return {"stored": total_stored, "as_of": today.isoformat()}


# --------------------------------------------------------------------------- #
# Read + enrichment (read-only over the price cache — never fetches)
# --------------------------------------------------------------------------- #
def _read_trades() -> list[dict]:
    with db_lock() as con:
        rows = con.execute(
            """
            SELECT source, filing_id, filer, filer_role, ticker, asset_class,
                   action, trade_date, filed_date, shares, price, value_lo,
                   value_hi, scheduled, url
            FROM disclosed_trades
            ORDER BY filed_date DESC, trade_date DESC
            """
        ).fetchall()
    keys = [
        "source", "filing_id", "filer", "filer_role", "ticker", "asset_class",
        "action", "trade_date", "filed_date", "shares", "price", "value_lo",
        "value_hi", "scheduled", "url",
    ]
    return [dict(zip(keys, r)) for r in rows]


def _close_on_or_after(adj: pd.Series, d: dt.date) -> float | None:
    """First available adjusted close on/after ``d`` (None if past the series)."""
    if adj is None or adj.empty:
        return None
    ts = pd.Timestamp(d)
    sub = adj[adj.index >= ts]
    return float(sub.iloc[0]) if len(sub) else None


def _pct(a: float | None, b: float | None) -> float | None:
    """(a/b − 1)·100, guarded."""
    if a is None or b is None or b == 0:
        return None
    return round((a / b - 1.0) * 100.0, 2)


def sum_value_range(trades: list[dict]) -> tuple[float, float]:
    """Aggregate disclosed dollar amounts as a *range* [Σlo, Σhi], never a point.

    Congress reports amounts as bands ($1k–$15k, …). Summing the midpoints would
    invent precision that isn't there; summing the bounds keeps the honest
    uncertainty. Used for any "total disclosed" figure.
    """
    lo = sum(float(t.get("value_lo", 0.0) or 0.0) for t in trades)
    hi = sum(float(t.get("value_hi", 0.0) or 0.0) for t in trades)
    return lo, hi


def _forward_from(adj: pd.Series, on: dt.date, horizon: int) -> float | None:
    """Return % ``horizon`` sessions after the first bar on/after ``on``."""
    if adj is None or adj.empty:
        return None
    ts = pd.Timestamp(on)
    pos = adj.index.searchsorted(ts, side="left")
    if pos >= len(adj) or pos + horizon >= len(adj):
        return None
    base = float(adj.iloc[pos])
    fwd = float(adj.iloc[pos + horizon])
    if base <= 0:
        return None
    return (fwd / base - 1.0) * 100.0


def _price_series(tickers: set[str]) -> dict[str, pd.Series]:
    """adj_close per ticker from the cache — read-only, one query."""
    if not tickers:
        return {}
    start = dt.date.today() - market.HISTORY_LOOKBACK
    end = dt.date.today()
    histories = market.read_cached(sorted(tickers), start, end)
    return {t: df["adj_close"].dropna() for t, df in histories.items() if not df.empty}


def _enrich(trade: dict, series: dict[str, pd.Series], voo: pd.Series | None) -> DisclosedTrade:
    ticker = trade["ticker"]
    adj = series.get(ticker)
    priceable = trade["asset_class"] == "equity" and adj is not None and not adj.empty

    since_trade = since_filed = lag_tax = voo_since_filed = None
    if priceable:
        latest = float(adj.iloc[-1])
        at_trade = _close_on_or_after(adj, trade["trade_date"])
        at_filed = _close_on_or_after(adj, trade["filed_date"])
        since_trade = _pct(latest, at_trade)
        since_filed = _pct(latest, at_filed)
        lag_tax = _pct(at_filed, at_trade)
        if voo is not None and not voo.empty:
            voo_since_filed = _pct(float(voo.iloc[-1]), _close_on_or_after(voo, trade["filed_date"]))

    lag_days = (trade["filed_date"] - trade["trade_date"]).days
    return DisclosedTrade(
        source=trade["source"],
        filing_id=trade["filing_id"],
        filer=trade["filer"],
        filer_role=trade["filer_role"],
        ticker=ticker,
        name=display_name(ticker),
        asset_class=trade["asset_class"],
        action=trade["action"],
        trade_date=trade["trade_date"],
        filed_date=trade["filed_date"],
        lag_days=lag_days,
        shares=trade["shares"],
        price=trade["price"],
        value_lo=trade["value_lo"],
        value_hi=trade["value_hi"],
        scheduled=bool(trade["scheduled"]),
        url=trade["url"],
        priceable=bool(priceable),
        since_trade_pct=since_trade,
        since_filed_pct=since_filed,
        lag_tax_pct=lag_tax,
        voo_since_filed_pct=voo_since_filed,
    )


# --------------------------------------------------------------------------- #
# Base rates: pooled forward outcomes of a filer's disclosed BUYS
# --------------------------------------------------------------------------- #
def _confidence(n: int, n_years: int) -> str:
    if n >= 12 and n_years >= 3:
        return "high"
    if n >= 8 and n_years >= 2:
        return "medium"
    return "low"


def filer_base_rates(
    trades: list[dict], series: dict[str, pd.Series], voo: pd.Series | None
) -> list[FilerBaseRate]:
    """One row per (filer, forward window). Pools each filer's disclosed buys.

    Outcomes are measured from the *disclosure* date — the only date a follower
    could act — so the number honestly reflects what copying would have yielded.
    """
    # Group priceable open-market buys by filer.
    by_filer: dict[str, list[dict]] = {}
    for t in trades:
        if t["action"] == "buy" and t["asset_class"] == "equity" and t["ticker"] in series:
            by_filer.setdefault(t["filer"], []).append(t)

    out: list[FilerBaseRate] = []
    for filer, buys in by_filer.items():
        lags = [(b["filed_date"] - b["trade_date"]).days for b in buys]
        for window_name, horizon in FILER_FORWARD_WINDOWS.items():
            outcomes: list[float] = []
            excesses: list[float] = []
            years: set[int] = set()
            for b in buys:
                r = _forward_from(series[b["ticker"]], b["filed_date"], horizon)
                if r is None:
                    continue
                outcomes.append(r)
                years.add(b["filed_date"].year)
                if voo is not None and not voo.empty:
                    vr = _forward_from(voo, b["filed_date"], horizon)
                    if vr is not None:
                        excesses.append(r - vr)
            if len(outcomes) < FILER_MIN_EPISODES:
                continue
            arr = np.array(outcomes)
            n_years = len(years)
            out.append(
                FilerBaseRate(
                    filer=filer,
                    window_days=horizon,
                    n=len(arr),
                    median_fwd_pct=round(float(np.median(arr)), 2),
                    win_rate=round(float((arr > 0).mean()), 3),
                    worst_pct=round(float(arr.min()), 2),
                    best_pct=round(float(arr.max()), 2),
                    p25_pct=round(float(np.percentile(arr, 25)), 2),
                    p75_pct=round(float(np.percentile(arr, 75)), 2),
                    n_years=n_years,
                    confidence=_confidence(len(arr), n_years),
                    n_benchmarked=len(excesses),
                    beat_benchmark=int(sum(1 for x in excesses if x > 0)),
                    median_excess_pct=round(float(np.median(excesses)), 2) if excesses else None,
                    median_lag_days=int(round(float(np.median(lags)))) if lags else 0,
                )
            )
    out.sort(key=lambda r: (r.filer, r.window_days))
    return out


# --------------------------------------------------------------------------- #
# Notices — named, caveated patterns (the disclosure "flags")
# --------------------------------------------------------------------------- #
def build_notices(trades: list[dict]) -> list[FilerNotice]:
    notices: list[FilerNotice] = []

    # cluster_buying: ≥2 DISTINCT filers buying the same ticker within the window.
    # Scheduled (10b5-1) trades are pre-arranged, so they're excluded — a cluster
    # should mean independent decisions, not coincident calendars.
    buys_by_ticker: dict[str, list[dict]] = {}
    for t in trades:
        if t["action"] == "buy" and not t["scheduled"]:
            buys_by_ticker.setdefault(t["ticker"], []).append(t)
    for ticker, buys in buys_by_ticker.items():
        buys = sorted(buys, key=lambda b: b["trade_date"])
        for i, anchor in enumerate(buys):
            window_filers = {
                b["filer"] for b in buys[i:]
                if (b["trade_date"] - anchor["trade_date"]).days <= FILER_CLUSTER_WINDOW_DAYS
            }
            if len(window_filers) >= 2:
                notices.append(
                    FilerNotice(
                        code="cluster_buying",
                        headline=f"Several insiders bought {display_name(ticker)} at once",
                        detail=(
                            f"{len(window_filers)} different insiders of {ticker} filed "
                            f"open-market purchases within {FILER_CLUSTER_WINDOW_DAYS} days "
                            "of each other. Clustered insider buying is one of the few "
                            "insider patterns academics find mildly informative."
                        ),
                        tone="neutral",
                        caveat=(
                            "A cluster can also reflect a shared vesting or window-open "
                            "date rather than independent conviction, and the price has "
                            "already moved by the time you can read the filing."
                        ),
                        tickers=[ticker],
                        filers=sorted(window_filers),
                    )
                )
                break  # one notice per ticker is enough

    # scheduled_sale: a spotlighted owner's SELL under a 10b5-1 plan — the classic
    # "this is not a reaction to news" teaching moment (Jensen Huang / NVDA).
    for t in trades:
        if t["action"] == "sell" and t["scheduled"]:
            famous = FAMOUS_OWNER_BY_TICKER.get(t["ticker"], "")
            if famous and famous.lower() in (t["filer"] or "").lower():
                notices.append(
                    FilerNotice(
                        code="scheduled_sale",
                        headline=f"{display_name(t['ticker'])} insider sold on a pre-set plan",
                        detail=(
                            "This sale was made under a Rule 10b5-1 plan — scheduled "
                            "months in advance, executed automatically regardless of "
                            "the news. It is routine diversification, not a signal."
                        ),
                        tone="neutral",
                        caveat=(
                            "10b5-1 plans can still be started or amended opportunistically; "
                            "the label tells you the timing was pre-arranged, not why."
                        ),
                        tickers=[t["ticker"]],
                        filers=[t["filer"]],
                    )
                )
                break

    # filer_sold_radar_name: a tracked insider sold a stock the Entry Radar is
    # currently featuring — a useful tension to notice. Best-effort; the tracked
    # megacaps rarely clear the affordability cap, so this often (correctly) fires
    # nothing.
    try:
        from .radar import build_radar

        radar_tickers = {r.row.ticker for r in build_radar(DEFAULT_BUDGET, "3m", 100).rows}
        seen: set[str] = set()
        for t in trades:
            if t["action"] == "sell" and t["ticker"] in radar_tickers and t["ticker"] not in seen:
                seen.add(t["ticker"])
                notices.append(
                    FilerNotice(
                        code="filer_sold_radar_name",
                        headline=f"An insider sold {display_name(t['ticker'])}, which the radar features",
                        detail=(
                            f"{t['filer']} disclosed a sale of {t['ticker']}, a name the "
                            "Entry Radar currently flags as a pullback worth studying. "
                            "Worth holding both facts side by side."
                        ),
                        tone="caution",
                        caveat=(
                            "Insiders sell for taxes, diversification and liquidity far "
                            "more often than for a view on value — a sale is rarely a verdict."
                        ),
                        tickers=[t["ticker"]],
                        filers=[t["filer"]],
                    )
                )
    except Exception:
        pass  # radar not warm / unavailable — notice layer degrades quietly

    return notices


# --------------------------------------------------------------------------- #
# Public build (cached per data generation, kind, limit)
# --------------------------------------------------------------------------- #
_lock = threading.Lock()
_cache: dict = {"key": None, "by_params": {}}


def filings_health() -> dict:
    """Freshness watermark + quarantine counts for /health/data."""
    with db_lock() as con:
        through = con.execute("SELECT MAX(filed_date) FROM disclosed_trades").fetchone()[0]
        quarantined = con.execute(
            "SELECT COUNT(*) FROM ingest_log WHERE kind IN ('suspect_value', 'parse_error')"
        ).fetchone()[0]
        total = con.execute("SELECT COUNT(*) FROM disclosed_trades").fetchone()[0]
    return {
        "filings_through": through,
        "filings_quarantined": int(quarantined or 0),
        "filings_total": int(total or 0),
    }


def _build(kind: str, limit: int, action: str = "all") -> FilersResponse:
    raw = _read_trades()
    if kind == "insider":
        raw = [t for t in raw if t["source"] == "edgar"]
    elif kind == "congress":
        raw = [t for t in raw if t["source"] in ("house", "senate")]

    # Notices and base rates always see the full picture; only the displayed
    # `trades` list honors an action filter (e.g. purchases-only) below.
    display_pool = raw
    if action in ("buy", "sell", "grant"):
        display_pool = [t for t in raw if t["action"] == action]

    # Amendment handling: a later filing of the same economic event (same filer,
    # ticker, trade date, action) supersedes the earlier one. Keep the newest
    # filed_date per event so an amended Form 4 replaces the original in the view.
    def _dedupe(pool: list[dict]) -> list[dict]:
        best: dict[tuple, dict] = {}
        for t in pool:
            key = (t["filer"], t["ticker"], t["trade_date"], t["action"], t["shares"])
            prev = best.get(key)
            if prev is None or t["filed_date"] > prev["filed_date"]:
                best[key] = t
        return sorted(best.values(), key=lambda t: (t["filed_date"], t["trade_date"]), reverse=True)

    all_rows = _dedupe(raw)          # full picture → notices, base rates, freshness
    display_rows = _dedupe(display_pool)  # what the table shows (may be action-filtered)

    tickers = {t["ticker"] for t in all_rows}
    series = _price_series(tickers | {settings.benchmark})
    voo = series.get(settings.benchmark)

    trades = [_enrich(t, series, voo) for t in display_rows[:limit]]
    base_rates = filer_base_rates(all_rows, series, voo)
    notices = build_notices(all_rows)

    through = max((t["filed_date"] for t in all_rows), default=None)
    as_of = dt.date.today()
    return FilersResponse(
        as_of=as_of,
        kind=kind,
        source_label="SEC EDGAR (Form 4 insider filings)",
        filings_through=through,
        note=_HONESTY_NOTE,
        trades=trades,
        base_rates=base_rates,
        notices=notices,
    )


def build_filers(kind: str, limit: int, action: str = "all") -> FilersResponse:
    """Cached per (price-cache generation, kind, limit, action) like radar/watchouts."""
    from . import analytics

    cache_key = analytics._cache["key"]
    params = (kind, limit, action)
    with _lock:
        if _cache["key"] != cache_key:
            _cache["key"] = cache_key
            _cache["by_params"] = {}
        cached = _cache["by_params"].get(params)
        if cached is not None:
            return cached
    result = _build(kind, limit, action)
    with _lock:
        _cache["by_params"][params] = result
    return result
