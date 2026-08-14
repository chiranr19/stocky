"use client";

import type { BreadthStats, IndexTile } from "@/lib/types";
import { fmtCurrency } from "@/lib/format";
import { Sparkline } from "@/components/ui/Sparkline";
import { ChangePct } from "@/components/ui/primitives";
import { Term } from "@/components/ui/Term";

const TILE_TERMS: Record<string, string> = {
  VOO: "voo",
  VIX: "vix",
  "10Y Yield": "tnx",
};

function fmtValue(tile: IndexTile): string {
  if (tile.unit === "usd") return fmtCurrency(tile.value);
  if (tile.unit === "percent") return `${tile.value.toFixed(2)}%`;
  return tile.value.toFixed(2);
}

function Tile({ tile }: { tile: IndexTile }) {
  const term = TILE_TERMS[tile.label];
  return (
    <div className="card flex flex-col gap-2 p-4">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-medium text-muted">
            {term ? <Term k={term}>{tile.label}</Term> : tile.label}
          </div>
          <div className="tnum mt-0.5 text-xl font-semibold">{fmtValue(tile)}</div>
        </div>
        <ChangePct value={tile.change_pct} className="text-xs" />
      </div>
      <Sparkline data={tile.spark} width={220} height={32} className="w-full" />
    </div>
  );
}

function BreadthCell({
  label,
  termKey,
  value,
  sub,
  tone = "",
}: {
  label: string;
  termKey?: string;
  value: string;
  sub?: string;
  tone?: string;
}) {
  return (
    <div className="flex flex-col justify-center px-4 py-3">
      <div className="text-[11px] uppercase tracking-wide text-faint">
        {termKey ? <Term k={termKey}>{label}</Term> : label}
      </div>
      <div className={`tnum text-lg font-semibold ${tone}`}>{value}</div>
      {sub && <div className="text-[11px] text-muted">{sub}</div>}
    </div>
  );
}

export function MarketStrip({
  tiles,
  breadth,
}: {
  tiles: IndexTile[];
  breadth: BreadthStats;
}) {
  return (
    <div className="grid gap-3 lg:grid-cols-[1.1fr_1fr]">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {tiles.map((t) => (
          <Tile key={t.ticker} tile={t} />
        ))}
      </div>

      <div className="card grid grid-cols-2 divide-x divide-y divide-hair sm:grid-cols-3">
        <BreadthCell
          label="Above 50-day"
          termKey="breadth"
          value={`${breadth.pct_above_ma50}%`}
          sub={`${breadth.members} members`}
          tone={breadth.pct_above_ma50 >= 50 ? "text-up" : "text-down"}
        />
        <BreadthCell
          label="Above 200-day"
          termKey="moving_average"
          value={`${breadth.pct_above_ma200}%`}
          tone={breadth.pct_above_ma200 >= 50 ? "text-up" : "text-down"}
        />
        <BreadthCell
          label="Adv / Dec"
          termKey="advancers"
          value={`${breadth.advancers} / ${breadth.decliners}`}
          tone={breadth.advancers >= breadth.decliners ? "text-up" : "text-down"}
        />
        <BreadthCell
          label="New 52w highs"
          termKey="range_52w"
          value={String(breadth.new_highs_52w)}
          tone="text-up"
        />
        <BreadthCell
          label="New 52w lows"
          termKey="range_52w"
          value={String(breadth.new_lows_52w)}
          tone={breadth.new_lows_52w > 0 ? "text-down" : ""}
        />
        <BreadthCell
          label="Breadth read"
          value={breadth.pct_above_ma50 >= 55 ? "Broad" : breadth.pct_above_ma50 >= 45 ? "Mixed" : "Narrow"}
        />
      </div>
    </div>
  );
}
