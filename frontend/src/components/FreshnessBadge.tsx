// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { CircleCheck, CircleDashed, Loader2, TriangleAlert } from "lucide-react";
import { fmtDate } from "@/lib/format";
import type { DataHealth } from "@/lib/types";
import { InfoPop } from "@/components/ui/InfoPop";

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
        <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" />
        <span className="hidden sm:inline">Loading data · </span>
        {pct}%
      </span>
    );
  }

  const fresh = health.is_fresh;
  const Icon = fresh ? CircleCheck : TriangleAlert;
  const tone = fresh
    ? "border-up/30 bg-up/10 text-up"
    : "border-down/30 bg-down/10 text-down";
  // Phones get the short form — "Data current · Aug 14, 2026" alone is half a
  // 375px viewport, and the full detail is one tap away in the popover.
  const shortLabel = fresh ? "Current" : `${health.sessions_behind} behind`;
  const longLabel = fresh
    ? `Data current · ${fmtDate(health.latest_trading_date ?? health.expected_session)}`
    : `${health.sessions_behind} sessions behind`;

  return (
    <InfoPop
      content={[
        `Latest session: ${health.latest_trading_date ?? "—"} (expected ${health.expected_session})`,
        `Coverage: ${health.tickers_loaded}/${health.tickers_total} tickers`,
        health.history_span_days
          ? `History: ${(health.history_span_days / 365).toFixed(1)} years · median ${health.median_sessions} sessions/ticker`
          : "",
        health.thinnest_ticker
          ? `Thinnest: ${health.thinnest_ticker} (${health.thinnest_sessions} sessions)`
          : "",
        `Failed fetches: ${health.failed_count} · flagged anomalies: ${health.anomalies_count}`,
        `End-of-day data from Yahoo Finance; intraday is delayed.`,
      ]
        .filter(Boolean)
        .join("\n")}
    >
      <span
        className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs ${tone}`}
      >
        <Icon className="h-3.5 w-3.5 shrink-0" />
        <span className="sm:hidden">{shortLabel}</span>
        <span className="hidden whitespace-nowrap sm:inline">{longLabel}</span>
      </span>
    </InfoPop>
  );
}
