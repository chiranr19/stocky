// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useMemo, useState } from "react";
import type { BasketMember, Constellation as ConstellationData, CorrelationMatrix } from "@/lib/types";
import { InfoPop } from "@/components/ui/InfoPop";
import { STUDY } from "@/lib/studyCopy";
import { GROUP } from "@/components/learn/shared";

interface Node {
  ticker: string;
  cx: number;
  cy: number;
  r: number;
  color: string;
  isVoo: boolean;
}

const PAD = 44; // how far from center (of 50) the outermost star can sit

export function Constellation({
  data,
  members,
  correlation,
  note,
}: {
  data: ConstellationData;
  members: BasketMember[];
  correlation: CorrelationMatrix;
  note: string;
}) {
  const [sel, setSel] = useState<string | null>(null);

  const byTicker = useMemo(() => new Map(members.map((m) => [m.ticker, m])), [members]);
  const idx = useMemo(
    () => new Map(correlation.labels.map((t, i) => [t, i])),
    [correlation.labels],
  );

  const rho = (a: string, b: string): number | null => {
    const i = idx.get(a);
    const j = idx.get(b);
    if (i == null || j == null) return null;
    return correlation.matrix[i]?.[j] ?? null;
  };

  const nodes: Node[] = useMemo(
    () =>
      (data?.nodes ?? []).map((n) => {
        const m = byTicker.get(n.ticker);
        const vol = m?.vol_90d ?? 25;
        const isVoo = m?.group === "benchmark";
        return {
          ticker: n.ticker,
          cx: 50 + n.x * PAD,
          cy: 50 - n.y * PAD, // flip: +y is up
          r: Math.max(2.4, Math.min(8, 2.4 + vol / 11)),
          color: m ? GROUP[m.group].hex : "#9AA3AD",
          isVoo,
        };
      }),
    [data.nodes, byTicker],
  );

  const nodeAt = useMemo(() => new Map(nodes.map((n) => [n.ticker, n])), [nodes]);

  if (nodes.length < 2) return null;

  return (
    <div className="card p-4">
      <div className="mb-2 flex justify-end">
        <InfoPop content={STUDY.constellation.method} align="right">
          <span className="text-[11px] text-faint underline decoration-dotted underline-offset-2">
            how it&apos;s placed
          </span>
        </InfoPop>
      </div>
      <div className="grid gap-4 md:grid-cols-[1fr_auto] md:items-center">
        <div className="relative mx-auto w-full max-w-md">
          <svg
            viewBox="0 0 100 100"
            className="aspect-square w-full"
            onClick={() => setSel(null)}
            role="img"
            aria-label="A map of which watchlist names move together."
          >
            {/* MST links — the skeleton connecting each star to its nearest kin. */}
            {(data?.mst ?? []).map((e) => {
              const a = nodeAt.get(e.a);
              const b = nodeAt.get(e.b);
              if (!a || !b) return null;
              const touchesSel = sel === e.a || sel === e.b;
              const strength = Math.min(1, Math.abs(e.r));
              return (
                <g key={`${e.a}-${e.b}`}>
                  <line
                    x1={a.cx}
                    y1={a.cy}
                    x2={b.cx}
                    y2={b.cy}
                    stroke={touchesSel ? "#7C6BFF" : "#8B929C"}
                    strokeWidth={touchesSel ? 0.7 : 0.4}
                    strokeOpacity={sel ? (touchesSel ? 0.9 : 0.12) : 0.2 + strength * 0.5}
                  />
                  {touchesSel && (
                    <text
                      x={(a.cx + b.cx) / 2}
                      y={(a.cy + b.cy) / 2 - 1}
                      fontSize={3}
                      fill="#B7ADFF"
                      textAnchor="middle"
                    >
                      {e.r.toFixed(2)}
                    </text>
                  )}
                </g>
              );
            })}

            {/* Stars. In "gravity view" (a star selected) every other star's glow
                tracks how tightly it moves with the chosen one. */}
            {nodes.map((n) => {
              const r = sel ? rho(sel, n.ticker) : null;
              const tight = r == null ? 1 : Math.abs(r);
              const dim = sel && n.ticker !== sel ? 0.2 + tight * 0.8 : 1;
              return (
                <g
                  key={n.ticker}
                  onClick={(ev) => {
                    ev.stopPropagation();
                    setSel((s) => (s === n.ticker ? null : n.ticker));
                  }}
                  className="cursor-pointer"
                >
                  {n.isVoo && (
                    <circle cx={n.cx} cy={n.cy} r={n.r + 1.5} fill="none" stroke="#E7E9EC" strokeWidth={0.5} strokeOpacity={dim} />
                  )}
                  <circle
                    cx={n.cx}
                    cy={n.cy}
                    r={n.r}
                    fill={n.isVoo ? "#E7E9EC" : n.color}
                    fillOpacity={dim}
                    stroke={n.ticker === sel ? "#7C6BFF" : "none"}
                    strokeWidth={0.8}
                  />
                  <text
                    x={n.cx}
                    y={n.cy + n.r + 3}
                    fontSize={3}
                    fill="#8B929C"
                    fillOpacity={dim}
                    textAnchor="middle"
                  >
                    {n.ticker}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        <div className="text-xs leading-relaxed text-muted md:max-w-[15rem]">
          <p>
            {sel ? (
              <>
                Brightness now tracks how tightly each name moves with{" "}
                <b className="text-ink">{sel}</b>. The dim, far-off stars are the ones giving you
                real diversification.
              </>
            ) : (
              <>Tap a star to see how tightly every other name is tied to it.</>
            )}
          </p>
          <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-[11px]">
            {(["mega", "umbrella", "wildcard", "scout", "benchmark"] as const)
              .filter((g) => nodes.some((n) => byTicker.get(n.ticker)?.group === g))
              .map((g) => (
                <span key={g} className="flex items-center gap-1">
                  <span className="h-2 w-2 rounded-full" style={{ background: GROUP[g].hex }} />
                  {GROUP[g].label}
                </span>
              ))}
          </div>
          <p className="mt-2 text-[10px] text-faint">Bigger star = wilder daily swings.</p>
        </div>
      </div>

      {note && <p className="mt-3 text-[11px] leading-relaxed text-faint">{note}</p>}

      <p className="mt-3 border-t border-hair pt-2 text-[11px] leading-relaxed text-faint">
        <span className="font-medium text-muted">Where this lies to you:</span> {STUDY.constellation.lie}
      </p>
    </div>
  );
}
