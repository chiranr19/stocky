"use client";

import { useState } from "react";
import { Line, LineChart, ResponsiveContainer, Tooltip, YAxis } from "recharts";
import type { BasketMember } from "@/lib/types";
import { GROUP, money } from "./shared";

function normalize(series: number[]): number[] {
  const base = series[0];
  return base ? series.map((v) => (1000 * v) / base) : series;
}

export function BoringWinner({ members }: { members: BasketMember[] }) {
  const voo = members.find((m) => m.group === "benchmark" && m.series_1y.length > 4);
  const eligible = members.filter(
    (m) => m.group !== "benchmark" && m.measurable && m.series_1y.length > 4,
  );
  const [ticker, setTicker] = useState<string>(eligible[0]?.ticker ?? "");
  const pick = eligible.find((m) => m.ticker === ticker) ?? eligible[0];

  if (!voo || !pick) return null;

  const nMember = normalize(pick.series_1y);
  const nVoo = normalize(voo.series_1y);
  const n = Math.max(nMember.length, nVoo.length);
  const data = Array.from({ length: n }, (_, i) => ({
    i,
    member: nMember[i] ?? null,
    voo: nVoo[i] ?? null,
  }));
  const endMember = nMember[nMember.length - 1];
  const endVoo = nVoo[nVoo.length - 1];
  const memberColor = GROUP[pick.group].hex;

  return (
    <div className="card p-4">
      <div className="mb-3 flex flex-wrap gap-1.5">
        {eligible.map((m) => (
          <button
            key={m.ticker}
            onClick={() => setTicker(m.ticker)}
            aria-pressed={m.ticker === pick.ticker}
            className={`rounded-lg border px-2.5 py-1 text-xs font-medium transition-colors ${
              m.ticker === pick.ticker
                ? "border-accent bg-accent text-white"
                : "border-hair bg-panel text-muted hover:text-ink"
            }`}
          >
            {m.ticker}
          </button>
        ))}
      </div>

      <div className="mb-2 flex flex-wrap gap-4 text-sm">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm" style={{ background: memberColor }} />
          {pick.ticker}: <span className="tnum font-semibold">{money(endMember)}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-sm bg-white/70" />
          VOO: <span className="tnum font-semibold">{money(endVoo)}</span>
        </span>
        <span className="text-faint">from $1,000, one year ago</span>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: 8 }}>
          <YAxis
            domain={["auto", "auto"]}
            tick={{ fill: "#5A616B", fontSize: 11 }}
            stroke="rgba(255,255,255,0.08)"
            tickFormatter={(v: number) => `$${Math.round(v)}`}
            width={48}
          />
          <Tooltip
            contentStyle={{ background: "#15181D", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 8, fontSize: 12 }}
            labelFormatter={() => ""}
            formatter={(v: number, name: string) => [money(v), name === "member" ? pick.ticker : "VOO"]}
          />
          <Line type="monotone" dataKey="voo" stroke="#FFFFFF" strokeOpacity={0.7} strokeWidth={1.5} dot={false} isAnimationActive={false} />
          <Line type="monotone" dataKey="member" stroke={memberColor} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>

      <p className="mt-3 rounded-lg border border-white/15 bg-white/5 px-3 py-2.5 text-xs leading-relaxed text-muted">
        <span className="font-medium text-ink">{voo.role}. </span>
        {voo.role_story}
      </p>
    </div>
  );
}
