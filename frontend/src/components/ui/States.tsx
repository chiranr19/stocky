// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { AlertTriangle, Loader2 } from "lucide-react";
import { useHealth } from "@/lib/useHealth";

export function ErrorCard({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="card flex flex-col items-start gap-3 p-5">
      <div className="flex items-center gap-2 text-sm text-down">
        <AlertTriangle className="h-4 w-4" />
        {message}
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-white hover:opacity-90"
        >
          Retry
        </button>
      )}
    </div>
  );
}

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-hair bg-panel px-4 py-10 text-sm text-muted">
      <Loader2 className="h-4 w-4 animate-spin text-accent" />
      {label}
    </div>
  );
}

/** Shown while the background warm-up is still ingesting the full universe. */
export function WarmingNotice() {
  const health = useHealth();
  if (!health || health.status !== "warming") return null;
  const pct = Math.min(
    100,
    Math.round((health.warm_loaded / Math.max(1, health.tickers_total)) * 100),
  );
  return (
    <div className="flex items-center gap-3 rounded-xl border border-accent/25 bg-accent/5 px-4 py-3 text-sm text-muted">
      <Loader2 className="h-4 w-4 shrink-0 animate-spin text-accent" />
      <div className="flex-1">
        <span className="text-ink">Loading the full S&amp;P 500…</span> {pct}% —
        priority names are ready, the rest are streaming in.
      </div>
      <div className="hidden h-1.5 w-40 overflow-hidden rounded-full bg-elevated sm:block">
        <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
