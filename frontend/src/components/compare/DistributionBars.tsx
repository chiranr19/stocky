// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import type { Histogram } from "@/lib/types";

/** Compact daily-return distribution (single hue). Wider spread = more volatile. */
export function DistributionBars({
  hist,
  color = "#7C6BFF",
  label,
}: {
  hist: Histogram;
  color?: string;
  label: string;
}) {
  const max = Math.max(1, ...hist.counts);
  return (
    <div className="rounded-lg border border-hair bg-elevated/40 p-3">
      <div className="mb-1.5 text-xs font-medium text-ink">{label}</div>
      <div className="flex h-16 items-end gap-[2px]">
        {hist.counts.map((c, i) => {
          const mid = i - Math.floor(hist.counts.length / 2);
          return (
            <div
              key={i}
              className="flex-1 rounded-sm"
              style={{
                height: `${(c / max) * 100}%`,
                background: color,
                opacity: mid === 0 ? 0.35 : 0.8,
              }}
              title={`${hist.edges[i]}%…${hist.edges[i + 1]}%: ${c} days`}
            />
          );
        })}
      </div>
      <div className="mt-1 flex justify-between text-[9px] text-faint">
        <span>{hist.edges[0]}%</span>
        <span>daily return</span>
        <span>+{hist.edges[hist.edges.length - 1]}%</span>
      </div>
    </div>
  );
}
