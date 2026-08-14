"use client";

import { AlertTriangle } from "lucide-react";
import type { RadarResponse, RadarRow } from "@/lib/types";
import { fmtPct } from "@/lib/format";
import { Term } from "@/components/ui/Term";
import { ScoreBadge } from "@/components/ui/primitives";
import { StockRowItem } from "@/components/stocks/StockRowItem";

/** Tiny horizontal bar showing pullback depth (capped at 30% for scale). */
function DepthBar({ depth }: { depth: number }) {
  const pct = Math.min(100, (depth / 30) * 100);
  return (
    <div className="w-16">
      <div className="tnum text-right text-xs font-semibold text-down">
        −{depth.toFixed(1)}%
      </div>
      <div className="mt-0.5 h-1 rounded-full bg-elevated">
        <div
          className="h-1 rounded-full bg-down/70"
          style={{ width: `${Math.max(6, pct)}%` }}
        />
      </div>
    </div>
  );
}

/** "What happened after similar dips" — base rates with N and worst case. */
export function EchoChip({ r, compact = false }: { r: RadarRow; compact?: boolean }) {
  if (!r.echo) {
    return (
      <span className="text-[10px] text-faint">
        <Term k="sample_size">not enough history</Term>
      </span>
    );
  }
  const e = r.echo;
  const ups = Math.round(e.win_rate * e.n);
  return (
    <div className={`text-right ${compact ? "text-[10px]" : "text-xs"}`}>
      <div className="text-muted">
        <span className="tnum text-ink">{e.n}</span> similar dips →{" "}
        <span className={`tnum font-semibold ${e.median_fwd_pct >= 0 ? "text-up" : "text-down"}`}>
          {fmtPct(e.median_fwd_pct)}
        </span>{" "}
        <Term k="forward_return">next mo</Term>
      </div>
      <div className="text-[10px] text-faint">
        <span className="tnum">{ups}↑ {e.n - ups}↓</span> · worst{" "}
        <span className="tnum text-down">{fmtPct(e.worst_pct)}</span>
      </div>
    </div>
  );
}

export function KnifeChip() {
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-down/40 bg-down/10 px-1.5 py-0.5 text-[10px] font-medium text-down">
      <AlertTriangle className="h-3 w-3" />
      <Term k="falling_knife">knife</Term>
    </span>
  );
}

/** One radar row: the standard stock row + depth, entry score, echo, knife. */
export function RadarRowItem({ r, rank }: { r: RadarRow; rank?: number }) {
  return (
    <div className="flex items-center gap-3">
      <div className="min-w-0 flex-1">
        <StockRowItem row={r.row} rank={rank} />
      </div>
      <div className="hidden shrink-0 md:block">
        <DepthBar depth={r.depth_pct} />
      </div>
      <div className="hidden w-44 shrink-0 lg:block">
        <EchoChip r={r} />
      </div>
      <div className="flex shrink-0 items-center gap-1.5 pr-2">
        {r.falling_knife && <KnifeChip />}
        <ScoreBadge score={r.entry_score} />
      </div>
    </div>
  );
}

/** The formula, spelled out — nothing hidden, nothing promised. */
export function MethodCard({ data }: { data: RadarResponse }) {
  const w = data.weights;
  return (
    <div className="card p-4 text-xs leading-relaxed text-muted">
      <h3 className="mb-1.5 text-sm font-semibold text-ink">
        <Term k="entry_score">How this list is ranked</Term>
      </h3>
      <p>
        Every affordable, liquid stock trading ≥5% below its {data.lookback.toUpperCase()}{" "}
        high gets an entry score:{" "}
        <span className="text-ink">
          Depth {Math.round((w.depth ?? 0) * 100)}%
        </span>{" "}
        (how unusual this <Term k="pullback">pullback</Term> is vs the stock&apos;s own
        history) ·{" "}
        <span className="text-ink">Trend {Math.round((w.trend ?? 0) * 100)}%</span>{" "}
        (above its 200-day average, i.e. not a{" "}
        <Term k="falling_knife">falling knife</Term>) ·{" "}
        <span className="text-ink">RSI {Math.round((w.rsi ?? 0) * 100)}%</span> (how
        washed-out it is) ·{" "}
        <span className="text-ink">Quality {Math.round((w.quality ?? 0) * 100)}%</span>{" "}
        (1-year return rank — dips in strong stocks first).
      </p>
      <p className="mt-2">
        The &quot;similar dips&quot; column is a <Term k="base_rate">base rate</Term>:
        we find every past episode with the same depth bucket and trend state, then
        measure the actual <Term k="forward_return">forward return</Term> over the
        next {data.horizon_days} sessions — with the{" "}
        <Term k="sample_size">sample size</Term>, <Term k="win_rate">win rate</Term> and
        worst case always shown.
      </p>
      <p className="mt-2 font-medium text-ink">
        These are setups worth studying, ranked transparently — not buy signals, and
        never a prediction. Past behavior does not guarantee anything.
      </p>
    </div>
  );
}
