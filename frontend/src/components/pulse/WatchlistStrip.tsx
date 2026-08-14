"use client";

import Link from "next/link";
import { Zap } from "lucide-react";
import type { WatchlistCard } from "@/lib/types";
import { fmtCurrency } from "@/lib/format";
import { Sparkline } from "@/components/ui/Sparkline";
import { ChangePct, RangeBar } from "@/components/ui/primitives";

export function WatchlistStrip({ cards }: { cards: WatchlistCard[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-3">
      {cards.map((c) => (
        <Link
          key={c.ticker}
          href={`/stock/${c.ticker}`}
          className="card group flex flex-col gap-2.5 p-3.5 transition-colors hover:border-white/15"
        >
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-semibold tracking-tight">{c.ticker}</span>
                {c.unusual_volume && <Zap className="h-3 w-3 text-accent" />}
              </div>
              <div className="truncate text-xs text-muted">{c.name}</div>
            </div>
            <div className="text-right">
              <div className="tnum text-sm font-semibold">{fmtCurrency(c.price)}</div>
              <ChangePct value={c.change_pct} className="justify-end text-xs" />
            </div>
          </div>
          <Sparkline data={c.sparkline} width={240} height={34} className="w-full" />
          <RangeBar position={c.range_52w_position} />
        </Link>
      ))}
    </div>
  );
}
