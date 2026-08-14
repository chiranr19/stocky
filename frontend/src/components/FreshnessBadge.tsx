"use client";

import { CircleCheck, CircleDashed, Loader2, TriangleAlert } from "lucide-react";
import { fmtDate } from "@/lib/format";
import type { DataHealth } from "@/lib/types";

export function FreshnessBadge({ health }: { health: DataHealth | null }) {
  if (!health) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-lg border border-hair bg-panel px-2.5 py-1.5 text-xs text-faint">
        <CircleDashed className="h-3.5 w-3.5" />
        connecting…
      </span>
    );
  }

  const warming = health.status === "warming";
  const pct = Math.min(
    100,
    Math.round((health.warm_loaded / Math.max(1, health.tickers_total)) * 100),
  );

  if (warming) {
    return (
      <span
        className="inline-flex items-center gap-1.5 rounded-lg border border-accent/30 bg-accent/10 px-2.5 py-1.5 text-xs text-accent"
        title={`Warming ${health.tickers_loaded}/${health.tickers_total} tickers`}
      >
        <Loader2 className="h-3.5 w-3.5 animate-spin" />
        Loading data · {pct}%
      </span>
    );
  }

  const fresh = health.is_fresh;
  const Icon = fresh ? CircleCheck : TriangleAlert;
  const tone = fresh
    ? "border-up/30 bg-up/10 text-up"
    : "border-down/30 bg-down/10 text-down";
  const label = fresh
    ? `Data current · ${fmtDate(health.latest_trading_date ?? health.expected_session)}`
    : `${health.sessions_behind} sessions behind`;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs ${tone}`}
      title={[
        `Latest session: ${health.latest_trading_date ?? "—"}`,
        `Expected: ${health.expected_session}`,
        `Loaded: ${health.tickers_loaded}/${health.tickers_total}`,
        health.failed_count ? `Failed: ${health.failed_count}` : "",
        `End-of-day data from Yahoo Finance; intraday is delayed.`,
      ]
        .filter(Boolean)
        .join("\n")}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </span>
  );
}
