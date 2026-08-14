"use client";

import { useState } from "react";
import { AlertTriangle, ChevronDown, Info, TrendingUp } from "lucide-react";
import type { Reading } from "@/lib/types";

const TONE = {
  constructive: {
    icon: TrendingUp,
    text: "text-up",
    border: "border-up/30",
    bg: "bg-up/5",
    label: "constructive",
  },
  caution: {
    icon: AlertTriangle,
    text: "text-down",
    border: "border-down/30",
    bg: "bg-down/5",
    label: "worth caution",
  },
  neutral: {
    icon: Info,
    text: "text-muted",
    border: "border-hair",
    bg: "bg-elevated/40",
    label: "neutral",
  },
} as const;

/** One interpretation: headline always visible, the reasoning on click. */
function ReadingItem({ r, defaultOpen = false }: { r: Reading; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  const tone = TONE[r.tone] ?? TONE.neutral;
  const Icon = tone.icon;

  return (
    <div className={`rounded-lg border ${tone.border} ${tone.bg}`}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-start gap-2.5 px-3 py-2.5 text-left"
      >
        <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${tone.text}`} />
        <span className="flex-1 text-sm font-medium text-ink">{r.headline}</span>
        <ChevronDown
          className={`mt-0.5 h-4 w-4 shrink-0 text-faint transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>
      {open && (
        <div className="space-y-2 px-3 pb-3 pl-[38px] text-xs leading-relaxed">
          <p className="text-muted">{r.detail}</p>
          <p className="text-faint">
            <span className="font-medium text-muted">When this reading lies to you: </span>
            {r.caveat}
          </p>
        </div>
      )}
    </div>
  );
}

/**
 * The reading layer: what the numbers on this page actually mean.
 * First item starts expanded — it answers "is this chart good or risky?".
 */
export function Readings({
  readings,
  title = "How to read this",
  columns = 1,
}: {
  readings: Reading[];
  title?: string;
  columns?: 1 | 2;
}) {
  if (!readings?.length) return null;
  return (
    <div className="card p-4">
      <h3 className="mb-2.5 text-sm font-semibold tracking-tight">{title}</h3>
      <div className={columns === 2 ? "grid gap-2 lg:grid-cols-2" : "space-y-2"}>
        {readings.map((r, i) => (
          <ReadingItem key={`${r.aspect}-${i}`} r={r} defaultOpen={i === 0} />
        ))}
      </div>
      <p className="mt-3 text-[11px] text-faint">
        Interpretations of what the data shows and how veterans read it — never
        instructions. Every reading includes what would make it wrong.
      </p>
    </div>
  );
}

/** Compact single-line reading, for tiles. */
export function ReadingCaption({ r }: { r: Reading }) {
  const tone = TONE[r.tone] ?? TONE.neutral;
  return (
    <div className={`mt-1.5 flex items-start gap-1.5 text-[11px] ${tone.text}`} title={`${r.detail}\n\nWhen it lies: ${r.caveat}`}>
      <span className="leading-snug">{r.headline.split("—").slice(1).join("—").trim() || r.headline}</span>
    </div>
  );
}
