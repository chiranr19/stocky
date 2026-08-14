import { Lightbulb } from "lucide-react";

/** A one-line "why veterans watch this" note above a section. */
export function TeachBanner({ children }: { children: React.ReactNode }) {
  return (
    <div className="mb-3 flex items-start gap-2 rounded-lg border border-hair bg-panel/50 px-3 py-2 text-xs text-muted">
      <Lightbulb className="mt-0.5 h-3.5 w-3.5 shrink-0 text-accent" />
      <span>{children}</span>
    </div>
  );
}
