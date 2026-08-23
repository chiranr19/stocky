"use client";

import { useState } from "react";
import Link from "next/link";
import { Area, AreaChart, ReferenceLine, ResponsiveContainer, Tooltip, YAxis } from "recharts";
import type { BasketMember } from "@/lib/types";
import { useLens } from "@/lib/lens";
import { money, underwater } from "./shared";

const AMOUNTS = [100, 500, 1000];

export function DrawdownRide({ members }: { members: BasketMember[] }) {
  const { lens } = useLens();
  const eligible = members.filter((m) => m.measurable && m.series_1y.length > 4);
  const voo = members.find((m) => m.group === "benchmark" && m.series_1y.length > 4);

  // Default to the deepest drawdown — it makes the lesson land hardest.
  const deepest = [...eligible].sort(
    (a, b) => (a.max_drawdown_1y ?? 0) - (b.max_drawdown_1y ?? 0),
  )[0];
  const [ticker, setTicker] = useState<string>(deepest?.ticker ?? eligible[0]?.ticker ?? "");
  // Seed the seat size from the global dollar lens (fall back to $500 in % mode).
  const [amount, setAmount] = useState<number>(typeof lens === "number" ? lens : 500);

  const pick = eligible.find((m) => m.ticker === ticker) ?? eligible[0];
  if (!pick) return null;

  const uw = underwater(pick.series_1y);
  const uwVoo = voo ? underwater(voo.series_1y) : [];
  const n = Math.max(uw.length, uwVoo.length);
  const data = Array.from({ length: n }, (_, i) => ({
    i,
    member: uw[i] ?? null,
    voo: uwVoo[i] ?? null,
  }));

  const worstPct = pick.max_drawdown_1y ?? Math.min(...uw, 0);
  const lostDollars = Math.abs((amount * worstPct) / 100);

  return (
    <div className="card p-4">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap overflow-hidden rounded-lg border border-hair text-xs">
          {eligible.map((m) => (
            <button
              key={m.ticker}
              onClick={() => setTicker(m.ticker)}
              aria-pressed={m.ticker === pick.ticker}
              className={`px-2.5 py-1.5 font-medium transition-colors ${
                m.ticker === pick.ticker ? "bg-accent text-white" : "bg-panel text-muted hover:text-ink"
              }`}
            >
              {m.ticker}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-3 flex flex-wrap items-baseline gap-x-2 gap-y-1 text-sm">
        <span className="text-muted">A</span>
        <div className="flex overflow-hidden rounded-lg border border-hair text-xs">
          {AMOUNTS.map((a) => (
            <button
              key={a}
              onClick={() => setAmount(a)}
              aria-pressed={a === amount}
              className={`tnum px-2.5 py-1 font-medium transition-colors ${
                a === amount ? "bg-accent text-white" : "bg-panel text-muted hover:text-ink"
              }`}
            >
              {money(a)}
            </button>
          ))}
        </div>
        <span className="text-muted">
          seat on {pick.ticker}&apos;s ride was down{" "}
          <span className="tnum font-semibold text-down">−{money(lostDollars)}</span> at the
          worst point (a <span className="tnum text-down">{worstPct.toFixed(0)}%</span> drop).
        </span>
      </div>

      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 6, right: 8, bottom: 0, left: 8 }}>
          <defs>
            <linearGradient id="uw" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#F6465D" stopOpacity={0.05} />
              <stop offset="100%" stopColor="#F6465D" stopOpacity={0.4} />
            </linearGradient>
          </defs>
          <YAxis
            domain={["dataMin", 0]}
            tick={{ fill: "#5A616B", fontSize: 11 }}
            stroke="rgba(255,255,255,0.08)"
            tickFormatter={(v: number) => `${v.toFixed(0)}%`}
            width={38}
          />
          <ReferenceLine y={0} stroke="rgba(255,255,255,0.2)" />
          <Tooltip
            contentStyle={{ background: "#15181D", border: "1px solid rgba(255,255,255,0.07)", borderRadius: 8, fontSize: 12 }}
            labelFormatter={() => ""}
            formatter={(v: number, name: string) => [`${v.toFixed(1)}%`, name === "member" ? pick.ticker : "VOO"]}
          />
          {voo && (
            <Area type="monotone" dataKey="voo" stroke="#9AA3AD" strokeWidth={1} fill="none" strokeDasharray="3 3" isAnimationActive={false} />
          )}
          <Area type="monotone" dataKey="member" stroke="#F6465D" strokeWidth={1.5} fill="url(#uw)" />
        </AreaChart>
      </ResponsiveContainer>

      <p className="mt-2 text-xs text-faint">
        The shaded valley is how far underwater you&apos;d have been at each moment over the
        past year — 0% is the last high-water mark. The dashed grey line is VOO&apos;s much
        shallower valley.{" "}
        <Link href={`/time-machine?ticker=${pick.ticker}`} className="text-muted underline-offset-2 hover:text-accent hover:underline">
          Ride it minute by minute in the Time Machine →
        </Link>
      </p>
    </div>
  );
}
