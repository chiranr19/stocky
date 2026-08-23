// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { Wallet } from "lucide-react";
import { BUDGET_PRESETS, useBudget } from "@/lib/budget";
import { Term } from "./ui/Term";

/** Global affordability cap — segmented control, drives every budget-aware view. */
export function BudgetControl() {
  const { budget, setBudget } = useBudget();

  return (
    <div className="flex items-center gap-2">
      <span className="hidden items-center gap-1 text-[11px] text-faint sm:flex">
        <Wallet className="h-3.5 w-3.5" />
        <Term k="share_price">Max/share</Term>
      </span>
      <div className="flex overflow-hidden rounded-lg border border-hair bg-panel p-0.5">
        {BUDGET_PRESETS.map((p) => {
          const active = budget === p.value;
          return (
            <button
              key={p.label}
              onClick={() => setBudget(p.value)}
              className={`tnum rounded-md px-1.5 py-1 text-xs transition-colors sm:px-2 ${
                active
                  ? "bg-accent text-white"
                  : "text-muted hover:bg-elevated hover:text-ink"
              }`}
              aria-label={`Max share price ${p.label}`}
            >
              <span className="sm:hidden">{p.short}</span>
              <span className="hidden sm:inline">{p.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
