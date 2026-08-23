// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { Coins } from "lucide-react";
import { LENS_PRESETS, useLens } from "@/lib/lens";

/** The dollar lens — flip returns between % and "what it did to a $N position". */
export function LensControl() {
  const { lens, setLens } = useLens();

  return (
    <div className="flex items-center gap-2">
      <span className="hidden items-center gap-1 text-[11px] text-faint sm:flex">
        <Coins className="h-3.5 w-3.5" />
        Show as
      </span>
      <div className="flex overflow-hidden rounded-lg border border-hair bg-panel p-0.5">
        {LENS_PRESETS.map((p) => {
          const active = lens === p.value;
          return (
            <button
              key={p.label}
              onClick={() => setLens(p.value)}
              className={`tnum rounded-md px-1.5 py-1 text-xs transition-colors sm:px-2 ${
                active
                  ? "bg-accent text-white"
                  : "text-muted hover:bg-elevated hover:text-ink"
              }`}
              aria-label={p.value === "pct" ? "Show returns as percent" : `Show returns on a $${p.value} position`}
              aria-pressed={active}
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
