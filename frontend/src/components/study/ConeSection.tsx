// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useState } from "react";
import type { BasketMember } from "@/lib/types";
import { ConePanel } from "./ConePanel";

/** The cone with a member picker — the /watchlist version. Thin-history names are
 *  disabled with the lesson in their tooltip; the panel itself teaches the rest. */
export function ConeSection({ members }: { members: BasketMember[] }) {
  const measurable = members.filter((m) => m.measurable);
  const initial =
    [...measurable].sort((a, b) => b.attention - a.attention)[0]?.ticker ??
    members[0]?.ticker ??
    "VOO";
  const [sel, setSel] = useState(initial);

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1.5">
        {members.map((m) => (
          <button
            key={m.ticker}
            type="button"
            disabled={!m.measurable}
            onClick={() => setSel(m.ticker)}
            title={
              m.measurable
                ? undefined
                : `${m.ticker} has too little history to simulate — a blank past can't be forecast.`
            }
            className={`rounded-md border px-2 py-0.5 text-[11px] font-medium transition-colors ${
              m.ticker === sel
                ? "border-accent/40 bg-accent/10 text-accent"
                : m.measurable
                  ? "border-hair text-muted hover:bg-elevated hover:text-ink"
                  : "cursor-not-allowed border-hair/50 text-faint/50"
            }`}
          >
            {m.ticker}
          </button>
        ))}
      </div>
      <ConePanel key={sel} ticker={sel} />
    </div>
  );
}
