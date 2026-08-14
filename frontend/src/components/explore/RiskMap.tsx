"use client";

import { useRouter } from "next/navigation";
import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { RiskMapResponse, RiskPoint } from "@/lib/types";
import { fmtCurrency, fmtPct } from "@/lib/format";

// Recharts hands click payloads back in different shapes across mark types;
// dig the ticker out of either the node or its `.payload`.
function tickerOf(p: unknown): string | undefined {
  const o = p as { ticker?: string; payload?: { ticker?: string } };
  return o?.ticker ?? o?.payload?.ticker;
}

// Distinguishable-on-dark hues per sector. Identity is confirmed on hover, so
// this leans on separation rather than strict CVD-safety across all 11 pairs.
const SECTOR_COLORS: Record<string, string> = {
  "Information Technology": "#7C6BFF",
  "Communication Services": "#22D3EE",
  "Consumer Discretionary": "#F59E0B",
  Financials: "#22C989",
  "Health Care": "#F472B6",
  Industrials: "#94A3B8",
  "Consumer Staples": "#A3E635",
  Energy: "#FB7185",
  Utilities: "#38BDF8",
  "Real Estate": "#C084FC",
  Materials: "#FBBF24",
};

/** Which quadrant vs VOO this lands in, and what that means. */
function quadrantVerdict(
  p: RiskPoint,
  bench: RiskPoint | null,
): { label: string; blurb: string; tone: string } {
  if (!bench) return { label: "", blurb: "", tone: "text-faint" };
  const calmer = p.vol_90d <= bench.vol_90d;
  const better = p.ret_1y >= bench.ret_1y;
  if (better && calmer)
    return {
      label: "Beat the market with less churn",
      blurb: "Rare and worth studying — though one year is a short window to judge it on.",
      tone: "text-up",
    };
  if (better && !calmer)
    return {
      label: "Beat the market, but a wilder ride",
      blurb: "You were paid for the extra swings this time. That trade doesn't always pay.",
      tone: "text-ink",
    };
  if (!better && calmer)
    return {
      label: "Lagged the market, but calmer",
      blurb: "Quieter, cheaper to hold emotionally — you gave up return for that comfort.",
      tone: "text-muted",
    };
  return {
    label: "More volatility, less return than VOO",
    blurb: "The worst corner of this chart: you paid in swings and weren't compensated.",
    tone: "text-down",
  };
}

function PointTooltip({
  active,
  payload,
  bench,
}: {
  active?: boolean;
  payload?: { payload: RiskPoint }[];
  bench: RiskPoint | null;
}) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  const v = quadrantVerdict(p, bench);
  return (
    <div className="max-w-[260px] rounded-lg border border-hair bg-elevated px-3 py-2 text-xs shadow-card">
      <div className="mb-0.5 font-semibold text-ink">
        {p.ticker} · <span className="text-muted">{fmtCurrency(p.price)}</span>
      </div>
      <div className="text-faint">{p.name}</div>
      <div className="mt-1 flex gap-4">
        <span>Risk: <span className="tnum text-ink">{p.vol_90d}%</span></span>
        <span>1y: <span className="tnum text-ink">{fmtPct(p.ret_1y)}</span></span>
      </div>
      {v.label && (
        <div className="mt-1.5 border-t border-hair pt-1.5">
          <div className={`font-medium ${v.tone}`}>{v.label}</div>
          <div className="mt-0.5 text-[10px] leading-snug text-faint">{v.blurb}</div>
        </div>
      )}
      <div className="mt-1 text-[10px] text-faint">click to open →</div>
    </div>
  );
}

export function RiskMap({ data }: { data: RiskMapResponse }) {
  const router = useRouter();
  const bench = data.benchmark;

  // Group by sector so the legend + colors follow the entity, not rank.
  const bySector = new Map<string, RiskPoint[]>();
  for (const p of data.points) {
    if (!bySector.has(p.sector)) bySector.set(p.sector, []);
    bySector.get(p.sector)!.push(p);
  }

  return (
    <div className="card p-4">
      <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[11px] text-muted">
        {[...bySector.keys()].map((s) => (
          <span key={s} className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full" style={{ background: SECTOR_COLORS[s] ?? "#8B929C" }} />
            {s}
          </span>
        ))}
        {bench && (
          <span className="flex items-center gap-1 font-medium text-ink">
            <span className="text-accent">★</span> VOO (benchmark)
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={440}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.05)" />
          <XAxis
            type="number"
            dataKey="vol_90d"
            name="Volatility"
            unit="%"
            tick={{ fill: "#5A616B", fontSize: 11 }}
            stroke="rgba(255,255,255,0.08)"
            label={{ value: "← safer   ·   Volatility (risk)   ·   riskier →", position: "bottom", fill: "#8B929C", fontSize: 11 }}
          />
          <YAxis
            type="number"
            dataKey="ret_1y"
            name="1y return"
            unit="%"
            tick={{ fill: "#5A616B", fontSize: 11 }}
            stroke="rgba(255,255,255,0.08)"
            label={{ value: "1-year return →", angle: -90, position: "insideLeft", fill: "#8B929C", fontSize: 11 }}
          />
          <ZAxis range={[36, 36]} />
          <Tooltip content={<PointTooltip bench={bench} />} cursor={{ strokeDasharray: "3 3", stroke: "rgba(255,255,255,0.2)" }} />

          {bench && (
            <>
              <ReferenceLine x={bench.vol_90d} stroke="#7C6BFF" strokeDasharray="4 4" strokeOpacity={0.5} />
              <ReferenceLine y={bench.ret_1y} stroke="#7C6BFF" strokeDasharray="4 4" strokeOpacity={0.5} />
            </>
          )}

          {[...bySector.entries()].map(([sector, points]) => (
            <Scatter
              key={sector}
              name={sector}
              data={points}
              fill={SECTOR_COLORS[sector] ?? "#8B929C"}
              fillOpacity={0.8}
              onClick={(p: unknown) => {
                const t = tickerOf(p);
                if (t) router.push(`/stock/${t}`);
              }}
              className="cursor-pointer"
            />
          ))}

          {bench && (
            <Scatter
              name="VOO"
              data={[bench]}
              shape="star"
              fill="#FFFFFF"
              className="cursor-pointer"
              onClick={() => router.push(`/stock/${bench.ticker}`)}
            />
          )}
        </ScatterChart>
      </ResponsiveContainer>

      <p className="mt-2 text-xs text-faint">
        Each dot is a stock: further <b className="text-ink">right</b> = more volatile
        (riskier), further <b className="text-ink">up</b> = better 1-year return. The
        dashed lines mark VOO. Anything <b className="text-up">up-and-left</b> of them beat
        the market with less risk — notice how few names manage it.
      </p>
    </div>
  );
}
