"use client";

import { useEffect, useRef, useState } from "react";
import type { BasketGroup } from "@/lib/types";

// Narrative families — the color key that ties the whole /learn page together.
// Muted secondary hues for data categories; the app's violet accent stays for
// the mega-caps, the names the beginner already knows.
export const GROUP: Record<
  BasketGroup,
  { label: string; hex: string; ring: string; chip: string }
> = {
  mega: {
    label: "Household names",
    hex: "#7C6BFF",
    ring: "border-accent/40",
    chip: "border-accent/30 bg-accent/10 text-accent",
  },
  umbrella: {
    label: "The four umbrellas",
    hex: "#38BDF8",
    ring: "border-sky-400/40",
    chip: "border-sky-400/30 bg-sky-400/10 text-sky-300",
  },
  wildcard: {
    label: "Wildcards",
    hex: "#F2A33C",
    ring: "border-amber-400/40",
    chip: "border-amber-400/30 bg-amber-400/10 text-amber-300",
  },
  scout: {
    label: "Scouting reports",
    hex: "#2DD4BF",
    ring: "border-teal-400/40",
    chip: "border-teal-400/30 bg-teal-400/10 text-teal-300",
  },
  benchmark: {
    label: "The benchmark",
    hex: "#9AA3AD",
    ring: "border-white/20",
    chip: "border-white/20 bg-white/10 text-muted",
  },
};

export const GROUP_ORDER: BasketGroup[] = ["mega", "umbrella", "wildcard", "scout", "benchmark"];

/** Reveal-on-scroll: returns a ref + whether it has entered the viewport once.
 *  Consumers gate motion behind `motion-safe:` so reduced-motion stays static. */
export function useReveal<T extends HTMLElement>(): [React.RefObject<T>, boolean] {
  const ref = useRef<T>(null);
  const [shown, setShown] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            setShown(true);
            io.disconnect();
          }
        }
      },
      { rootMargin: "-8% 0px -8% 0px" },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return [ref, shown];
}

/** Numbers that reach the screen must be rounded (no float artifacts). */
export const pct = (v: number | null | undefined, dp = 1): string =>
  v == null ? "—" : `${v >= 0 ? "+" : ""}${v.toFixed(dp)}%`;

export const money = (v: number | null | undefined): string =>
  v == null ? "—" : `$${Math.round(v).toLocaleString()}`;

/** Percent below the running peak at each point — the "underwater" drawdown
 *  curve. Always ≤ 0. Shared by DrawdownRide and any valley sparkline. */
export function underwater(series: number[]): number[] {
  let peak = -Infinity;
  return series.map((v) => {
    peak = Math.max(peak, v);
    return peak > 0 ? (v / peak - 1) * 100 : 0;
  });
}
