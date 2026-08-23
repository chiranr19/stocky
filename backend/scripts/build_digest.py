# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Build the Stocky daily email digest — HTML + plain-text.

Every sentence is template-assembled from computed values produced by the
deterministic engines (insights, flags, radar, analytics). No LLM text.

Usage (backend warm-up must have completed first):
    python -m scripts.build_digest [output_dir]

Writes digest.html and digest.txt into `output_dir` (default: scripts/).
"""

from __future__ import annotations

import datetime as dt
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import DEFAULT_BUDGET, display_name  # noqa: E402
from app.models import Reading  # noqa: E402
from app.services import analytics, insights, learn  # noqa: E402
from app.services.calendar import build_calendar  # noqa: E402
from app.services.flags import GLOSSARY  # noqa: E402
from app.services.radar import build_radar  # noqa: E402

HERE = Path(__file__).parent


# ── Helpers ──────────────────────────────────────────────────────────────────

def _chg(v: float | None) -> str:
    if v is None:
        return "-"
    return f"{v:+.2f}%"


def _chg_html(v: float | None) -> str:
    if v is None:
        return '<span style="color:#8B929C">-</span>'
    color = "#22C989" if v > 0 else "#F6465D" if v < 0 else "#8B929C"
    return f'<span style="color:{color}">{v:+.2f}%</span>'


def _money(v: float) -> str:
    return f"${v:,.2f}" if v < 1000 else f"${v:,.0f}"


def _conf_label(conf: str) -> str:
    return {"high": "strong", "medium": "decent", "low": "thin"}.get(conf, conf)


def _session_info(as_of: dt.date) -> tuple[bool, str]:
    """(intraday, build-time label).

    The digest is scheduled at 3 PM ET — inside the trading session — so its
    prices are an intraday snapshot, not the close. The copy must say which.
    Intraday only when we're inside NYSE regular hours AND the data actually
    carries today's (partial) bar; a holiday build falls back to "close".
    """
    try:
        from zoneinfo import ZoneInfo
        now = dt.datetime.now(ZoneInfo("America/New_York"))
    except Exception:  # tz database unavailable — assume after-close
        return False, ""
    intraday = (now.weekday() < 5
                and dt.time(9, 30) <= now.time() < dt.time(16, 0)
                and as_of == now.date())
    hour12 = (now.hour - 1) % 12 + 1
    label = f"{hour12}:{now.minute:02d} {'PM' if now.hour >= 12 else 'AM'} ET"
    return intraday, label


def _echo_scope(echo) -> str:
    """Which past episodes the echo counted — 'exact' bucket vs widened."""
    if echo.kind == "at_least":
        return f"dips of at least {echo.min_depth_pct:.0f}%"
    return f"dips of {echo.bucket_lo:.0f}-{echo.bucket_hi:.0f}%"


def _best_per_sector(rows) -> list:
    """Top-scoring setup per sector (``rows`` arrive sorted by score desc)."""
    best: dict[str, object] = {}
    for r in rows:
        best.setdefault(r.row.sector, r)
    return sorted(best.values(), key=lambda r: -r.entry_score)


def _flags_in_play(radar, watchouts, sector_best=None) -> list[str]:
    """Distinct flag codes shown anywhere in this digest, in order seen."""
    codes: list[str] = []
    for r in list(radar.rows) + list(sector_best or []) + list(watchouts.rows):
        for fl in r.flags:
            if fl.code not in codes and fl.code in GLOSSARY:
                codes.append(fl.code)
    return codes


def _umbrella_correlation(basket) -> tuple[float, float] | None:
    """Live min/max pairwise correlation among the 'umbrella' members, if any."""
    if basket is None:
        return None
    labels = basket.correlation.get("labels", [])
    matrix = basket.correlation.get("matrix", [])
    idx = [labels.index(m.ticker) for m in basket.members
           if m.group == "umbrella" and m.ticker in labels]
    vals: list[float] = []
    for a in idx:
        for b in idx:
            if a == b:
                continue
            v = matrix[a][b]
            if isinstance(v, (int, float)) and v == v:  # exclude NaN
                vals.append(v)
    return (min(vals), max(vals)) if vals else None


def _law_of_the_day(basket, as_of: dt.date) -> str:
    """One of the watchlist's laws, rotated deterministically by the date."""
    if basket is None or not basket.laws:
        return ""
    return basket.laws[as_of.toordinal() % len(basket.laws)]


def _upcoming_events(cal, limit: int = 5) -> list[tuple[dt.date, str]]:
    """The next few dated events, earnings and macro merged, soonest first.

    Deliberately not windowed to "this week": macro releases are roughly
    monthly, so a 7-day window leaves this section empty most days. Knowing the
    next CPI print is three weeks out is still worth a line.
    """
    today = dt.date.today()
    events = [(e.date, e.label) for e in cal.macro if e.date >= today]
    events += [(e.date, f"{e.ticker} earnings") for e in cal.earnings if e.date >= today]
    events.sort(key=lambda x: x[0])
    return events[:limit]


