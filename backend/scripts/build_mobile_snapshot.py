"""Render a self-contained, phone-first HTML snapshot of the Stocky dashboard.

Usage (backend must be running on :8000):

    python scripts/build_mobile_snapshot.py [output.html]

The result is a single static file — publish it anywhere (e.g. as a Claude
artifact) to view the day's dashboard on a phone with the laptop off.
"""

import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
API = "http://127.0.0.1:8000"


def load(path):
    with urllib.request.urlopen(f"{API}{path}", timeout=60) as resp:
        return json.load(resp)


overview = load("/overview")
sectors = load("/sectors?budget=200")
gainers = load("/movers?type=gainers&budget=200&limit=10")
losers = load("/movers?type=losers&budget=200&limit=10")
signals = load("/signals?budget=200")
pulse = load("/pulse")

_gid = 0


def spark(points, w=88, h=26, cls=None):
    """Tiny area sparkline, colored by net direction (or forced via cls)."""
    global _gid
    if not points or len(points) < 2:
        return f'<svg width="{w}" height="{h}"></svg>'
    _gid += 1
    lo, hi = min(points), max(points)
    span = (hi - lo) or 1.0
    step = w / (len(points) - 1)
    pad = 2
    uh = h - pad * 2
    pts = [(i * step, pad + (1 - (v - lo) / span) * uh) for i, v in enumerate(points)]
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    up = points[-1] >= points[0]
    color = {"up": "#22C989", "down": "#F6465D", "accent": "#7C6BFF"}.get(
        cls or ("up" if up else "down")
    )
    return (
        f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" preserveAspectRatio="none" aria-hidden="true">'
        f'<defs><linearGradient id="g{_gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{color}" stop-opacity=".28"/>'
        f'<stop offset="100%" stop-color="{color}" stop-opacity="0"/></linearGradient></defs>'
        f'<path d="{d} L{w},{h} L0,{h} Z" fill="url(#g{_gid})"/>'
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="1.5" '
        f'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )


def chg(v, arrow=True):
    if v is None:
        return '<span class="num muted">—</span>'
    cls = "pos" if v > 0 else "neg" if v < 0 else "muted"
    a = ("▲ " if v > 0 else "▼ " if v < 0 else "") if arrow else ""
    return f'<span class="num {cls}">{a}{v:+.2f}%</span>'


def money(v):
    return f"${v:,.2f}" if v < 1000 else f"${v:,.0f}"


def score_chip(s):
    if s is None:
        return ""
    cls = "chip-hi" if s >= 80 else "chip-mid" if s >= 60 else "chip-low"
    return f'<span class="chip {cls} num">{s:.0f}</span>'


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---------------------------------------------------------------- header bits
as_of = dt.date.fromisoformat(overview["as_of"]).strftime("%b %-d, %Y") \
    if hasattr(dt.date.today(), "x") else dt.date.fromisoformat(overview["as_of"]).strftime("%b %d, %Y").replace(" 0", " ")
captured = dt.datetime.now().strftime("%I:%M %p").lstrip("0")

# ---------------------------------------------------------------- index tiles
tile_html = ""
for t in overview["tiles"]:
    val = money(t["value"]) if t["unit"] == "usd" else (
        f"{t['value']:.2f}%" if t["unit"] == "percent" else f"{t['value']:.2f}")
    tile_html += f"""
    <div class="card tile">
      <div class="tile-top"><span class="lbl">{esc(t['label'])}</span>{chg(t['change_pct'])}</div>
      <div class="tile-val num">{val}</div>
      <div class="tile-spark">{spark(t['spark'], w=200, h=30)}</div>
    </div>"""

b = overview["breadth"]
read = "Broad" if b["pct_above_ma50"] >= 55 else "Mixed" if b["pct_above_ma50"] >= 45 else "Narrow"
breadth_html = f"""
  <div class="card breadth">
    <div class="bcell"><span class="lbl">Above 50-day</span><span class="num {'pos' if b['pct_above_ma50']>=50 else 'neg'}">{b['pct_above_ma50']}%</span></div>
    <div class="bcell"><span class="lbl">Above 200-day</span><span class="num {'pos' if b['pct_above_ma200']>=50 else 'neg'}">{b['pct_above_ma200']}%</span></div>
    <div class="bcell"><span class="lbl">Adv / Dec</span><span class="num {'pos' if b['advancers']>=b['decliners'] else 'neg'}">{b['advancers']} / {b['decliners']}</span></div>
    <div class="bcell"><span class="lbl">New highs</span><span class="num pos">{b['new_highs_52w']}</span></div>
    <div class="bcell"><span class="lbl">New lows</span><span class="num {'neg' if b['new_lows_52w'] else 'muted'}">{b['new_lows_52w']}</span></div>
    <div class="bcell"><span class="lbl">Read</span><span class="num">{read}</span></div>
  </div>"""

# ---------------------------------------------------------------- sectors
sector_html = ""
for p in sectors["sectors"]:
    rows = ""
    for i, r in enumerate(p["top"][:5], 1):
        rows += f"""
        <div class="row">
          <span class="rank num">{i}</span>
          <div class="ident"><div class="tick">{esc(r['ticker'])}</div><div class="name">{esc(r['name'])}</div></div>
          <div class="rspark">{spark(r['spark'])}</div>
          {score_chip(r['score'])}
          <div class="rprice"><div class="num price">{money(r['price'])}</div>{chg(r['change_pct'], arrow=False)}</div>
        </div>"""
    if not rows:
        rows = '<div class="empty">Nothing under $200 here — a pricier sector.</div>'
    ec = p["etf_change_pct"]
    sector_html += f"""
    <details class="card sector">
      <summary>
        <span class="sname">{esc(p['label'])}</span>
        {chg(ec, arrow=False)}
        <span class="scount num">{p['members_affordable']}<span class="dim">/{p['members_total']}</span></span>
        <span class="caret" aria-hidden="true">▾</span>
      </summary>
      <div class="rows">{rows}</div>
    </details>"""

# ---------------------------------------------------------------- movers
def mover_rows(rows):
    out = ""
    for i, r in enumerate(rows, 1):
        out += f"""
        <div class="row">
          <span class="rank num">{i}</span>
          <div class="ident"><div class="tick">{esc(r['ticker'])}</div><div class="name">{esc(r['name'])}</div></div>
          <div class="rprice"><div class="num price">{money(r['price'])}</div>{chg(r['change_pct'], arrow=False)}</div>
        </div>"""
    return out


movers_html = f"""
  <div class="card">
    <div class="tabs" role="tablist">
      <button class="tab active" data-t="g" role="tab" aria-selected="true">Gainers</button>
      <button class="tab" data-t="l" role="tab" aria-selected="false">Losers</button>
    </div>
    <div class="rows pane" id="pane-g">{mover_rows(gainers)}</div>
    <div class="rows pane hidden" id="pane-l">{mover_rows(losers)}</div>
  </div>"""

# ---------------------------------------------------------------- signals
def sig_card(title, rows, tone, note):
    chips = "".join(
        f'<span class="tchip num">{esc(r["ticker"])}</span>' for r in rows[:4]
    ) or '<span class="dim">none</span>'
    return f"""
    <div class="card sig">
      <div class="sig-top"><span class="sig-title {tone}">{title}</span><span class="num sig-n">{len(rows)}</span></div>
      <div class="sig-chips">{chips}</div>
      <div class="sig-note">{note}</div>
    </div>"""


signals_html = (
    sig_card("Golden crosses", signals["golden_crosses"], "pos", "50-day crossed above 200-day — bullish, but it lags.")
    + sig_card("Death crosses", signals["death_crosses"], "neg", "50-day below 200-day — often fires near bottoms.")
    + sig_card("Overbought", signals["overbought"], "pos", "RSI ≥ 70. Stretched — strong stocks can stay here.")
    + sig_card("Oversold", signals["oversold"], "neg", "RSI ≤ 30. Washed out — or still falling.")
)

# ---------------------------------------------------------------- watchlist
watch_html = ""
for c in pulse["watchlist"]:
    watch_html += f"""
    <div class="row">
      <div class="ident"><div class="tick">{esc(c['ticker'])}</div><div class="name">{esc(c['name'])}</div></div>
      <div class="rspark">{spark(c['sparkline'])}</div>
      <div class="rprice"><div class="num price">{money(c['price'])}</div>{chg(c['change_pct'], arrow=False)}</div>
    </div>"""

# ---------------------------------------------------------------- page
CSS = """
:root{--bg:#0A0B0D;--panel:#0F1114;--elev:#15181D;--ink:#E7E9EC;--muted:#8B929C;
--faint:#5A616B;--up:#22C989;--down:#F6465D;--accent:#7C6BFF;--hair:rgba(255,255,255,.07)}
*{box-sizing:border-box;margin:0}
body{background:radial-gradient(700px 340px at 50% -8%,rgba(124,107,255,.14),transparent 60%),var(--bg);
color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
-webkit-font-smoothing:antialiased;padding:0 0 48px}
.wrap{max-width:28rem;margin:0 auto;padding:0 14px}
.num{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.pos{color:var(--up)}.neg{color:var(--down)}.muted{color:var(--muted)}.dim{color:var(--faint)}
.lbl{font-size:10px;text-transform:uppercase;letter-spacing:.08em;color:var(--faint)}
header{position:sticky;top:0;z-index:5;background:rgba(10,11,13,.82);backdrop-filter:blur(10px);
border-bottom:1px solid var(--hair);margin-bottom:16px}
.hrow{max-width:28rem;margin:0 auto;padding:12px 14px;display:flex;align-items:center;gap:10px}
.logo{width:26px;height:26px;border-radius:8px;display:grid;place-items:center;font-weight:700;font-size:13px;
color:#fff;background:linear-gradient(135deg,var(--accent),#4A3FA8);box-shadow:0 0 14px rgba(124,107,255,.4)}
.brand{font-weight:600;letter-spacing:-.01em}
.asof{margin-left:auto;text-align:right;font-size:11px;color:var(--muted)}
.asof b{color:var(--ink);font-weight:600}
h2{font-size:12px;text-transform:uppercase;letter-spacing:.09em;color:var(--muted);margin:22px 2px 8px;
display:flex;align-items:baseline;gap:8px}
h2 .sub{text-transform:none;letter-spacing:0;font-size:11px;color:var(--faint);font-weight:400}
.card{background:var(--panel);border:1px solid var(--hair);border-radius:12px;
box-shadow:0 1px 0 0 rgba(255,255,255,.04) inset,0 8px 24px -16px rgba(0,0,0,.7)}
.tile{padding:12px 14px;display:flex;flex-direction:column;gap:6px;margin-bottom:10px}
.tile-top{display:flex;justify-content:space-between;align-items:baseline;font-size:12px}
.tile-val{font-size:22px;font-weight:600}
.tile-spark svg{width:100%;height:30px;display:block}
.breadth{display:grid;grid-template-columns:1fr 1fr 1fr;padding:4px}
.bcell{padding:10px 10px;display:flex;flex-direction:column;gap:3px;font-size:14px}
.sector{margin-bottom:8px;overflow:hidden}
summary{list-style:none;display:flex;align-items:center;gap:10px;padding:12px 14px;cursor:pointer}
summary::-webkit-details-marker{display:none}
summary:focus-visible{outline:2px solid var(--accent);outline-offset:-2px;border-radius:12px}
.sname{font-weight:600;font-size:14px;flex:1}
.scount{font-size:12px;color:var(--muted)}
.caret{color:var(--faint);transition:transform .18s}
details[open] .caret{transform:rotate(180deg)}
.rows{border-top:1px solid var(--hair);padding:4px 6px}
.row{display:flex;align-items:center;gap:10px;padding:8px 8px;border-bottom:1px solid rgba(255,255,255,.04)}
.row:last-child{border-bottom:0}
.rank{width:14px;font-size:11px;color:var(--faint);text-align:right;flex:none}
.ident{flex:1;min-width:0}
.tick{font-weight:600;font-size:14px;letter-spacing:-.01em}
.name{font-size:11px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.rspark{flex:none}.rspark svg{display:block}
.rprice{flex:none;text-align:right;font-size:12px}
.price{font-size:14px;font-weight:600}
.chip{flex:none;min-width:30px;text-align:center;font-size:12px;font-weight:700;
padding:3px 7px;border-radius:7px;border:1px solid}
.chip-hi{color:var(--up);border-color:rgba(34,201,137,.4);background:rgba(34,201,137,.1)}
.chip-mid{color:var(--accent);border-color:rgba(124,107,255,.4);background:rgba(124,107,255,.1)}
.chip-low{color:var(--muted);border-color:var(--hair);background:var(--elev)}
.empty{padding:14px;font-size:13px;color:var(--faint);text-align:center}
.tabs{display:flex;gap:4px;padding:8px;border-bottom:1px solid var(--hair)}
.tab{flex:1;padding:7px;border-radius:8px;border:0;background:transparent;color:var(--muted);
font:600 13px system-ui;cursor:pointer}
.tab.active{background:var(--accent);color:#fff}
.tab:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.hidden{display:none}
.sigs{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.sig{padding:12px}
.sig-top{display:flex;justify-content:space-between;align-items:baseline}
.sig-title{font-size:12px;font-weight:600}
.sig-n{font-size:18px;font-weight:700}
.sig-chips{display:flex;flex-wrap:wrap;gap:4px;margin:8px 0 6px}
.tchip{font-size:11px;padding:2px 7px;border-radius:6px;background:var(--elev);border:1px solid var(--hair)}
.sig-note{font-size:10.5px;color:var(--faint);line-height:1.4}
.note{font-size:11px;color:var(--faint);margin:8px 2px 0}
footer{margin-top:28px;padding:14px;border:1px solid var(--hair);border-radius:12px;
background:rgba(15,17,20,.6);font-size:11.5px;color:var(--muted);line-height:1.5}
footer b{color:var(--ink)}
@media (prefers-reduced-motion:reduce){.caret{transition:none}}
"""

JS = """
document.querySelectorAll('.tab').forEach(function(btn){
  btn.addEventListener('click',function(){
    document.querySelectorAll('.tab').forEach(function(t){
      t.classList.remove('active');t.setAttribute('aria-selected','false')});
    btn.classList.add('active');btn.setAttribute('aria-selected','true');
    document.getElementById('pane-g').classList.toggle('hidden',btn.dataset.t!=='g');
    document.getElementById('pane-l').classList.toggle('hidden',btn.dataset.t!=='l');
  });
});
"""

html = f"""<title>Stocky — Market Snapshot</title>
<style>{CSS}</style>
<header><div class="hrow">
  <div class="logo">S</div><span class="brand">Stocky</span>
  <div class="asof"><b>{as_of}</b> close<br>snapshot · {captured}</div>
</div></header>
<div class="wrap">

  <h2>Market overview <span class="sub">check the weather first</span></h2>
  {tile_html}
  {breadth_html}

  <h2>Sector pulse <span class="sub">top affordable (≤$200), ranked · tap to open</span></h2>
  {sector_html}
  <p class="note">Score = momentum 40 · stability 30 · resilience 20 · liquidity 10, ranked within each sector. A transparent starting point — not a recommendation.</p>

  <h2>Today's movers <span class="sub">under $200</span></h2>
  {movers_html}

  <h2>Trend signals</h2>
  <div class="sigs">{signals_html}</div>

  <h2>Watchlist</h2>
  <div class="card rows">{watch_html}</div>

  <footer>
    <b>Static snapshot</b> — numbers frozen at capture time; ask Claude to refresh this
    page (same link) for current data. End-of-day data via Yahoo Finance.<br><br>
    Educational tool for building market intuition — <b>not financial advice</b>.
    Past performance never guarantees future results.
  </footer>
</div>
<script>{JS}</script>
"""

out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "stocky_snapshot.html"
# Pure-ASCII output (entities for any non-ASCII) → immune to charset guessing.
out.write_bytes(html.encode("ascii", "xmlcharrefreplace"))
print(f"wrote {out} ({out.stat().st_size:,} bytes, ascii-safe)")
