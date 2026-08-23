// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useState } from "react";
import type { BasketMember, CorrelationMatrix } from "@/lib/types";
import { CorrelationGrid } from "@/components/compare/CorrelationGrid";

function slice(corr: CorrelationMatrix, keep: string[]): CorrelationMatrix {
  const idx = keep.map((k) => corr.labels.indexOf(k)).filter((i) => i >= 0);
  return {
    labels: idx.map((i) => corr.labels[i]),
    matrix: idx.map((i) => idx.map((j) => corr.matrix[i][j])),
  };
}

export function UmbrellaGrid({
  members,
  correlation,
  note,
  benchmark,
}: {
  members: BasketMember[];
  correlation: CorrelationMatrix;
  note: string;
  benchmark: string;
}) {
  const [view, setView] = useState<"umbrellas" | "all">("umbrellas");

  const umbrellas = members.filter((m) => m.group === "umbrella").map((m) => m.ticker);
  const shown =
    view === "umbrellas"
      ? slice(correlation, [...umbrellas, benchmark])
      : correlation;

  // Live min/max pairwise correlation among the umbrellas (off-diagonal).
  const u = slice(correlation, umbrellas);
  let lo = 1;
  let hi = -1;
  for (let i = 0; i < u.labels.length; i++) {
    for (let j = 0; j < u.labels.length; j++) {
      if (i === j) continue;
      const v = u.matrix[i][j];
      if (Number.isFinite(v)) {
        lo = Math.min(lo, v);
        hi = Math.max(hi, v);
      }
    }
  }
  const haveRange = u.labels.length >= 2 && hi >= lo;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex overflow-hidden rounded-lg border border-hair text-xs">
          {(["umbrellas", "all"] as const).map((v) => (
            <button
              key={v}
              onClick={() => setView(v)}
              aria-pressed={view === v}
              className={`px-3 py-1.5 font-medium transition-colors ${
                view === v ? "bg-accent text-white" : "bg-panel text-muted hover:text-ink"
              }`}
            >
              {v === "umbrellas" ? "The four utilities" : "Whole watchlist"}
            </button>
          ))}
        </div>
        {haveRange && (
          <p className="text-xs text-muted">
            The four move together at{" "}
            <span className="tnum font-medium text-ink">
              {lo.toFixed(2)}–{hi.toFixed(2)}
            </span>{" "}
            — near lockstep. Four names, effectively <span className="text-ink">one bet</span>.
          </p>
        )}
      </div>

      <CorrelationGrid corr={shown} />

      {note && (
        <p className="rounded-lg border border-amber-400/25 bg-amber-400/5 px-3 py-2 text-xs leading-relaxed text-muted">
          {note}
        </p>
      )}
    </div>
  );
}
