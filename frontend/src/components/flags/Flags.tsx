"use client";

import { useState } from "react";
import { AlertTriangle, ChevronDown, ShieldCheck } from "lucide-react";
import type { RiskFlag } from "@/lib/types";

const SEVERITY = {
  high: { risk: "border-down/50 bg-down/15 text-down", strength: "border-up/50 bg-up/15 text-up" },
  medium: { risk: "border-down/30 bg-down/10 text-down/90", strength: "border-up/30 bg-up/10 text-up/90" },
  low: { risk: "border-hair bg-elevated text-muted", strength: "border-hair bg-elevated text-muted" },
} as const;

/** Compact named-pattern chip. Hover gives the full reasoning. */
export function FlagChip({ flag, compact = false }: { flag: RiskFlag; compact?: boolean }) {
  const cls = SEVERITY[flag.severity]?.[flag.kind] ?? SEVERITY.low.risk;
  const Icon = flag.kind === "risk" ? AlertTriangle : ShieldCheck;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 font-medium ${cls} ${
        compact ? "text-[10px]" : "text-[11px]"
      }`}
      title={`${flag.label} — ${flag.why}\n\nWhat vets do: ${flag.what_vets_do}`}
    >
      <Icon className="h-3 w-3 shrink-0" />
      {flag.label}
    </span>
  );
}

export function FlagChips({ flags, max = 3, compact = false }: { flags: RiskFlag[]; max?: number; compact?: boolean }) {
  if (!flags?.length) return null;
  const shown = flags.slice(0, max);
  const rest = flags.length - shown.length;
  return (
    <div className="flex flex-wrap items-center gap-1">
      {shown.map((f) => (
        <FlagChip key={f.code} flag={f} compact={compact} />
      ))}
      {rest > 0 && <span className="text-[10px] text-faint">+{rest}</span>}
    </div>
  );
}

/** Expandable full explanation of one flag — used on the deep dive. */
function FlagDetail({ flag }: { flag: RiskFlag }) {
  const [open, setOpen] = useState(false);
  const isRisk = flag.kind === "risk";
  const Icon = isRisk ? AlertTriangle : ShieldCheck;
  return (
    <div className={`rounded-lg border ${isRisk ? "border-down/25 bg-down/5" : "border-up/25 bg-up/5"}`}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center gap-2 px-3 py-2 text-left"
      >
        <Icon className={`h-3.5 w-3.5 shrink-0 ${isRisk ? "text-down" : "text-up"}`} />
        <span className="flex-1 text-xs font-medium text-ink">{flag.label}</span>
        <span className="text-[10px] uppercase tracking-wide text-faint">{flag.severity}</span>
        <ChevronDown className={`h-3.5 w-3.5 text-faint transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="space-y-1.5 px-3 pb-2.5 pl-[30px] text-[11px] leading-relaxed">
          <p className="text-muted">{flag.why}</p>
          <p className="text-faint">
            <span className="font-medium text-muted">What vets do: </span>
            {flag.what_vets_do}
          </p>
        </div>
      )}
    </div>
  );
}

/** Both sides of the picture: what's wrong with this setup, and what's right. */
export function FlagPanel({ flags }: { flags: RiskFlag[] }) {
  if (!flags?.length) return null;
  const risks = flags.filter((f) => f.kind === "risk");
  const strengths = flags.filter((f) => f.kind === "strength");

  return (
    <div className="card p-4">
      <h3 className="mb-2.5 text-sm font-semibold tracking-tight">
        What makes this setup good or bad
      </h3>
      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <div className="mb-1.5 text-[11px] uppercase tracking-wide text-down">
            Watch-outs {risks.length > 0 && `(${risks.length})`}
          </div>
          {risks.length ? (
            <div className="space-y-1.5">
              {risks.map((f) => (
                <FlagDetail key={f.code} flag={f} />
              ))}
            </div>
          ) : (
            <p className="text-xs text-faint">
              None of the standard risk patterns are present right now. That is not the
              same as &quot;safe&quot; — it means these specific hazards aren&apos;t
              visible in the price data.
            </p>
          )}
        </div>
        <div>
          <div className="mb-1.5 text-[11px] uppercase tracking-wide text-up">
            Strengths {strengths.length > 0 && `(${strengths.length})`}
          </div>
          {strengths.length ? (
            <div className="space-y-1.5">
              {strengths.map((f) => (
                <FlagDetail key={f.code} flag={f} />
              ))}
            </div>
          ) : (
            <p className="text-xs text-faint">
              No standard strength patterns right now.
            </p>
          )}
        </div>
      </div>
      <p className="mt-3 text-[11px] text-faint">
        Named patterns detected from price behavior — descriptions of what is there, not
        instructions about what to do.
      </p>
    </div>
  );
}
