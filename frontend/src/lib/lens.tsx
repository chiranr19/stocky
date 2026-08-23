// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

// The "dollar lens": show returns as percents, or as what they'd do to a
// hypothetical position of $100 / $500 / $1,000. Follows you across the app.
export type Lens = "pct" | 100 | 500 | 1000;

export const LENS_PRESETS: { label: string; short: string; value: Lens }[] = [
  { label: "%", short: "%", value: "pct" },
  { label: "$100", short: "100", value: 100 },
  { label: "$500", short: "500", value: 500 },
  { label: "$1,000", short: "1k", value: 1000 },
];

const DEFAULT_LENS: Lens = 500; // a $500 hypothetical position
const STORAGE_KEY = "stocky.lens";

interface LensCtx {
  lens: Lens;
  setLens: (l: Lens) => void;
}

const Ctx = createContext<LensCtx>({ lens: DEFAULT_LENS, setLens: () => {} });

export function LensProvider({ children }: { children: React.ReactNode }) {
  const [lens, setLensState] = useState<Lens>(DEFAULT_LENS);

  useEffect(() => {
    const raw =
      typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (raw !== null) setLensState(raw === "pct" ? "pct" : (Number(raw) as Lens));
  }, []);

  const setLens = useCallback((l: Lens) => {
    setLensState(l);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, String(l));
    }
  }, []);

  return <Ctx.Provider value={{ lens, setLens }}>{children}</Ctx.Provider>;
}

export const useLens = () => useContext(Ctx);

/** Render a percent RETURN through the lens. In dollar mode it's what that
 *  return did to the lens-sized position (e.g. −39% on $500 → "−$196").
 *  Only percent RETURNS convert — volatility, RSI, range %, breadth are rates,
 *  not returns, so they stay in percent regardless of the lens. */
export function fmtLens(pctValue: number | null | undefined, lens: Lens): string {
  if (pctValue == null) return "—";
  if (lens === "pct") return `${pctValue >= 0 ? "+" : "−"}${Math.abs(pctValue).toFixed(1)}%`;
  const dollars = Math.round((lens * pctValue) / 100);
  return `${dollars >= 0 ? "+" : "−"}$${Math.abs(dollars).toLocaleString()}`;
}

/** The short "on a $500 position" phrase for captioning a lens-aware column. */
export function lensBasis(lens: Lens): string {
  return lens === "pct" ? "" : `on $${lens.toLocaleString()}`;
}
