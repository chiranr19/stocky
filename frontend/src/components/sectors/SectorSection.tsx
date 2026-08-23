// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useState } from "react";
import { ChevronDown } from "lucide-react";
import type { SectorPanel } from "@/lib/types";
import { formatBudget, useBudget } from "@/lib/budget";
import { ChangePct } from "@/components/ui/primitives";
import { Term } from "@/components/ui/Term";
import { StockRowItem } from "@/components/stocks/StockRowItem";

const INITIAL = 5;

export function SectorSection({ panel }: { panel: SectorPanel }) {
  const { budget } = useBudget();
  const [expanded, setExpanded] = useState(false);
  const shown = expanded ? panel.top : panel.top.slice(0, INITIAL);

  return (
    <section
      id={`sector-${panel.etf}`}
      className="card scroll-mt-20 overflow-hidden"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-hair px-4 py-3">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold tracking-tight">
            <Term k="sector">{panel.label}</Term>
          </h3>
          <span className="rounded-md border border-hair px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-faint">
            <Term k="etf">{panel.etf}</Term> <ChangePct value={panel.etf_change_pct} showArrow={false} className="text-[10px]" />
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs text-muted">
          <span title="Share of members up today">
            <Term k="breadth">Breadth</Term>{" "}
            <span
              className={`tnum font-medium ${panel.breadth_pct_up >= 50 ? "text-up" : "text-down"}`}
            >
              {panel.breadth_pct_up}%
            </span>
          </span>
          <span className="tnum">
            {panel.members_affordable}
            <span className="text-faint">/{panel.members_total} affordable</span>
          </span>
        </div>
      </div>

      {/* Rows */}
      {shown.length === 0 ? (
        <div className="px-4 py-6 text-center text-sm text-faint">
          No {panel.label} stocks {formatBudget(budget)}. Try a higher cap.
        </div>
      ) : (
        <div className="divide-y divide-hair/50 p-1.5">
          {shown.map((row, i) => (
            <StockRowItem key={row.ticker} row={row} rank={i + 1} showScore />
          ))}
        </div>
      )}

      {/* Footer */}
      {panel.top.length > INITIAL && (
        <button
          onClick={() => setExpanded((e) => !e)}
          className="flex w-full items-center justify-center gap-1.5 border-t border-hair py-2 text-xs text-muted transition-colors hover:bg-elevated hover:text-ink"
        >
          {expanded ? "Show top 5" : `Show all ${panel.top.length}`}
          <ChevronDown
            className={`h-3.5 w-3.5 transition-transform ${expanded ? "rotate-180" : ""}`}
          />
        </button>
      )}
    </section>
  );
}
