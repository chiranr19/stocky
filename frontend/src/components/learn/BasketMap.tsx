"use client";

import { useRouter } from "next/navigation";
import {
  CartesianGrid,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type { BasketMember, BasketGroup } from "@/lib/types";
import { fmtCurrency, fmtPct } from "@/lib/format";
import { fmtLens, lensBasis, useLens, type Lens } from "@/lib/lens";
import { GROUP, GROUP_ORDER } from "./shared";

type Pt = {
  ticker: string;
  name: string;
  role: string;
  group: BasketGroup;
  vol_90d: number;
  ret_1y: number;
  price: number | null;
};

function tickerOf(p: unknown): string | undefined {
  const o = p as { ticker?: string; payload?: { ticker?: string } };
  return o?.ticker ?? o?.payload?.ticker;
}

function verdict(p: Pt, bench: Pt | null): { label: string; tone: string } {
  if (!bench) return { label: "", tone: "text-faint" };
  const calmer = p.vol_90d <= bench.vol_90d;
  const better = p.ret_1y >= bench.ret_1y;
  if (better && calmer) return { label: "Beat the market with less churn", tone: "text-up" };
  if (better && !calmer) return { label: "Beat the market, wilder ride", tone: "text-ink" };
  if (!better && calmer) return { label: "Lagged, but calmer", tone: "text-muted" };
  return { label: "More risk, less return than VOO", tone: "text-down" };
}

function Tip({ active, payload, bench, lens }: { active?: boolean; payload?: { payload: Pt }[]; bench: Pt | null; lens?: Lens }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  const v = verdict(p, bench);
  const dollarMode = lens != null && lens !== "pct";
  return (
    <div className="max-w-[240px] rounded-lg border border-hair bg-elevated px-3 py-2 text-xs shadow-card">
      <div className="mb-0.5 font-semibold text-ink">
        {p.ticker} · <span className="text-muted">{fmtCurrency(p.price ?? 0)}</span>
      </div>
      <div className="text-[11px] italic" style={{ color: GROUP[p.group].hex }}>{p.role}</div>
      <div className="mt-1 flex gap-4">
        <span>Risk: <span className="tnum text-ink">{p.vol_90d}%</span></span>
        <span>1y: <span className="tnum text-ink">{lens ? fmtLens(p.ret_1y, lens) : fmtPct(p.ret_1y)}</span></span>
      </div>
      {dollarMode && (
        <div className="mt-0.5 text-[10px] text-faint">on a {lensBasis(lens as Lens)} position</div>
      )}
      {v.label && (
        <div className={`mt-1.5 border-t border-hair pt-1.5 font-medium ${v.tone}`}>{v.label}</div>
      )}
      <div className="mt-1 text-[10px] text-faint">click to open →</div>
    </div>
  );
}

export function BasketMap({ members }: { members: BasketMember[] }) {
  const router = useRouter();
  const { lens } = useLens();

  const pts: Pt[] = members
    .filter((m) => m.measurable && m.vol_90d != null && m.ret_1y != null)
    .map((m) => ({
      ticker: m.ticker,
      name: m.name,
      role: m.role,
      group: m.group,
      vol_90d: m.vol_90d as number,
      ret_1y: m.ret_1y as number,
      price: m.price,
    }));
  const offMap = members.filter((m) => !m.measurable);
  const bench = pts.find((p) => p.group === "benchmark") ?? null;

  if (!pts.length) return null;

  const vols = pts.map((p) => p.vol_90d);
  const rets = pts.map((p) => p.ret_1y);
  const xMin = Math.max(0, Math.floor(Math.min(...vols) - 6));
  const xMax = Math.ceil(Math.max(...vols) + 6);
  const yMin = Math.floor(Math.min(...rets) - 12);
  const yMax = Math.ceil(Math.max(...rets) + 12);
  const bx = bench?.vol_90d ?? (xMin + xMax) / 2;
  const by = bench?.ret_1y ?? 0;

  const byGroup = GROUP_ORDER.map((g) => [g, pts.filter((p) => p.group === g)] as const).filter(
    ([, list]) => list.length,
  );

  const zoneLabel = { fontSize: 10, fill: "#5A616B", fontWeight: 600 } as const;

  return (
    <div className="card p-4">
      <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[11px] text-muted">
        {byGroup.map(([g]) => (
          <span key={g} className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full" style={{ background: GROUP[g].hex }} />
            {GROUP[g].label}
          </span>
        ))}
      </div>

      <ResponsiveContainer width="100%" height={420}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 24, left: 8 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.05)" />
          {/* Weather quadrants, split at VOO. */}
          <ReferenceArea x1={xMin} x2={bx} y1={by} y2={yMax} fill="#22C989" fillOpacity={0.05}
            label={{ value: "calm & paid", position: "insideTopLeft", ...zoneLabel }} />
          <ReferenceArea x1={bx} x2={xMax} y1={by} y2={yMax} fill="#7C6BFF" fillOpacity={0.04}
            label={{ value: "wild & paid", position: "insideTopRight", ...zoneLabel }} />
          <ReferenceArea x1={xMin} x2={bx} y1={yMin} y2={by} fill="#8B929C" fillOpacity={0.04}
            label={{ value: "calm & unpaid", position: "insideBottomLeft", ...zoneLabel }} />
          <ReferenceArea x1={bx} x2={xMax} y1={yMin} y2={by} fill="#F6465D" fillOpacity={0.05}
            label={{ value: "wild & unpaid", position: "insideBottomRight", ...zoneLabel }} />

          <XAxis
            type="number" dataKey="vol_90d" name="Volatility" unit="%" domain={[xMin, xMax]}
            tick={{ fill: "#5A616B", fontSize: 11 }} stroke="rgba(255,255,255,0.08)"
            label={{ value: "← calmer   ·   how wild the ride is   ·   wilder →", position: "bottom", fill: "#8B929C", fontSize: 11 }}
          />
          <YAxis
            type="number" dataKey="ret_1y" name="1y return" unit="%" domain={[yMin, yMax]}
            tick={{ fill: "#5A616B", fontSize: 11 }} stroke="rgba(255,255,255,0.08)"
            label={{ value: "1-year return →", angle: -90, position: "insideLeft", fill: "#8B929C", fontSize: 11 }}
          />
          <ZAxis range={[60, 60]} />
          <Tooltip content={<Tip bench={bench} lens={lens} />} cursor={{ strokeDasharray: "3 3", stroke: "rgba(255,255,255,0.2)" }} />

          {bench && (
            <>
              <ReferenceLine x={bx} stroke="#9AA3AD" strokeDasharray="4 4" strokeOpacity={0.5} />
              <ReferenceLine y={by} stroke="#9AA3AD" strokeDasharray="4 4" strokeOpacity={0.5} />
            </>
          )}

          {byGroup.map(([g, list]) => (
            <Scatter
              key={g}
              data={g === "benchmark" ? [] : list}
              fill={GROUP[g].hex}
              fillOpacity={0.85}
              onClick={(p: unknown) => {
                const t = tickerOf(p);
                if (t) router.push(`/stock/${t}`);
              }}
              className="cursor-pointer"
            />
          ))}
          {bench && (
            <Scatter
              data={[bench]} shape="star" fill="#FFFFFF" className="cursor-pointer"
              onClick={() => router.push(`/stock/${bench.ticker}`)}
            />
          )}
        </ScatterChart>
      </ResponsiveContainer>

      <p className="mt-2 text-xs text-faint">
        The dashed cross is VOO. The dream corner is <b className="text-up">up-and-left</b>:
        beat the market with a calmer ride — notice how empty it is. Tap any dot to open it.
      </p>

      {offMap.length > 0 && (
        <div className="mt-3 rounded-lg border border-amber-400/25 bg-amber-400/5 px-3 py-2.5">
          <div className="text-[11px] font-semibold uppercase tracking-wide text-amber-300">
            Off the map
          </div>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            {offMap.map((m) => m.ticker).join(", ")} can&apos;t be plotted — too little
            history to measure risk or a full-year return.{" "}
            <span className="text-ink">Unplottable means unmeasurable risk, not no risk.</span>{" "}
            A blank past is a warning, not a clean slate.
          </p>
        </div>
      )}
    </div>
  );
}
