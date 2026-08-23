// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
import type { StudyCopy } from "@/lib/studyCopy";

/** The metaphor lede for a study section, plus an optional data-driven line that
 *  makes the section read itself ("NVDA ran furthest this year"). */
export function StudyLede({
  copy,
  computed,
}: {
  copy: StudyCopy;
  computed?: React.ReactNode;
}) {
  return (
    <div className="mb-3 max-w-2xl">
      <p className="text-sm leading-relaxed text-muted">{copy.lede}</p>
      {computed && <p className="mt-1 text-sm font-medium text-ink">{computed}</p>}
    </div>
  );
}
