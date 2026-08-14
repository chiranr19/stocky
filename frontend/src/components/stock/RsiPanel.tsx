"use client";

import {
  Area,
  AreaChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SeriesPoint } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { Term } from "@/components/ui/Term";

export function RsiPanel({ rsi }: { rsi: SeriesPoint[] }) {
  const data = rsi
    .filter((p) => p.value !== null)
    .map((p) => ({ t: new Date(p.date + "T00:00:00").getTime(), rsi: p.value as number }));

  const latest = data.length ? data[data.length - 1].rsi : null;

  return (
    <div className="card p-4">
      <div className="mb-1 flex items-center justify-between">
        <h3 className="text-sm font-semibold tracking-tight">
          <Term k="rsi">RSI (14)</Term>
        </h3>
        {latest !== null && (
          <span
            className={`tnum text-sm font-semibold ${latest >= 70 ? "text-up" : latest <= 30 ? "text-down" : "text-muted"}`}
          >
            {latest.toFixed(0)}
            <span className="ml-1 text-xs text-faint">
              {latest >= 70 ? "overbought" : latest <= 30 ? "oversold" : "neutral"}
            </span>
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={120}>
        <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id="rsiFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#7C6BFF" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#7C6BFF" stopOpacity={0} />
            </linearGradient>
          </defs>
          <ReferenceArea y1={70} y2={100} fill="#22C989" fillOpacity={0.06} />
          <ReferenceArea y1={0} y2={30} fill="#F6465D" fillOpacity={0.06} />
          <ReferenceLine y={70} stroke="#22C989" strokeDasharray="3 3" strokeOpacity={0.4} />
          <ReferenceLine y={30} stroke="#F6465D" strokeDasharray="3 3" strokeOpacity={0.4} />
          <XAxis
            dataKey="t"
            type="number"
            scale="time"
            domain={["dataMin", "dataMax"]}
            tickFormatter={(t) => fmtDate(new Date(t).toISOString().slice(0, 10))}
            tick={{ fill: "#5A616B", fontSize: 10 }}
            minTickGap={60}
            stroke="rgba(255,255,255,0.08)"
          />
          <YAxis domain={[0, 100]} ticks={[30, 50, 70]} tick={{ fill: "#5A616B", fontSize: 10 }} width={28} stroke="rgba(255,255,255,0.08)" />
          <Tooltip
            contentStyle={{ background: "#15181D", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 8, fontSize: 12 }}
            labelFormatter={(t) => fmtDate(new Date(t as number).toISOString().slice(0, 10))}
            formatter={(v: number) => [v.toFixed(1), "RSI"]}
          />
          <Area type="monotone" dataKey="rsi" stroke="#7C6BFF" strokeWidth={1.5} fill="url(#rsiFill)" />
        </AreaChart>
      </ResponsiveContainer>
      <div className="mt-1 flex justify-between text-[10px] leading-snug">
        <span className="text-down">
          Below 30 — <span className="text-faint">washed out; sellers exhausted, or still falling</span>
        </span>
        <span className="text-up">
          Above 70 — <span className="text-faint">stretched; strong stocks can stay here for weeks</span>
        </span>
      </div>
    </div>
  );
}
