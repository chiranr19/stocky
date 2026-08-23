// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useMemo, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import type { BasketMember } from "@/lib/types";
import { lensBasis, useLens } from "@/lib/lens";
import { useReducedMotion } from "@/lib/motion";
import { STUDY } from "@/lib/studyCopy";
import { GROUP, useReveal } from "@/components/learn/shared";

const L = 60; // common race length (a full downsampled year)

function daysApart(a: string | null, b: string | null): number {
  if (!a || !b) return Infinity;
  return Math.abs((new Date(a).getTime() - new Date(b).getTime()) / 86_400_000);
}

/** Resample a series to exactly L points by index (eligible series are already
 *  ~L long and start-aligned; this just guards the off-by-a-few case). */
function toL(series: number[]): number[] {
  if (series.length === L) return series;
  return Array.from({ length: L }, (_, i) =>
    series[Math.round((i / (L - 1)) * (series.length - 1))],
  );
}

export function RaceChart({ members }: { members: BasketMember[] }) {
  const { lens } = useLens();
  const reduced = useReducedMotion();
  const [ref, shown] = useReveal<HTMLDivElement>();

  const voo = members.find((m) => m.group === "benchmark") ?? null;
  const vooStart = voo?.series_start ?? null;

  const { eligible, late } = useMemo(() => {
    const el: BasketMember[] = [];
    const lt: BasketMember[] = [];
    for (const m of members) {
      const len = m.series_1y?.length ?? 0;
      const longEnough = len >= 55;
      const aligned = m.group === "benchmark" || daysApart(m.series_start, vooStart) <= 9;
      if (longEnough && aligned) el.push(m);
      else if (len > 0 && m.group !== "benchmark") lt.push(m);
    }
    return { eligible: el, late: lt };
  }, [members, vooStart]);

  const dollar = lens !== "pct";
  const basis = dollar ? (lens as number) : 100;
  const startVal = dollar ? basis : 0;
  const norm = (series: number[]): number[] => {
    const s = toL(series);
    const first = s[0] || 1;
    return s.map((v) => (dollar ? Math.round((v / first) * basis) : +(((v / first - 1) * 100).toFixed(2))));
  };

  const normed = useMemo(
    () => new Map(eligible.map((m) => [m.ticker, norm(m.series_1y)])),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [eligible, lens],
  );

  const data = useMemo(
    () =>
      Array.from({ length: L }, (_, i) => {
        const row: Record<string, number> = { t: i };
        for (const [tk, arr] of normed) row[tk] = arr[i];
        return row;
      }),
    [normed],
  );

  // Default selection = the eligible non-VOO name that most wants attention.
  const [selected, setSelected] = useState<string | null>(null);
  const pick =
    selected ??
    eligible
      .filter((m) => m.group !== "benchmark")
      .sort((a, b) => b.attention - a.attention)[0]?.ticker ??
    null;

  const standings = useMemo(
    () =>
      eligible
        .map((m) => ({ m, end: normed.get(m.ticker)?.[L - 1] ?? startVal }))
        .sort((a, b) => b.end - a.end),
    [eligible, normed, startVal],
  );

  if (eligible.length < 2) return null;

  const selMember = eligible.find((m) => m.ticker === pick) ?? null;
  const yFmt = (v: number) =>
    dollar ? `$${Math.round(v).toLocaleString()}` : `${v >= 0 ? "+" : ""}${v}%`;

  return (
    <div className="card p-4" ref={ref}>
      {/* Legend chips — click to spotlight a runner. */}
      <div className="mb-3 flex flex-wrap gap-1.5">
        {eligible
          .filter((m) => m.group !== "benchmark")
          .map((m) => (
            <button
              key={m.ticker}
              type="button"
              onClick={() => setSelected((s) => (s === m.ticker ? null : m.ticker))}
              className={`rounded-md border px-2 py-0.5 text-[11px] font-medium transition-colors ${
                m.ticker === pick
                  ? "border-accent/40 bg-accent/10 text-accent"
                  : "border-hair text-muted hover:bg-elevated hover:text-ink"
              }`}
            >
              {m.ticker}
            </button>
          ))}
      </div>

      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 6, right: 12, bottom: 4, left: 4 }}>
          <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis
            dataKey="t"
            type="number"
            domain={[0, L - 1]}
            ticks={[0, L - 1]}
            tickFormatter={(t: number) => (t === 0 ? "1y ago" : "now")}
            tick={{ fill: "#5A616B", fontSize: 11 }}
            stroke="rgba(255,255,255,0.08)"
          />
          <YAxis
            tickFormatter={yFmt}
            tick={{ fill: "#5A616B", fontSize: 11 }}
            stroke="rgba(255,255,255,0.08)"
            width={54}
          />
          <ReferenceLine y={startVal} stroke="#5A616B" strokeDasharray="4 4" strokeOpacity={0.5} />

          {eligible.map((m) => {
            const isVoo = m.group === "benchmark";
            const isSel = m.ticker === pick;
            const spotlight = isVoo || isSel;
            return (
              <Line
                key={m.ticker}
                dataKey={m.ticker}
                stroke={isVoo ? "#E7E9EC" : GROUP[m.group].hex}
                strokeWidth={isVoo ? 2.4 : isSel ? 2.4 : 1}
                strokeOpacity={spotlight ? 1 : 0.18}
                dot={false}
                isAnimationActive={shown && !reduced}
                animationDuration={900}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>

      {/* Finish-line standings. */}
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px]">
        {standings.map(({ m, end }, i) => (
          <button
            key={m.ticker}
            type="button"
            onClick={() => setSelected(m.ticker === "VOO" ? null : m.ticker)}
            className="flex items-center gap-1.5"
          >
            <span className="tnum w-4 text-right text-faint">{i + 1}</span>
            <span
              className="h-2 w-2 rounded-full"
              style={{ background: m.group === "benchmark" ? "#E7E9EC" : GROUP[m.group].hex }}
            />
            <span className={m.ticker === pick ? "font-semibold text-ink" : "text-muted"}>
              {m.ticker}
            </span>
            <span className="tnum text-faint">{yFmt(end)}</span>
          </button>
        ))}
      </div>

      {selMember && (
        <Barcode member={selMember} voo={voo} normed={normed} startVal={startVal} lens={lens} />
      )}

      {late.length > 0 && (
        <p className="mt-3 text-[11px] leading-relaxed text-muted">
          <span className="text-faint">Joined the race late:</span>{" "}
          {late.map((m) => m.ticker).join(", ")} — too little of a year to run a fair lap. A blank
          stretch can&apos;t race, the same lottery-ticket lesson from the map.
        </p>
      )}

      <p className="mt-3 border-t border-hair pt-2 text-[11px] leading-relaxed text-faint">
        <span className="font-medium text-muted">Where this lies to you:</span> {STUDY.race.lie}
      </p>
    </div>
  );
}

function Barcode({
  member,
  voo,
  normed,
  startVal,
  lens,
}: {
  member: BasketMember;
  voo: BasketMember | null;
  normed: Map<string, number[]>;
  startVal: number;
  lens: ReturnType<typeof useLens>["lens"];
}) {
  const dollar = lens !== "pct";
  const reg = member.regime_1y ?? [];
  const above = reg.filter(Boolean).length;
  const end = normed.get(member.ticker)?.[L - 1] ?? startVal;
  const vooEnd = voo ? normed.get(voo.ticker)?.[L - 1] ?? startVal : null;
  // Both end values already share the display unit ($ or % points), so the gap
  // is a straight difference — no lens conversion needed.
  const gap = vooEnd != null ? end - vooEnd : null;
  const fmtGap = (g: number) =>
    dollar
      ? `${g >= 0 ? "+" : "−"}$${Math.abs(Math.round(g)).toLocaleString()}`
      : `${g >= 0 ? "+" : ""}${g.toFixed(1)}%`;

  return (
    <div className="mt-3 rounded-lg border border-hair bg-elevated/40 p-3">
      <div className="mb-1.5 flex items-center justify-between text-[11px]">
        <span className="font-medium text-ink">{member.ticker} · trend record</span>
        {reg.length > 0 && (
          <span className="text-muted">
            above its 200-day line{" "}
            <b className="tnum text-ink">
              {above} of {reg.length}
            </b>{" "}
            days
          </span>
        )}
      </div>
      {reg.length > 0 ? (
        <div className="flex h-2.5 gap-px overflow-hidden rounded" aria-label="days above vs below the 200-day line">
          {reg.map((up, i) => (
            <span
              key={i}
              className="flex-1"
              style={{ background: up ? "#22C989" : "#F6465D", opacity: up ? 0.8 : 0.7 }}
            />
          ))}
        </div>
      ) : (
        <p className="text-[11px] text-faint">Not enough history to draw a trend record.</p>
      )}
      <p className="mt-1.5 text-[11px] leading-relaxed text-faint">
        Green = a day closed above its 200-day line (the sale rack is inside the store); red = below.{" "}
        {gap != null && (
          <span className="text-muted">
            {member.ticker} finished{" "}
            <b className={gap >= 0 ? "text-up" : "text-down"}>{fmtGap(gap)}</b>{" "}
            {gap >= 0 ? "ahead of" : "behind"} VOO
            {dollar ? ` ${lensBasis(lens)}` : ""}.
          </span>
        )}
      </p>
    </div>
  );
}
