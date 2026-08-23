// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import Link from "next/link";
import { ArrowUpRight, TrendingDown, TrendingUp } from "lucide-react";
import type { StockRow } from "@/lib/types";
import { fmtCompact, fmtCurrency } from "@/lib/format";
import { Sparkline } from "@/components/ui/Sparkline";
import { ChangePct, FactorBars, RangeBar, ScoreBadge } from "@/components/ui/primitives";

/**
 * One clickable stock row → deep dive. Used in sector panels, movers, signals.
 * `rank` shows a position number; `showScore` adds the screener score + factors.
 */
export function StockRowItem({
  row,
  rank,
  showScore = false,
}: {
  row: StockRow;
  rank?: number;
  showScore?: boolean;
}) {
  return (
    <Link
      href={`/stock/${row.ticker}`}
      className="group grid grid-cols-[auto_1fr_auto] items-center gap-3 rounded-lg border border-transparent px-2.5 py-2 transition-colors hover:border-hair hover:bg-elevated/60 sm:grid-cols-[auto_minmax(0,1.4fr)_auto_auto_auto]"
    >
      {/* Rank + identity */}
      <div className="flex items-center gap-2.5">
        {rank !== undefined && (
          <span className="tnum w-5 text-right text-xs text-faint">{rank}</span>
        )}
        <div className="min-w-0">
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-semibold tracking-tight">{row.ticker}</span>
            {row.cross === "golden" && (
              <TrendingUp className="h-3 w-3 text-up" aria-label="golden cross" />
            )}
            {row.cross === "death" && (
              <TrendingDown className="h-3 w-3 text-down" aria-label="death cross" />
            )}
          </div>
          <div className="truncate text-xs text-muted">{row.name}</div>
        </div>
      </div>

      {/* Sparkline + 52w range */}
      <div className="hidden min-w-0 flex-col gap-1 sm:flex">
        <Sparkline data={row.spark} width={140} height={26} className="w-full max-w-[160px]" />
        <RangeBar position={row.range_52w_position} className="max-w-[160px]" />
      </div>

      {/* Score / factors */}
      {showScore ? (
        <div className="hidden items-center gap-2 sm:flex">
          <ScoreBadge score={row.score} />
          <FactorBars factors={row.factors} compact />
        </div>
      ) : (
        <div className="hidden text-right sm:block">
          <div className="text-[10px] uppercase text-faint">Vol/avg</div>
          <div className="tnum text-xs text-muted">{row.volume_ratio.toFixed(1)}×</div>
        </div>
      )}

      {/* Price + change */}
      <div className="text-right">
        <div className="tnum text-sm font-semibold">{fmtCurrency(row.price)}</div>
        <ChangePct value={row.change_pct} className="justify-end text-xs" />
      </div>

      {/* 3-month return + open arrow */}
      <div className="hidden items-center gap-2 text-right sm:flex">
        <div>
          <div className="text-[10px] uppercase text-faint">3M</div>
          <ChangePct value={row.ret_3m} showArrow={false} className="justify-end text-xs" />
        </div>
        <ArrowUpRight className="h-4 w-4 text-faint opacity-0 transition-opacity group-hover:opacity-100" />
      </div>
    </Link>
  );
}

export function DollarVolume({ value }: { value: number }) {
  return <span className="tnum text-muted">${fmtCompact(value)}</span>;
}
