"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { CompareSeries } from "@/lib/types";
import { fmtDate } from "@/lib/format";

// VOO always gray (the baseline); others get fixed categorical hues in order.
const SERIES_COLORS = ["#7C6BFF", "#22D3EE", "#F59E0B", "#22C989"];
export const BENCH_COLOR = "#8B929C";

export function colorFor(ticker: string, index: number, benchmark: string): string {
  return ticker === benchmark ? BENCH_COLOR : SERIES_COLORS[index % SERIES_COLORS.length];
}

interface Row {
  t: number;
  [ticker: string]: number;
}

function ChartTooltip({
  active,
  payload,
  colors,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string; payload: Row }[];
  colors: Record<string, string>;
}) {
  if (!active || !payload?.length) return null;
  const t = payload[0].payload.t;
  return (
    <div className="rounded-lg border border-hair bg-elevated px-3 py-2 text-xs shadow-card">
      <div className="mb-1 text-faint">{fmtDate(new Date(t).toISOString().slice(0, 10))}</div>
      {payload
        .slice()
        .sort((a, b) => b.value - a.value)
        .map((p) => (
          <div key={p.name} className="flex items-center justify-between gap-4">
            <span style={{ color: colors[p.name] }}>{p.name}</span>
            <span className="tnum text-ink">{p.value?.toFixed(1)}</span>
          </div>
        ))}
    </div>
  );
}

export function NormalizedChart({
  series,
  benchmark,
}: {
  series: CompareSeries[];
  benchmark: string;
}) {
  // Merge all series onto a shared time axis.
  const map = new Map<number, Row>();
  const colors: Record<string, string> = {};
  let ci = 0;
  for (const s of series) {
    const color = colorFor(s.ticker, s.ticker === benchmark ? -1 : ci++, benchmark);
    colors[s.ticker] = color;
    for (const p of s.points) {
      const t = new Date(p.date + "T00:00:00").getTime();
      const row = map.get(t) ?? ({ t } as Row);
      row[s.ticker] = p.value;
      map.set(t, row);
    }
  }
  const data = [...map.values()].sort((a, b) => a.t - b.t);

  return (
    <div className="card p-4">
      <div className="mb-2 flex flex-wrap items-center gap-3 text-xs">
        {series.map((s) => (
          <span key={s.ticker} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ background: colors[s.ticker] }} />
            {s.ticker}
            {s.ticker === benchmark && <span className="text-faint">(benchmark)</span>}
          </span>
        ))}
        <span className="ml-auto text-faint">all rebased to 100 at the start</span>
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            tickFormatter={(t) => fmtDate(new Date(t).toISOString().slice(0, 10))}
            tick={{ fill: "#5A616B", fontSize: 11 }}
            minTickGap={56}
            stroke="rgba(255,255,255,0.08)"
          />
          <YAxis
            tick={{ fill: "#5A616B", fontSize: 11 }}
            width={44}
            stroke="rgba(255,255,255,0.08)"
            domain={["auto", "auto"]}
          />
          <Tooltip content={<ChartTooltip colors={colors} />} />
          {series.map((s) => (
            <Line
              key={s.ticker}
              type="monotone"
              dataKey={s.ticker}
              stroke={colors[s.ticker]}
              strokeWidth={s.ticker === benchmark ? 1.5 : 2}
              strokeDasharray={s.ticker === benchmark ? "4 3" : undefined}
              dot={false}
              connectNulls
              animationDuration={800}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
