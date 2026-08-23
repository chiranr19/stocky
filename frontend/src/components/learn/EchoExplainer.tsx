// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useState } from "react";
import type { BasketMember } from "@/lib/types";
import { pct } from "./shared";

/** A strip of one dot per past episode: wins green, losses red, worst ringed. */
function DotStrip({ n, wins }: { n: number; wins: number }) {
  const dots = Array.from({ length: n }, (_, i) => i < wins);
  return (
    <div className="flex flex-wrap gap-1">
      {dots.map((win, i) => {
        const isWorst = i === n - 1; // the last loss carries the worst-case ring
        return (
          <span
            key={i}
            style={{ animationDelay: `${i * 35}ms` }}
            className={`h-3 w-3 rounded-full motion-safe:animate-pop-in ${
              win ? "bg-up" : "bg-down"
            } ${isWorst && !win ? "ring-2 ring-down ring-offset-2 ring-offset-panel" : ""}`}
          />
        );
      })}
    </div>
  );
}

export function EchoExplainer({ members }: { members: BasketMember[] }) {
  const withEcho = members.filter((m) => m.echo);
  const without = members.filter((m) => !m.echo);
  const [ticker, setTicker] = useState<string>(withEcho[0]?.ticker ?? "");

  const pick = withEcho.find((m) => m.ticker === ticker) ?? withEcho[0];

  if (!pick || !pick.echo) {
    return (
      <div className="card p-4 text-sm text-muted">
        None of the watchlist names has enough similar past dips to build a base rate right
        now — thinner evidence, not a verdict.
      </div>
    );
  }

  const e = pick.echo;
  const wins = Math.round(e.win_rate * e.n);
  const scope = e.kind === "at_least" ? `dips of at least ${e.min_depth_pct}%` : "similar past dips";

  return (
    <div className="card p-4">
      <div className="mb-3 flex flex-wrap gap-1.5">
        {withEcho.map((m) => (
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

      <p className="text-sm leading-relaxed text-ink">
        The last <span className="tnum font-semibold">{e.n}</span> times {pick.ticker} sat in{" "}
        {scope}, a month later{" "}
        <span className="tnum font-semibold text-up">{wins}</span> ended higher and{" "}
        <span className="tnum font-semibold text-down">{e.n - wins}</span> lower. The typical
        move was <span className="tnum font-semibold">{pct(e.median_fwd_pct)}</span>; the worst
        of them kept falling to{" "}
        <span className="tnum font-semibold text-down">{pct(e.worst_pct)}</span>.
      </p>

      <div className="my-3">
        <DotStrip n={e.n} wins={wins} />
      </div>

      {e.n_benchmarked ? (
        <p className="text-xs text-muted">
          And versus just holding VOO over the same windows:{" "}
          <span className="tnum font-medium text-ink">
            {e.beat_benchmark} of {e.n_benchmarked}
          </span>{" "}
          beat the boring benchmark
          {e.median_excess_pct != null && (
            <>
              {" "}
              (a typical edge of{" "}
              <span className={`tnum ${e.median_excess_pct >= 0 ? "text-up" : "text-down"}`}>
                {pct(e.median_excess_pct)}
              </span>
              )
            </>
          )}
          .
        </p>
      ) : null}

      {without.length > 0 && (
        <p className="mt-3 border-t border-hair pt-2 text-[11px] text-faint">
          No base rate for {without.map((m) => m.ticker).join(", ")}: near its high, or too
          little history. Thinner evidence, not a green light.
        </p>
      )}
    </div>
  );
}
