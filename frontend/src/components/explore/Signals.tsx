// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import Link from "next/link";
import { TrendingDown, TrendingUp } from "lucide-react";
import type { SignalsResponse, StockRow } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { Term } from "@/components/ui/Term";
import { StockRowItem } from "@/components/stocks/StockRowItem";

function SignalColumn({
  title,
  termKey,
  blurb,
  rows,
  tone,
  extra,
}: {
  title: string;
  termKey: string;
  blurb: React.ReactNode;
  rows: StockRow[];
  tone: "up" | "down";
  extra?: (r: StockRow) => React.ReactNode;
}) {
  const Icon = tone === "up" ? TrendingUp : TrendingDown;
  return (
    <div className="card overflow-hidden">
      <div className={`flex items-center gap-2 border-b border-hair px-4 py-3 ${tone === "up" ? "text-up" : "text-down"}`}>
        <Icon className="h-4 w-4" />
        <h3 className="text-sm font-semibold text-ink">
          <Term k={termKey}>{title}</Term>
        </h3>
        <span className="tnum ml-auto text-xs text-faint">{rows.length}</span>
      </div>
      <div className="px-4 py-2 text-xs text-faint">{blurb}</div>
      <div className="max-h-[420px] overflow-y-auto p-1.5">
        {rows.length === 0 ? (
          <div className="px-3 py-6 text-center text-sm text-faint">None right now.</div>
        ) : (
          rows.map((r) => (
            <div key={r.ticker} className="flex items-center">
              <div className="min-w-0 flex-1">
                <StockRowItem row={r} />
              </div>
              {extra && <div className="shrink-0 pr-2 text-right">{extra(r)}</div>}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export function Signals({ data }: { data: SignalsResponse }) {
  return (
    <div className="grid gap-3 lg:grid-cols-2">
      <SignalColumn
        title="Golden crosses"
        termKey="golden_cross"
        tone="up"
        blurb="50-day average just crossed above the 200-day — a classic bullish trend flag. Remember: it lags."
        rows={data.golden_crosses}
        extra={(r) => (
          <span className="tnum text-[10px] text-faint">
            {r.cross_date ? fmtDate(r.cross_date) : ""}
          </span>
        )}
      />
      <SignalColumn
        title="Death crosses"
        termKey="death_cross"
        tone="down"
        blurb="50-day crossed below the 200-day — bearish, but famous for firing near bottoms."
        rows={data.death_crosses}
        extra={(r) => (
          <span className="tnum text-[10px] text-faint">
            {r.cross_date ? fmtDate(r.cross_date) : ""}
          </span>
        )}
      />
      <SignalColumn
        title="Overbought (RSI ≥ 70)"
        termKey="rsi"
        tone="up"
        blurb="Stretched to the upside. A caution flag — strong stocks can stay overbought for weeks."
        rows={data.overbought}
        extra={(r) => <span className="tnum text-xs text-ink">{r.rsi14?.toFixed(0)}</span>}
      />
      <SignalColumn
        title="Oversold (RSI ≤ 30)"
        termKey="rsi"
        tone="down"
        blurb={
          <>
            Stretched to the downside. Oversold says <i>stretched</i> — the{" "}
            <Link href="/radar" className="text-accent hover:underline">
              Entry Radar
            </Link>{" "}
            adds trend context and what historically happened next.
          </>
        }
        rows={data.oversold}
        extra={(r) => <span className="tnum text-xs text-ink">{r.rsi14?.toFixed(0)}</span>}
      />
    </div>
  );
}
