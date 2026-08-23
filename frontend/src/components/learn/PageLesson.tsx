// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { AlertTriangle } from "lucide-react";

/** The light ActShell — a metaphor lede + optional "where this lies to you"
 *  footer — for pages that aren't the six-act /learn tour but should still open
 *  in the same teaching voice. */
export function PageLesson({ metaphor, lie }: { metaphor: string; lie?: string }) {
  return (
    <div className="mb-5 space-y-2">
      <p className="max-w-2xl border-l-2 border-accent/40 pl-4 text-base italic leading-relaxed text-ink/90">
        {metaphor}
      </p>
      {lie && (
        <div className="flex max-w-2xl items-start gap-2 rounded-lg border border-down/25 bg-down/5 px-3.5 py-2">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-down" />
          <p className="text-xs leading-relaxed text-muted">
            <span className="font-medium text-down">Where this lies to you: </span>
            {lie}
          </p>
        </div>
      )}
    </div>
  );
}
