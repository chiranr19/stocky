"use client";

import { useEffect, useState } from "react";
import { Check } from "lucide-react";

const KEY = "stocky.learn.progress";

export type Act = { id: string; label: string };

/** Sticky act rail: click to jump, tracks which acts you've reached. */
export function LearnProgress({ acts }: { acts: Act[] }) {
  const [active, setActive] = useState<string>(acts[0]?.id ?? "");
  const [visited, setVisited] = useState<Set<string>>(new Set());

  // Restore prior progress.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setVisited(new Set(JSON.parse(raw) as string[]));
    } catch {
      /* ignore */
    }
  }, []);

  // Track the section nearest the top of the viewport as "active", and mark
  // every act that scrolls into view as visited.
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        const inView = entries.filter((e) => e.isIntersecting);
        if (inView.length) {
          const top = inView.sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
          setActive(top.target.id);
          setVisited((prev) => {
            const next = new Set(prev);
            inView.forEach((e) => next.add(e.target.id));
            try {
              localStorage.setItem(KEY, JSON.stringify([...next]));
            } catch {
              /* ignore */
            }
            return next;
          });
        }
      },
      { rootMargin: "-40% 0px -55% 0px" },
    );
    acts.forEach((a) => {
      const el = document.getElementById(a.id);
      if (el) io.observe(el);
    });
    return () => io.disconnect();
  }, [acts]);

  return (
    <nav
      aria-label="Lesson progress"
      className="sticky top-2 z-30 -mx-1 mb-6 flex gap-1.5 overflow-x-auto rounded-xl border border-hair bg-panel/80 px-1.5 py-1.5 backdrop-blur [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
    >
      {acts.map((a, i) => {
        const isActive = active === a.id;
        const done = visited.has(a.id) && !isActive;
        return (
          <button
            key={a.id}
            onClick={() => document.getElementById(a.id)?.scrollIntoView({ behavior: "smooth", block: "start" })}
            aria-current={isActive ? "true" : undefined}
            className={`flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors ${
              isActive
                ? "bg-accent text-white"
                : done
                  ? "text-up hover:bg-elevated"
                  : "text-muted hover:bg-elevated hover:text-ink"
            }`}
          >
            <span className="tnum opacity-70">{done ? <Check className="h-3 w-3" /> : String(i + 1).padStart(2, "0")}</span>
            {a.label}
          </button>
        );
      })}
    </nav>
  );
}
