// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import type { SectorPanel } from "@/lib/types";
import { fmtPct } from "@/lib/format";

// Green/red intensity scales with the move, saturating around ±2%.
function tileColor(pct: number): string {
  const mag = Math.min(Math.abs(pct) / 2, 1);
  const alpha = 0.1 + mag * 0.5;
  return pct >= 0
    ? `rgba(34, 201, 137, ${alpha})`
    : `rgba(246, 70, 93, ${alpha})`;
}

/** Compact clickable overview — click a tile to jump to that sector's panel. */
export function SectorHeatmapStrip({ sectors }: { sectors: SectorPanel[] }) {
  const jump = (etf: string) => {
    document.getElementById(`sector-${etf}`)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  };

  return (
    <div className="grid grid-cols-3 gap-1.5 sm:grid-cols-6 lg:grid-cols-11">
      {sectors.map((s) => (
        <button
          key={s.etf}
          onClick={() => jump(s.etf)}
          title={`${s.label} · ${s.members_affordable} affordable · jump ↓`}
          className="flex flex-col gap-1 rounded-lg border border-hair px-2.5 py-2 text-left transition-transform hover:-translate-y-0.5"
          style={{ backgroundColor: tileColor(s.etf_change_pct) }}
        >
          <span className="truncate text-[11px] font-medium text-ink">{s.label}</span>
          <span className="tnum text-sm font-semibold">{fmtPct(s.etf_change_pct)}</span>
        </button>
      ))}
    </div>
  );
}
