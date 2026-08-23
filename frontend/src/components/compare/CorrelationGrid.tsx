// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import type { CorrelationMatrix } from "@/lib/types";
import { Term } from "@/components/ui/Term";

// Diverging scale: cool (move oppositely) ↔ neutral gray (unrelated) ↔ warm
// (move together). Not green/red — correlation isn't "good/bad".
function cellColor(r: number): string {
  const mag = Math.min(Math.abs(r), 1);
  if (r >= 0) return `rgba(124, 107, 255, ${0.12 + mag * 0.55})`; // violet = together
  return `rgba(34, 211, 238, ${0.12 + mag * 0.55})`; // cyan = opposite
}

export function CorrelationGrid({ corr }: { corr: CorrelationMatrix }) {
  const { labels, matrix } = corr;
  if (labels.length < 2) return null;

  return (
    <div className="card p-4">
      <h3 className="mb-1 text-sm font-semibold tracking-tight">
        <Term k="correlation">Correlation</Term>
      </h3>
      <p className="mb-3 text-xs text-faint">
        +1 = move in lockstep · 0 = unrelated · −1 = opposite. Two stocks near +1 are
        really <Term k="diversification">one bet</Term> twice.
      </p>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[360px] border-separate border-spacing-1">
          <thead>
            <tr>
              <th />
              {labels.map((l) => (
                <th key={l} className="tnum px-1 pb-1 text-xs font-medium text-muted">
                  {l}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {matrix.map((row, i) => (
              <tr key={labels[i]}>
                <td className="tnum pr-2 text-right text-xs font-medium text-muted">
                  {labels[i]}
                </td>
                {row.map((v, j) => (
                  <td
                    key={j}
                    className="tnum rounded-md px-2 py-2 text-center text-xs text-ink"
                    style={{ background: i === j ? "rgba(255,255,255,0.06)" : cellColor(v) }}
                    title={`${labels[i]} vs ${labels[j]}: ${v.toFixed(2)}`}
                  >
                    {v.toFixed(2)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
