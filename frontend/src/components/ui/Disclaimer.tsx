import { Info } from "lucide-react";

// Persistent, honest framing — this is a learning tool, never advice.
export function Disclaimer({ className = "" }: { className?: string }) {
  return (
    <div
      className={`flex items-start gap-2 rounded-lg border border-hair bg-panel/60 px-3 py-2 text-xs text-muted ${className}`}
    >
      <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-faint" />
      <span>
        Educational tool for building market intuition — <b>not financial
        advice</b>. Past performance never guarantees future results.
      </span>
    </div>
  );
}
