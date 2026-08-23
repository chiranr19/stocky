// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { AlertTriangle } from "lucide-react";
import { useReveal } from "./shared";

/** The recurring frame for one act: metaphor first → live chart → where it lies. */
export function ActShell({
  id,
  index,
  eyebrow,
  title,
  metaphor,
  lie,
  children,
}: {
  id: string;
  index: number;
  eyebrow: string;
  title: string;
  metaphor: string;
  lie: string;
  children: React.ReactNode;
}) {
  const [ref, shown] = useReveal<HTMLElement>();

  return (
    <section
      id={id}
      ref={ref}
      className="scroll-mt-24 border-t border-hair pt-8 motion-safe:transition-all motion-safe:duration-500"
      style={
        shown
          ? undefined
          : { opacity: 0.001, transform: "translateY(10px)" }
      }
    >
      <div className="mb-4 flex items-baseline gap-3">
        <span className="tnum text-3xl font-semibold text-accent/40">
          {String(index).padStart(2, "0")}
        </span>
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-[0.15em] text-faint">
            {eyebrow}
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-ink">{title}</h2>
        </div>
      </div>

      <p className="mb-5 max-w-2xl border-l-2 border-accent/40 pl-4 text-lg italic leading-relaxed text-ink/90">
        {metaphor}
      </p>

      <div>{children}</div>

      <div className="mt-4 flex items-start gap-2 rounded-lg border border-down/25 bg-down/5 px-3.5 py-2.5">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-down" />
        <p className="text-xs leading-relaxed text-muted">
          <span className="font-medium text-down">Where this lies to you: </span>
          {lie}
        </p>
      </div>
    </section>
  );
}
