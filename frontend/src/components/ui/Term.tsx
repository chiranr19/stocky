// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useEffect, useRef, useState } from "react";
import { getTerm } from "@/lib/glossary";

/**
 * Inline, teachable term. Wrap any metric label:
 *   <Term k="voo">VOO</Term>
 * Dotted underline → click → plain-English popover (what / why / when it lies).
 */
export function Term({
  k,
  children,
  className = "",
}: {
  k: string;
  children?: React.ReactNode;
  className?: string;
}) {
  const entry = getTerm(k);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!entry) return <span className={className}>{children}</span>;

  return (
    <span ref={ref} className="relative inline-block">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setOpen((o) => !o);
        }}
        className={`cursor-help border-b border-dotted border-faint/70 text-inherit decoration-dotted underline-offset-2 transition-colors hover:border-accent hover:text-accent ${className}`}
        aria-expanded={open}
      >
        {children ?? entry.term}
      </button>

      {open && (
        <span
          role="dialog"
          className="absolute left-0 top-full z-50 mt-2 block w-72 animate-fade-in cursor-default rounded-xl border border-hair bg-elevated p-3.5 text-left shadow-glow"
          onClick={(e) => e.stopPropagation()}
        >
          <span className="mb-1.5 block text-[13px] font-semibold text-ink">
            {entry.term}
          </span>

          {entry.analogy && (
            <span className="mb-2 block rounded-lg border border-accent/20 bg-accent/5 px-2.5 py-1.5">
              <span className="block text-[10px] font-semibold uppercase tracking-wide text-accent">
                Think of it like
              </span>
              <span className="mt-0.5 block text-xs italic leading-relaxed text-ink/90">
                {entry.analogy}
              </span>
            </span>
          )}

          <span className="block text-xs leading-relaxed text-muted">{entry.what}</span>

          <span className="mt-2.5 block text-[10px] font-semibold uppercase tracking-wide text-accent">
            Why veterans watch it
          </span>
          <span className="block text-xs leading-relaxed text-muted">
            {entry.whyVetsWatchIt}
          </span>

          <span className="mt-2.5 block text-[10px] font-semibold uppercase tracking-wide text-down">
            When it lies to you
          </span>
          <span className="block text-xs leading-relaxed text-muted">
            {entry.whenItLies}
          </span>
        </span>
      )}
    </span>
  );
}