# ── Data assembly ────────────────────────────────────────────────────────────

def _gather():
    """Collect all data from the existing services."""
    overview = analytics.build_overview()
    radar = build_radar(DEFAULT_BUDGET, "3m", 5)
    # Wider pull for the sector spread — best affordable setup in each sector,
    # so the digest never reads as one crowded corner of the market.
    sector_best = _best_per_sector(build_radar(DEFAULT_BUDGET, "3m", 60).rows)
    watchouts = analytics.build_watchouts(DEFAULT_BUDGET, 5)
    gainers = analytics.build_movers("gainers", DEFAULT_BUDGET, 3)
    losers = analytics.build_movers("losers", DEFAULT_BUDGET, 3)
    cal = build_calendar()
    basket = learn.build_basket()
    return overview, radar, sector_best, watchouts, gainers, losers, cal, basket


# ── Plain text ───────────────────────────────────────────────────────────────

def build_text(overview, radar, watchouts, gainers, losers, cal,
               sector_best=None, basket=None) -> str:
    lines: list[str] = []
    as_of = overview.as_of.strftime("%b %d, %Y").replace(" 0", " ")
    intraday, t_label = _session_info(overview.as_of)
    lead = f" — {radar.rows[0].row.ticker} leads the radar" if radar.rows else ""
    lines.append(f"STOCKY DAILY DIGEST — {as_of}{lead}")
    lines.append("=" * 50)
    if intraday:
        lines.append(f"(intraday snapshot, built {t_label} — the market closes at 4 PM)")

    # § At a glance — the market read in sentences, not fragments
    lines.append("")
    lines.append("AT A GLANCE")
    lines.append("-" * 30)
    for t in overview.tiles:
        val = _money(t.value) if t.unit == "usd" else (
            f"{t.value:.2f}%" if t.unit == "percent" else f"{t.value:.2f}")
        lines.append(f"  {t.label}: {val} ({_chg(t.change_pct)})")

    b = overview.breadth
    lines.append(f"  Breadth: {b.pct_above_ma50:.0f}% of S&P names are above their "
                 f"50-day average, {b.advancers} advancing vs {b.decliners} declining, "
                 f"{b.new_highs_52w} new 52-week high{'s' if b.new_highs_52w != 1 else ''} "
                 f"vs {b.new_lows_52w} new low{'s' if b.new_lows_52w != 1 else ''}.")

    if overview.readings:
        lines.append("")
        lines.append("  What that means:")
        for r in overview.readings:
            lines.append(f"  * {r.headline}")
            lines.append(f"    {r.detail}")
            if r.analogy:
                lines.append(f"    Think of it like: {r.analogy}")

    # § Today's standout setup — the radar's #1, with the full reasoning
    if radar.rows:
        top = radar.rows[0]
        s = top.row
        lines.append("")
        lines.append("TODAY'S STANDOUT SETUP")
        lines.append("-" * 30)
        lines.append(f"  {s.ticker} ({display_name(s.ticker)}) — {_money(s.price)}, {s.sector}")
        factor_bit = ", ".join(f"{k} {v:.0f}" for k, v in top.entry_factors.items())
        lines.append(f"  Top entry score on today's radar: {top.entry_score:.0f}/100 "
                     f"({factor_bit}).")
        trend_bit = ("below its 200-day average — a falling knife, not a dip"
                     if top.falling_knife else "with its long-term trend intact")
        lines.append(f"  It sits {top.depth_pct:.0f}% below its recent high, {trend_bit}.")
        if top.echo:
            e_ = top.echo
            wins = round(e_.win_rate * e_.n)
            lines.append(f"  Its own history: across {e_.n} past {_echo_scope(e_)}, a month "
                         f"later the median outcome was {_chg(e_.median_fwd_pct)}, "
                         f"{wins} of {e_.n} ended higher, worst case {_chg(e_.worst_pct)} "
                         f"({_conf_label(e_.confidence)} sample spanning {e_.n_years} "
                         f"calendar years).")
            if e_.p25_pct is not None and e_.p75_pct is not None:
                lines.append(f"  The middle half of those outcomes landed between "
                             f"{_chg(e_.p25_pct)} and {_chg(e_.p75_pct)}.")
            if e_.n_benchmarked and e_.median_excess_pct is not None:
                lines.append(f"  Against just holding VOO over the same windows: ahead "
                             f"{e_.beat_benchmark} of {e_.n_benchmarked} times, median "
                             f"edge {_chg(e_.median_excess_pct)}.")
            if e_.median_fwd_pct < 0 or e_.win_rate < 0.5:
                lines.append("  Score and history disagree here: today's numbers look "
                             "strong, but similar past dips more often kept falling. "
                             "The kind of setup to study, not chase.")
            else:
                lines.append("  That worst case happened to a setup that looked this good "
                             "too — base rates describe the past, not the future.")
        else:
            lines.append("  No base rate quoted: too few similar past dips in this stock's "
                         "history to measure — thinner evidence, not a green light.")
        for fl in top.flags[:2]:
            lines.append(f"  Hazard on this setup — {fl.label} ({fl.severity}): {fl.why}")
        if len(radar.rows) > 1:
            others = ", ".join(f"{r.row.ticker} ({r.entry_score:.0f})"
                               for r in radar.rows[1:4])
            lines.append(f"  Next in line: {others} — full table below.")

    # § Today's top watch-out — the mirror image, with the reasons spelled out
    if watchouts.rows:
        wo = watchouts.rows[0]
        lines.append("")
        lines.append("TODAY'S TOP WATCH-OUT")
        lines.append("-" * 30)
        lines.append(f"  {wo.row.ticker} ({display_name(wo.row.ticker)}) — "
                     f"{_money(wo.row.price)}, risk score {wo.risk_score:.0f}")
        for fl in wo.flags[:3]:
            lines.append(f"  * {fl.label} ({fl.severity}): {fl.why}")
        if wo.flags:
            lines.append(f"    What veterans do: {wo.flags[0].what_vets_do}")

    # § Details
    lines.append("")
    lines.append("THE DETAILS")
    lines.append("-" * 30)

    lines.append("")
    lines.append("Entry Radar — top 5 pullback setups (budget <= $200):")
    for i, r in enumerate(radar.rows, 1):
        echo = ""
        if r.echo:
            echo = (f" | {r.echo.n} past dips -> {_chg(r.echo.median_fwd_pct)} med, "
                    f"worst {_chg(r.echo.worst_pct)}, {_conf_label(r.echo.confidence)}")
        knife = " [KNIFE]" if r.falling_knife else ""
        risk_chips = ""
        if r.flags:
            risk_chips = " [" + ", ".join(f.label for f in r.flags[:2]) + "]"
        lines.append(f"  {i}. {r.row.ticker} ({display_name(r.row.ticker)}) "
                     f"{_money(r.row.price)} | -{r.depth_pct:.0f}% dip | "
                     f"score {r.entry_score:.0f}{knife}{risk_chips}{echo}")

    if sector_best:
        lines.append("")
        lines.append("Across the sectors — the strongest affordable setup in each:")
        for r in sector_best:
            echo = ""
            if r.echo:
                echo = (f" | {r.echo.n} dips -> {_chg(r.echo.median_fwd_pct)} med, "
                        f"worst {_chg(r.echo.worst_pct)}")
            knife = " [KNIFE]" if r.falling_knife else ""
            lines.append(f"  {r.row.sector}: {r.row.ticker} {_money(r.row.price)} | "
                         f"-{r.depth_pct:.0f}% dip | score {r.entry_score:.0f}"
                         f"{knife}{echo}")

    lines.append("")
    lines.append("Watch-outs — top 5 risk-heavy names:")
    for i, r in enumerate(watchouts.rows, 1):
        flags = ", ".join(f"{f.label} ({f.severity})" for f in r.flags[:3])
        lines.append(f"  {i}. {r.row.ticker} ({display_name(r.row.ticker)}) "
                     f"{_money(r.row.price)} | risk {r.risk_score:.0f} | {flags}")

    if basket is not None and basket.members:
        lines.append("")
        lines.append("Your watchlist — the cast:")
        for m in basket.members:
            price = _money(m.price) if m.price is not None else "-"
            chg = f" ({_chg(m.change_pct)})" if m.change_pct is not None else ""
            tail = "" if m.measurable else " (too little history to measure)"
            lines.append(f"  {m.ticker:<5} {price}{chg} — {m.role}{tail}")
        u = _umbrella_correlation(basket)
        if u is not None:
            names = "/".join(m.ticker for m in basket.members if m.group == "umbrella")
            lines.append(f"  The umbrellas moved as one again: {names} correlation "
                         f"{u[0]:.2f}-{u[1]:.2f} over the last six months.")
        law = _law_of_the_day(basket, overview.as_of)
        if law:
            lines.append(f"  Today's law: {law}")

    # Since yesterday on your watchlist — the what-changed feed (cap 6 lines).
    if basket is not None and basket.events:
        lines.append("")
        lines.append("Since yesterday on your watchlist:")
        for e in basket.events[:6]:
            lines.append(f"  * {e.headline}")
            lines.append(f"    {e.detail}")

    lines.append("")
    lines.append("Movers:")
    lines.append("  Gainers: " + ", ".join(
        f"{r.ticker} {_chg(r.change_pct)}" for r in gainers))
    lines.append("  Losers:  " + ", ".join(
        f"{r.ticker} {_chg(r.change_pct)}" for r in losers))

    upcoming = _upcoming_events(cal)
    if upcoming:
        lines.append("")
        lines.append("Coming up:")
        for d, label in upcoming:
            lines.append(f"  {d.strftime('%a %b %d')} — {label}")

    codes = _flags_in_play(radar, watchouts, sector_best)
    if codes:
        lines.append("")
        lines.append("FLAGS EXPLAINED")
        lines.append("-" * 30)
        lines.append("Every label used above, and the pattern behind it:")
        for code in codes:
            g = GLOSSARY[code]
            lines.append(f"  [{g['kind']}] {g['label']} — {g['meaning']}")
            if g.get("analogy"):
                lines.append(f"      Think of it like: {g['analogy']}")
            lines.append(f"      What vets do: {g['vets']}")

    lines.append("")
    lines.append("-" * 50)
    src = (f"intraday Yahoo Finance data (built {t_label}, before the close)"
           if intraday else "Yahoo Finance end-of-day data")
    lines.append(f"Every number above is computed from {src} "
                 f"as of {as_of}; no text in this email is model-generated. "
                 f"Educational, not advice.")
    return "\n".join(lines)


