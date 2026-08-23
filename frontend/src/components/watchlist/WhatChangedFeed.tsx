// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import Link from "next/link";
import { AlertTriangle, Info, TrendingUp } from "lucide-react";
import type { WatchEvent } from "@/lib/types";

const TONE = {
  constructive: { icon: TrendingUp, border: "border-up/30", text: "text-up" },
  caution: { icon: AlertTriangle, border: "border-down/30", text: "text-down" },
  neutral: { icon: Info, border: "border-hair", text: "text-muted" },
} as const;

/** The day-over-day change feed — what's different about your names since yesterday. */
export function WhatChangedFeed({ events }: { events: WatchEvent[] }) {
  if (!events.length) {
    return (
      <div className="card p-4 text-sm text-muted">
        A quiet day on your list — no verdicts changed since yesterday.
      </div>
    );
  }
  return (
    <div className="space-y-2">
      {events.map((e, i) => {
        const tone = TONE[e.tone] ?? TONE.neutral;
        const Icon = tone.icon;
        return (
          <div
            key={`${e.ticker}-${e.code}-${i}`}
            className={`flex items-start gap-2.5 rounded-lg border ${tone.border} bg-panel/60 px-3.5 py-2.5`}
          >
            <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${tone.text}`} />
            <div className="min-w-0 flex-1">
              <div className="flex items-baseline gap-2">
                <Link
                  href={`/stock/${e.ticker}`}
                  className="shrink-0 text-xs font-semibold text-ink hover:text-accent"
                >
                  {e.ticker}
                </Link>
                <span className="text-sm font-medium text-ink">{e.headline}</span>
              </div>
              <p className="mt-0.5 text-xs leading-relaxed text-muted">{e.detail}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
