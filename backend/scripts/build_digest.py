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
from app.services import analytics, insights  # noqa: E402
from app.services.calendar import build_calendar  # noqa: E402
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
    watchouts = analytics.build_watchouts(DEFAULT_BUDGET, 5)
    gainers = analytics.build_movers("gainers", DEFAULT_BUDGET, 3)
    losers = analytics.build_movers("losers", DEFAULT_BUDGET, 3)
    cal = build_calendar()
    return overview, radar, watchouts, gainers, losers, cal


# ── Plain text ───────────────────────────────────────────────────────────────

def build_text(overview, radar, watchouts, gainers, losers, cal) -> str:
    lines: list[str] = []
    as_of = overview.as_of.strftime("%b %d, %Y").replace(" 0", " ")
    lines.append(f"STOCKY DAILY DIGEST — {as_of}")
    lines.append("=" * 50)

    # § At a glance
    lines.append("")
    lines.append("AT A GLANCE")
    lines.append("-" * 30)
    for t in overview.tiles:
        val = _money(t.value) if t.unit == "usd" else (
            f"{t.value:.2f}%" if t.unit == "percent" else f"{t.value:.2f}")
        lines.append(f"  {t.label}: {val} ({_chg(t.change_pct)})")

    b = overview.breadth
    lines.append(f"  Breadth: {b.pct_above_ma50:.0f}% above 50-day, "
                 f"{b.advancers} adv / {b.decliners} dec")

    for r in overview.readings:
        lines.append(f"  {r.headline}")

    if radar.rows:
        top = radar.rows[0]
        echo_bit = ""
        if top.echo:
            echo_bit = (f" | {top.echo.n} similar dips -> "
                        f"median {_chg(top.echo.median_fwd_pct)} next month "
                        f"({_conf_label(top.echo.confidence)} sample)")
        lines.append(f"  #1 setup: {top.row.ticker} at {_money(top.row.price)}, "
                     f"down {top.depth_pct:.0f}%, score {top.entry_score:.0f}{echo_bit}")

    if watchouts.rows:
        wo = watchouts.rows[0]
        flag_names = ", ".join(f.label for f in wo.flags[:3])
        lines.append(f"  #1 watch-out: {wo.row.ticker} — {flag_names} "
                     f"(risk score {wo.risk_score:.0f})")

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

    lines.append("")
    lines.append("Watch-outs — top 5 risk-heavy names:")
    for i, r in enumerate(watchouts.rows, 1):
        flags = ", ".join(f"{f.label} ({f.severity})" for f in r.flags[:3])
        lines.append(f"  {i}. {r.row.ticker} ({display_name(r.row.ticker)}) "
                     f"{_money(r.row.price)} | risk {r.risk_score:.0f} | {flags}")

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

    lines.append("")
    lines.append("-" * 50)
    lines.append(f"Every number above is computed from Yahoo Finance end-of-day "
                 f"data as of {as_of}; no text in this email is model-generated. "
                 f"Educational, not advice.")
    return "\n".join(lines)


# ── HTML ─────────────────────────────────────────────────────────────────────

def build_html(overview, radar, watchouts, gainers, losers, cal) -> str:
    as_of = overview.as_of.strftime("%b %d, %Y").replace(" 0", " ")
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

    # Readings (at a glance)
    readings_html = ""
    for r in overview.readings:
        tone_color = "#22C989" if r.tone == "constructive" else "#F6465D" if r.tone == "caution" else "#6B7280"
        readings_html += (
            f'<div style="padding:6px 0;font-size:13px;border-bottom:1px solid #F3F4F6">'
            f'<span style="color:{tone_color};font-weight:600">{e(r.headline)}</span>'
            f'</div>'
        )

    # Top setup one-liner
    setup_html = ""
    if radar.rows:
        top = radar.rows[0]
        echo_bit = ""
        if top.echo:
            echo_bit = (f' — {top.echo.n} similar dips &rarr; '
                        f'median {_chg(top.echo.median_fwd_pct)} next month '
                        f'({_conf_label(top.echo.confidence)} sample)')
        setup_html = (
            f'<div style="padding:8px 12px;background:#F0FDF4;border-radius:6px;'
            f'border:1px solid #BBF7D0;font-size:13px;margin:8px 0">'
            f'<strong>#{1} setup:</strong> {e(top.row.ticker)} at {_money(top.row.price)}, '
            f'down {top.depth_pct:.0f}%, score {top.entry_score:.0f}{echo_bit}'
            f'</div>'
        )

    # Top watchout one-liner
    watchout_html = ""
    if watchouts.rows:
        wo = watchouts.rows[0]
        flag_names = ", ".join(f.label for f in wo.flags[:3])
        watchout_html = (
            f'<div style="padding:8px 12px;background:#FEF2F2;border-radius:6px;'
            f'border:1px solid #FECACA;font-size:13px;margin:8px 0">'
            f'<strong>#{1} watch-out:</strong> {e(wo.row.ticker)} — {e(flag_names)} '
            f'(risk score {wo.risk_score:.0f})'
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

    # Movers
    gainers_html = ", ".join(
        f'<strong>{e(r.ticker)}</strong> {_chg_html(r.change_pct)}' for r in gainers)
    losers_html = ", ".join(
        f'<strong>{e(r.ticker)}</strong> {_chg_html(r.change_pct)}' for r in losers)

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
  {as_of} close
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

<h3 style="font-size:13px;font-weight:600;margin:20px 0 4px">Today's movers</h3>
<div style="font-size:13px;padding:4px 0">
  <strong style="color:#22C989">Gainers:</strong> {gainers_html}<br>
  <strong style="color:#F6465D">Losers:</strong> {losers_html}
</div>

{"<h3 style='font-size:13px;font-weight:600;margin:20px 0 4px'>This week</h3><table width='100%' cellpadding='0' cellspacing='0' style='border-collapse:collapse'>" + cal_rows + "</table>" if cal_rows else ""}

<!-- Footer -->
<div style="margin-top:24px;padding:12px;border-top:2px solid #E5E7EB;font-size:11px;color:#9CA3AF;line-height:1.6">
  Every number above is computed from Yahoo Finance end-of-day data as of {as_of};
  no text in this email is model-generated. Educational, not advice.
</div>

</div>"""


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Building digest …")
    overview, radar, watchouts, gainers, losers, cal = _gather()

    html = build_html(overview, radar, watchouts, gainers, losers, cal)
    txt = build_text(overview, radar, watchouts, gainers, losers, cal)

    html_path = out_dir / "digest.html"
    txt_path = out_dir / "digest.txt"
    html_path.write_text(html, encoding="utf-8")
    txt_path.write_text(txt, encoding="utf-8")
    print(f"Wrote {html_path} ({html_path.stat().st_size:,} bytes)")
    print(f"Wrote {txt_path} ({txt_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