# ── HTML ─────────────────────────────────────────────────────────────────────

def build_html(overview, radar, watchouts, gainers, losers, cal,
               sector_best=None, basket=None) -> str:
    as_of = overview.as_of.strftime("%b %d, %Y").replace(" 0", " ")
    intraday, t_label = _session_info(overview.as_of)
    stamp = f"{as_of} &middot; {t_label} snapshot" if intraday else f"{as_of} close"
    src = (f"intraday Yahoo Finance data (built {t_label}, before the close)"
           if intraday else "Yahoo Finance end-of-day data")
    e = escape

    # Tiles
    tiles_html = ""
    for t in overview.tiles:
        val = _money(t.value) if t.unit == "usd" else (
            f"{t.value:.2f}%" if t.unit == "percent" else f"{t.value:.2f}")
        tiles_html += (
            f'<td style="padding:8px 12px;border-bottom:1px solid #E5E7EB">'
            f'<div style="font-size:11px;color:#6B7280;text-transform:uppercase">{e(t.label)}</div>'
            f'<div style="font-size:18px;font-weight:600">{val}</div>'
            f'<div style="font-size:13px">{_chg_html(t.change_pct)}</div>'
            f'</td>'
        )

    # Breadth
    b = overview.breadth
    breadth_color = "#22C989" if b.pct_above_ma50 >= 50 else "#F6465D"
    breadth_html = (
        f'<table width="100%" cellpadding="0" cellspacing="0" style="margin:8px 0;font-size:13px">'
        f'<tr>'
        f'<td style="padding:4px 8px">Above 50-day: <strong style="color:{breadth_color}">{b.pct_above_ma50:.0f}%</strong></td>'
        f'<td style="padding:4px 8px">Adv/Dec: <strong>{b.advancers}/{b.decliners}</strong></td>'
        f'<td style="padding:4px 8px">New highs: <strong>{b.new_highs_52w}</strong></td>'
        f'</tr></table>'
    )

    # Readings (at a glance) — headline plus the explanation, not just a fragment
    readings_html = ""
    for r in overview.readings:
        tone_color = "#22C989" if r.tone == "constructive" else "#F6465D" if r.tone == "caution" else "#6B7280"
        analogy_html = (
            f'<div style="font-size:12px;color:#6B7280;font-style:italic;margin-top:2px">'
            f'Think of it like: {e(r.analogy)}</div>'
        ) if r.analogy else ""
        readings_html += (
            f'<div style="padding:8px 0;border-bottom:1px solid #F3F4F6">'
            f'<div style="font-size:13px;color:{tone_color};font-weight:600">{e(r.headline)}</div>'
            f'<div style="font-size:12px;color:#4B5563;margin-top:2px">{e(r.detail)}</div>'
            f'{analogy_html}'
            f'</div>'
        )

    # Today's standout setup — the radar's #1 with the full reasoning
    setup_html = ""
    if radar.rows:
        top = radar.rows[0]
        s = top.row
        factor_bit = " &middot; ".join(f"{e(k)} {v:.0f}" for k, v in top.entry_factors.items())
        trend_bit = ("below its 200-day average — a falling knife, not a dip"
                     if top.falling_knife else "with its long-term trend intact")
        if top.echo:
            e_ = top.echo
            if e_.median_fwd_pct < 0 or e_.win_rate < 0.5:
                echo_note = ('Score and history disagree here: today&#39;s numbers look '
                             'strong, but similar past dips more often kept falling. '
                             'The kind of setup to study, not chase.')
            else:
                echo_note = ('That worst case happened to a setup that looked this good '
                             'too — base rates describe the past, not the future.')
            wins = round(e_.win_rate * e_.n)
            spread_bit = ""
            if e_.p25_pct is not None and e_.p75_pct is not None:
                spread_bit = (f' The middle half of those outcomes landed between '
                              f'{_chg_html(e_.p25_pct)} and {_chg_html(e_.p75_pct)}.')
            voo_bit = ""
            if e_.n_benchmarked and e_.median_excess_pct is not None:
                voo_bit = (f' Against just holding <strong>VOO</strong> over the same '
                           f'windows: ahead {e_.beat_benchmark} of {e_.n_benchmarked} '
                           f'times, median edge {_chg_html(e_.median_excess_pct)}.')
            echo_html = (
                f'<div style="font-size:13px;margin-top:6px">'
                f'<strong>Its own history:</strong> across {e_.n} past {e(_echo_scope(e_))}, '
                f'a month later the median outcome was {_chg_html(e_.median_fwd_pct)}, '
                f'{wins} of {e_.n} ended higher, worst case {_chg_html(e_.worst_pct)} '
                f'({_conf_label(e_.confidence)} sample spanning {e_.n_years} calendar years).'
                f'{spread_bit}{voo_bit} '
                f'<span style="color:#6B7280">{echo_note}</span>'
                f'</div>'
            )
        else:
            echo_html = (
                '<div style="font-size:13px;margin-top:6px;color:#6B7280">'
                'No base rate quoted: too few similar past dips in this stock&#39;s '
                'history to measure — thinner evidence, not a green light.</div>'
            )
        flag_bits = "".join(
            f'<div style="font-size:12px;color:#B45309;margin-top:4px">'
            f'&#9888; {e(fl.label)} ({e(fl.severity)}): {e(fl.why)}</div>'
            for fl in top.flags[:2]
        )
        others = ""
        if len(radar.rows) > 1:
            others_txt = ", ".join(f"{r.row.ticker} ({r.entry_score:.0f})"
                                   for r in radar.rows[1:4])
            others = (f'<div style="font-size:12px;color:#6B7280;margin-top:6px">'
                      f'Next in line: {e(others_txt)} — full table below.</div>')
        setup_html = (
            f'<div style="padding:14px 16px;background:#F0FDF4;border-radius:8px;'
            f'border:1px solid #BBF7D0;margin:12px 0">'
            f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.05em;'
            f'color:#15803D;font-weight:700">Today&#39;s standout setup</div>'
            f'<div style="font-size:18px;font-weight:700;margin-top:4px">{e(s.ticker)} '
            f'<span style="font-weight:400;color:#6B7280;font-size:13px">'
            f'{e(display_name(s.ticker))} &middot; {e(s.sector)}</span></div>'
            f'<div style="font-size:13px;margin-top:6px">{_money(s.price)}, '
            f'{top.depth_pct:.0f}% below its recent high, {trend_bit}. '
            f'Top entry score on today&#39;s radar: <strong>{top.entry_score:.0f}/100</strong> '
            f'<span style="color:#6B7280;font-size:12px">({factor_bit})</span>.</div>'
            f'{echo_html}{flag_bits}{others}'
            f'</div>'
        )

    # Today's top watch-out — the mirror image, with the reasons spelled out
    watchout_html = ""
    if watchouts.rows:
        wo = watchouts.rows[0]
        hazard_rows = "".join(
            f'<div style="font-size:13px;margin-top:4px"><strong>{e(fl.label)}</strong> '
            f'<span style="font-size:11px;color:#DC2626">({e(fl.severity)})</span>: '
            f'{e(fl.why)}</div>'
            for fl in wo.flags[:3]
        )
        vets = ""
        if wo.flags:
            vets = (f'<div style="font-size:12px;color:#6B7280;margin-top:6px">'
                    f'What veterans do: {e(wo.flags[0].what_vets_do)}</div>')
        watchout_html = (
            f'<div style="padding:14px 16px;background:#FEF2F2;border-radius:8px;'
            f'border:1px solid #FECACA;margin:12px 0">'
            f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.05em;'
            f'color:#B91C1C;font-weight:700">Today&#39;s top watch-out</div>'
            f'<div style="font-size:18px;font-weight:700;margin-top:4px">{e(wo.row.ticker)} '
            f'<span style="font-weight:400;color:#6B7280;font-size:13px">'
            f'{e(display_name(wo.row.ticker))} &middot; risk score {wo.risk_score:.0f}'
            f'</span></div>'
            f'{hazard_rows}{vets}'
            f'</div>'
        )

    # Radar table
    radar_rows = ""
    for i, r in enumerate(radar.rows, 1):
        echo_cell = "-"
        if r.echo:
            echo_cell = (f'{r.echo.n} &rarr; {_chg(r.echo.median_fwd_pct)} med, '
                         f'worst {_chg(r.echo.worst_pct)}<br>'
                         f'<span style="font-size:11px;color:#9CA3AF">{_conf_label(r.echo.confidence)}</span>')
        knife = ' <span style="color:#F6465D;font-weight:600">[knife]</span>' if r.falling_knife else ""
        risk_chips = ""
        if r.flags:
            risk_chips = " ".join(
                f'<span style="display:inline-block;padding:1px 5px;border-radius:4px;'
                f'font-size:10px;background:#FEE2E2;color:#DC2626">{e(f.label)}</span>'
                for f in r.flags[:2]
            )
        radar_rows += (
            f'<tr style="border-bottom:1px solid #F3F4F6">'
            f'<td style="padding:6px 8px;color:#9CA3AF">{i}</td>'
            f'<td style="padding:6px 8px"><strong>{e(r.row.ticker)}</strong>{knife}<br>'
            f'<span style="font-size:11px;color:#9CA3AF">{e(display_name(r.row.ticker))}</span></td>'
            f'<td style="padding:6px 8px;text-align:right">{_money(r.row.price)}</td>'
            f'<td style="padding:6px 8px;text-align:right;color:#F6465D">-{r.depth_pct:.0f}%</td>'
            f'<td style="padding:6px 8px;text-align:center;font-weight:600">{r.entry_score:.0f}</td>'
            f'<td style="padding:6px 8px;font-size:12px">{echo_cell}</td>'
            f'<td style="padding:6px 8px">{risk_chips}</td>'
            f'</tr>'
        )

    # Watchouts table
    watchout_rows = ""
    for i, r in enumerate(watchouts.rows, 1):
        flag_chips = " ".join(
            f'<span style="display:inline-block;padding:1px 5px;border-radius:4px;'
            f'font-size:10px;background:{("#FEE2E2" if f.severity == "high" else "#FEF3C7" if f.severity == "medium" else "#F3F4F6")};'
            f'color:{("#DC2626" if f.severity == "high" else "#D97706" if f.severity == "medium" else "#6B7280")}">'
            f'{e(f.label)}</span>'
            for f in r.flags[:3]
        )
        watchout_rows += (
            f'<tr style="border-bottom:1px solid #F3F4F6">'
            f'<td style="padding:6px 8px;color:#9CA3AF">{i}</td>'
            f'<td style="padding:6px 8px"><strong>{e(r.row.ticker)}</strong><br>'
            f'<span style="font-size:11px;color:#9CA3AF">{e(display_name(r.row.ticker))}</span></td>'
            f'<td style="padding:6px 8px;text-align:right">{_money(r.row.price)}</td>'
            f'<td style="padding:6px 8px;text-align:right;font-weight:600;color:#F6465D">'
            f'{r.risk_score:.0f}</td>'
            f'<td style="padding:6px 8px">{flag_chips}</td>'
            f'</tr>'
        )

    # Across the sectors — strongest affordable setup in each
    sector_rows = ""
    for r in (sector_best or []):
        echo_cell = "-"
        if r.echo:
            echo_cell = (f'{r.echo.n} &rarr; {_chg(r.echo.median_fwd_pct)} med, '
                         f'worst {_chg(r.echo.worst_pct)}')
        knife = ' <span style="color:#F6465D;font-weight:600">[knife]</span>' if r.falling_knife else ""
        sector_rows += (
            f'<tr style="border-bottom:1px solid #F3F4F6">'
            f'<td style="padding:6px 8px;font-size:12px;color:#6B7280">{e(r.row.sector)}</td>'
            f'<td style="padding:6px 8px"><strong>{e(r.row.ticker)}</strong>{knife}</td>'
            f'<td style="padding:6px 8px;text-align:right">{_money(r.row.price)}</td>'
            f'<td style="padding:6px 8px;text-align:right;color:#F6465D">-{r.depth_pct:.0f}%</td>'
            f'<td style="padding:6px 8px;text-align:center;font-weight:600">{r.entry_score:.0f}</td>'
            f'<td style="padding:6px 8px;font-size:12px">{echo_cell}</td>'
            f'</tr>'
        )
    sector_html = ""
    if sector_rows:
        sector_html = (
            '<h3 style="font-size:13px;font-weight:600;margin:20px 0 4px">'
            'Across the sectors — the strongest affordable setup in each</h3>'
            '<table width="100%" cellpadding="0" cellspacing="0" '
            'style="font-size:13px;border-collapse:collapse">'
            '<tr style="background:#F9FAFB;font-size:11px;text-transform:uppercase;color:#9CA3AF">'
            '<th style="padding:4px 8px;text-align:left">Sector</th>'
            '<th style="padding:4px 8px;text-align:left">Ticker</th>'
            '<th style="padding:4px 8px;text-align:right">Price</th>'
            '<th style="padding:4px 8px;text-align:right">Dip</th>'
            '<th style="padding:4px 8px;text-align:center">Score</th>'
            '<th style="padding:4px 8px;text-align:left">Past dips</th>'
            f'</tr>{sector_rows}</table>'
        )

    # Flags explained — a legend for every label used anywhere above
    flag_defs = ""
    for code in _flags_in_play(radar, watchouts, sector_best):
        g = GLOSSARY[code]
        chip_bg = "#FEE2E2" if g["kind"] == "risk" else "#DCFCE7"
        chip_fg = "#DC2626" if g["kind"] == "risk" else "#15803D"
        flag_defs += (
            f'<div style="padding:8px 0;border-bottom:1px solid #F3F4F6;font-size:13px">'
            f'<span style="display:inline-block;padding:1px 6px;border-radius:4px;'
            f'font-size:11px;background:{chip_bg};color:{chip_fg};font-weight:600">'
            f'{e(g["label"])}</span> '
            f'<span style="font-size:11px;color:#9CA3AF;text-transform:uppercase">'
            f'{e(g["kind"])}</span>'
            f'<div style="margin-top:3px;color:#374151">{e(g["meaning"])}</div>'
            + (f'<div style="margin-top:2px;font-size:12px;color:#6B7280;font-style:italic">'
               f'Think of it like: {e(g["analogy"])}</div>' if g.get("analogy") else "")
            + f'<div style="margin-top:2px;font-size:12px;color:#6B7280">'
            f'What vets do: {e(g["vets"])}</div>'
            f'</div>'
        )
    flags_html = ""
    if flag_defs:
        flags_html = (
            '<h2 style="font-size:14px;text-transform:uppercase;letter-spacing:0.05em;'
            'color:#6B7280;margin:24px 0 8px;border-bottom:1px solid #E5E7EB;'
            'padding-bottom:4px">Flags explained</h2>'
            '<div style="font-size:12px;color:#9CA3AF;margin-bottom:4px">'
            'Every label used above, and the pattern behind it.</div>'
            f'{flag_defs}'
        )

    # Movers
    gainers_html = ", ".join(
        f'<strong>{e(r.ticker)}</strong> {_chg_html(r.change_pct)}' for r in gainers)
    losers_html = ", ".join(
        f'<strong>{e(r.ticker)}</strong> {_chg_html(r.change_pct)}' for r in losers)

    # Your watchlist — the cast (role labels + live numbers; the dated stories
    # stay in the app so the email never reprints frozen numbers as if fresh).
    cast_html = ""
    if basket is not None and basket.members:
        cast_rows = ""
        for m in basket.members:
            price = _money(m.price) if m.price is not None else "-"
            chg = _chg_html(m.change_pct) if m.change_pct is not None else '<span style="color:#8B929C">-</span>'
            role = e(m.role) + ("" if m.measurable else
                                ' <span style="color:#9CA3AF;font-size:11px">(too little history to measure)</span>')
            cast_rows += (
                f'<tr style="border-bottom:1px solid #F3F4F6">'
                f'<td style="padding:6px 8px"><strong>{e(m.ticker)}</strong></td>'
                f'<td style="padding:6px 8px;text-align:right">{price}</td>'
                f'<td style="padding:6px 8px;text-align:right">{chg}</td>'
                f'<td style="padding:6px 8px;font-size:12px;color:#4B5563">{role}</td>'
                f'</tr>'
            )
        u = _umbrella_correlation(basket)
        corr_line = ""
        if u is not None:
            names = "/".join(m.ticker for m in basket.members if m.group == "umbrella")
            corr_line = (f'<div style="font-size:12px;color:#6B7280;margin-top:6px">'
                         f'The umbrellas moved as one again: {e(names)} correlation '
                         f'{u[0]:.2f}-{u[1]:.2f} over the last six months.</div>')
        law = _law_of_the_day(basket, overview.as_of)
        law_line = ""
        if law:
            law_line = (f'<div style="font-size:13px;color:#4B5563;margin-top:6px">'
                        f'<strong>Today&#39;s law:</strong> {e(law)}</div>')
        cast_html = (
            '<h3 style="font-size:13px;font-weight:600;margin:20px 0 4px">'
            'Your watchlist — the cast</h3>'
            '<table width="100%" cellpadding="0" cellspacing="0" '
            'style="font-size:13px;border-collapse:collapse">'
            '<tr style="background:#F9FAFB;font-size:11px;text-transform:uppercase;color:#9CA3AF">'
            '<th style="padding:4px 8px;text-align:left">Ticker</th>'
            '<th style="padding:4px 8px;text-align:right">Price</th>'
            '<th style="padding:4px 8px;text-align:right">Day</th>'
            '<th style="padding:4px 8px;text-align:left">Role</th>'
            f'</tr>{cast_rows}</table>{corr_line}{law_line}'
        )

    # Since yesterday on your watchlist — the what-changed feed.
    events_html = ""
    if basket is not None and basket.events:
        rows = ""
        for ev in basket.events[:6]:
            color = ("#22C989" if ev.tone == "constructive"
                     else "#F6465D" if ev.tone == "caution" else "#6B7280")
            rows += (
                f'<div style="padding:6px 0;border-bottom:1px solid #F3F4F6">'
                f'<div style="font-size:13px;font-weight:600;color:{color}">{e(ev.headline)}</div>'
                f'<div style="font-size:12px;color:#4B5563;margin-top:2px">{e(ev.detail)}</div>'
                f'</div>'
            )
        events_html = (
            '<h3 style="font-size:13px;font-weight:600;margin:20px 0 4px">'
            'Since yesterday on your watchlist</h3>' + rows
        )

    cal_rows = ""
    for ev_date, ev_label in _upcoming_events(cal):
        days_out = (ev_date - dt.date.today()).days
        when = "today" if days_out == 0 else "tomorrow" if days_out == 1 else f"in {days_out}d"
        cal_rows += (
            f'<tr>'
            f'<td style="padding:4px 8px;font-size:12px;white-space:nowrap">'
            f'{ev_date.strftime("%a %b %d")}</td>'
            f'<td style="padding:4px 8px;font-size:12px">{e(ev_label)}</td>'
            f'<td style="padding:4px 8px;font-size:11px;color:#9CA3AF;text-align:right">{when}</td>'
            f'</tr>')

    return f"""\
<div style="max-width:600px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#111827;line-height:1.5">

<!-- Header -->
<table width="100%" cellpadding="0" cellspacing="0" style="border-bottom:2px solid #7C6BFF;margin-bottom:16px">
<tr>
<td style="padding:16px 0">
  <span style="display:inline-block;width:28px;height:28px;border-radius:8px;background:linear-gradient(135deg,#7C6BFF,#4A3FA8);color:#fff;text-align:center;line-height:28px;font-weight:700;font-size:14px;vertical-align:middle">S</span>
  <span style="font-size:18px;font-weight:600;vertical-align:middle;margin-left:8px">Stocky Daily Digest</span>
</td>
<td style="padding:16px 0;text-align:right;font-size:13px;color:#6B7280">
  {stamp}
</td>
</tr>
</table>

<!-- § AT A GLANCE -->
<h2 style="font-size:14px;text-transform:uppercase;letter-spacing:0.05em;color:#6B7280;margin:20px 0 8px;border-bottom:1px solid #E5E7EB;padding-bottom:4px">
  At a glance
</h2>

<table width="100%" cellpadding="0" cellspacing="0"><tr>{tiles_html}</tr></table>
{breadth_html}
{readings_html}
{setup_html}
{watchout_html}

<!-- § THE DETAILS -->
<h2 style="font-size:14px;text-transform:uppercase;letter-spacing:0.05em;color:#6B7280;margin:24px 0 8px;border-bottom:1px solid #E5E7EB;padding-bottom:4px">
  The details
</h2>

<h3 style="font-size:13px;font-weight:600;margin:16px 0 4px">Entry Radar — top 5 pullback setups (budget &le; $200)</h3>
<table width="100%" cellpadding="0" cellspacing="0" style="font-size:13px;border-collapse:collapse">
<tr style="background:#F9FAFB;font-size:11px;text-transform:uppercase;color:#9CA3AF">
  <th style="padding:4px 8px;text-align:left">#</th>
  <th style="padding:4px 8px;text-align:left">Ticker</th>
  <th style="padding:4px 8px;text-align:right">Price</th>
  <th style="padding:4px 8px;text-align:right">Dip</th>
  <th style="padding:4px 8px;text-align:center">Score</th>
  <th style="padding:4px 8px;text-align:left">Past dips</th>
  <th style="padding:4px 8px;text-align:left">Flags</th>
</tr>
{radar_rows}
</table>

{sector_html}

<h3 style="font-size:13px;font-weight:600;margin:20px 0 4px">Watch-outs — top 5 risk-heavy names</h3>
<table width="100%" cellpadding="0" cellspacing="0" style="font-size:13px;border-collapse:collapse">
<tr style="background:#F9FAFB;font-size:11px;text-transform:uppercase;color:#9CA3AF">
  <th style="padding:4px 8px;text-align:left">#</th>
  <th style="padding:4px 8px;text-align:left">Ticker</th>
  <th style="padding:4px 8px;text-align:right">Price</th>
  <th style="padding:4px 8px;text-align:right">Risk</th>
  <th style="padding:4px 8px;text-align:left">Hazards</th>
</tr>
{watchout_rows}
</table>

{cast_html}

{events_html}

<h3 style="font-size:13px;font-weight:600;margin:20px 0 4px">Today's movers</h3>
<div style="font-size:13px;padding:4px 0">
  <strong style="color:#22C989">Gainers:</strong> {gainers_html}<br>
  <strong style="color:#F6465D">Losers:</strong> {losers_html}
</div>

{"<h3 style='font-size:13px;font-weight:600;margin:20px 0 4px'>This week</h3><table width='100%' cellpadding='0' cellspacing='0' style='border-collapse:collapse'>" + cal_rows + "</table>" if cal_rows else ""}

{flags_html}

<!-- Footer -->
<div style="margin-top:24px;padding:12px;border-top:2px solid #E5E7EB;font-size:11px;color:#9CA3AF;line-height:1.6">
  Every number above is computed from {src} as of {as_of};
  no text in this email is model-generated. Educational, not advice.
</div>

</div>"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Building digest …")
    overview, radar, sector_best, watchouts, gainers, losers, cal, basket = _gather()

    html = build_html(overview, radar, watchouts, gainers, losers, cal,
                      sector_best=sector_best, basket=basket)
    txt = build_text(overview, radar, watchouts, gainers, losers, cal,
                     sector_best=sector_best, basket=basket)

    html_path = out_dir / "digest.html"
    txt_path = out_dir / "digest.txt"
    html_path.write_text(html, encoding="utf-8")
    txt_path.write_text(txt, encoding="utf-8")
    print(f"Wrote {html_path} ({html_path.stat().st_size:,} bytes)")
    print(f"Wrote {txt_path} ({txt_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
