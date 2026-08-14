"use client";

import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { fmtPct, toneClass } from "@/lib/format";
import { Term } from "./Term";

/** Colored, signed percent with a directional arrow. */
export function ChangePct({
  value,
  className = "",
  showArrow = true,
}: {
  value: number | null;
  className?: string;
  showArrow?: boolean;
}) {
  if (value === null || value === undefined)
    return <span className="tnum text-faint">—</span>;
  const up = value >= 0;
  return (
    <span
      className={`tnum inline-flex items-center gap-0.5 ${toneClass(value)} ${className}`}
    >
      {showArrow &&
        (up ? (
          <ArrowUpRight className="h-3 w-3" />
        ) : (
          <ArrowDownRight className="h-3 w-3" />
        ))}
      {fmtPct(value)}
    </span>
  );
}

/** 0–100 screener score as a colored chip. */
export function ScoreBadge({
  score,
  size = "sm",
}: {
  score: number | null;
  size?: "sm" | "lg";
}) {
  if (score === null || score === undefined) return null;
  const tone =
    score >= 80
      ? "border-up/40 text-up bg-up/10"
      : score >= 60
        ? "border-accent/40 text-accent bg-accent/10"
        : "border-hair text-muted bg-elevated";
  const pad = size === "lg" ? "px-2.5 py-1 text-sm" : "px-1.5 py-0.5 text-[11px]";
  return (
    <span className={`tnum inline-flex items-center rounded-md border font-semibold ${tone} ${pad}`}>
      {score.toFixed(0)}
    </span>
  );
}

const FACTOR_LABELS: Record<string, { label: string; term: string }> = {
  momentum: { label: "Mom", term: "momentum" },
  stability: { label: "Stab", term: "volatility" },
  resilience: { label: "Res", term: "drawdown" },
  liquidity: { label: "Liq", term: "liquidity" },
};

/** Four thin factor bars (0–100) making the score legible at a glance. */
export function FactorBars({
  factors,
  compact = false,
}: {
  factors: Record<string, number> | null;
  compact?: boolean;
}) {
  if (!factors) return null;
  const order = ["momentum", "stability", "resilience", "liquidity"];
  return (
    <div className="flex items-end gap-1" title="Score factors (0–100)">
      {order.map((key) => {
        const v = factors[key] ?? 0;
        const meta = FACTOR_LABELS[key];
        return (
          <div key={key} className="flex flex-col items-center gap-0.5">
            <div
              className={`flex ${compact ? "h-5 w-1.5" : "h-6 w-2"} items-end overflow-hidden rounded-sm bg-elevated`}
            >
              <div
                className="w-full rounded-sm bg-accent/80"
                style={{ height: `${Math.max(6, v)}%` }}
              />
            </div>
            {!compact && (
              <span className="text-[8px] uppercase text-faint">{meta.label}</span>
            )}
          </div>
        );
      })}
    </div>
  );
}

/** 52-week range with a marker for where price sits (0 = low, 1 = high). */
export function RangeBar({
  position,
  className = "",
}: {
  position: number;
  className?: string;
}) {
  const pct = Math.round(position * 100);
  return (
    <div className={`relative h-1.5 rounded-full bg-elevated ${className}`}>
      <div
        className="absolute top-1/2 h-3 w-1 -translate-y-1/2 rounded-full bg-accent shadow-glow"
        style={{ left: `calc(${Math.min(98, Math.max(2, pct))}% - 2px)` }}
      />
    </div>
  );
}

/** Section header with an optional teachable term and right-aligned slot. */
export function SectionHeader({
  icon: Icon,
  title,
  termKey,
  sub,
  right,
}: {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  termKey?: string;
  sub?: string;
  right?: React.ReactNode;
}) {
  return (
    <div className="mb-3 flex items-end justify-between gap-3">
      <div className="flex items-center gap-2">
        {Icon && <Icon className="h-4 w-4 text-accent" />}
        <h2 className="text-sm font-semibold tracking-tight">
          {termKey ? <Term k={termKey}>{title}</Term> : title}
        </h2>
        {sub && <span className="text-xs text-faint">{sub}</span>}
      </div>
      {right}
    </div>
  );
}

/** A labeled stat tile; label can be a teachable term. */
export function StatTile({
  label,
  termKey,
  value,
  tone = "",
  hint,
}: {
  label: string;
  termKey?: string;
  value: React.ReactNode;
  tone?: string;
  hint?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-hair bg-elevated/50 px-3 py-2.5">
      <div className="text-[11px] uppercase tracking-wide text-faint">
        {termKey ? <Term k={termKey}>{label}</Term> : label}
      </div>
      <div className={`tnum mt-0.5 text-lg font-semibold ${tone}`}>{value}</div>
      {hint && <div className="text-[11px] text-muted">{hint}</div>}
    </div>
  );
}
