"use client";

import type { WatchoutRow } from "@/lib/types";
import { InfoPop } from "@/components/ui/InfoPop";
import { StockRowItem } from "@/components/stocks/StockRowItem";
import { FlagChips } from "@/components/flags/Flags";

const RISK_NOTE =
  "Weighted severity of the hazards detected — higher means more, or more " +
  "serious, risk patterns.\n\n" +
  "High-severity flags count 3, medium 2, low 1. It describes what is visible " +
  "in the price data today, not a prediction about tomorrow.";

/**
 * One watch-out row: stock + its named hazards + risk score.
 *
 * Shared by the Watch-outs page and the Pulse preview so the two can't drift.
 * The hazard chips are the entire point of the row, so on phones they move to
 * a second line instead of being hidden.
 */
export function WatchoutRowItem({ r, rank }: { r: WatchoutRow; rank?: number }) {
  return (
    <div className="border-b border-hair/40 last:border-0">
      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <StockRowItem row={r.row} rank={rank} />
        </div>
        <div className="hidden max-w-[300px] shrink-0 justify-end md:flex">
          <FlagChips flags={r.flags} max={3} />
        </div>
        <div className="shrink-0 pr-3 text-right">
          <InfoPop content={RISK_NOTE}>
            <span className="tnum block text-sm font-semibold text-down">
              {r.risk_score.toFixed(0)}
            </span>
            <span className="block text-[10px] text-faint">risk</span>
          </InfoPop>
        </div>
      </div>

      {/* Phone: the hazards are why this row is here — never hide them. */}
      <div className="flex flex-wrap gap-1 px-2.5 pb-2 pl-9 md:hidden">
        <FlagChips flags={r.flags} max={3} compact />
      </div>
    </div>
  );
}
