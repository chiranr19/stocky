"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

// null = no cap ("show me everything"). Default is the user's real $200 max.
export type Budget = number | null;

export const BUDGET_PRESETS: { label: string; value: Budget }[] = [
  { label: "$50", value: 50 },
  { label: "$100", value: 100 },
  { label: "$200", value: 200 },
  { label: "$500", value: 500 },
  { label: "No cap", value: null },
];

const DEFAULT_BUDGET: Budget = 200;
const STORAGE_KEY = "stocky.budget";

interface BudgetCtx {
  budget: Budget;
  setBudget: (b: Budget) => void;
}

const Ctx = createContext<BudgetCtx>({ budget: DEFAULT_BUDGET, setBudget: () => {} });

export function BudgetProvider({ children }: { children: React.ReactNode }) {
  const [budget, setBudgetState] = useState<Budget>(DEFAULT_BUDGET);

  useEffect(() => {
    const raw =
      typeof window !== "undefined" ? window.localStorage.getItem(STORAGE_KEY) : null;
    if (raw !== null) setBudgetState(raw === "null" ? null : Number(raw));
  }, []);

  const setBudget = useCallback((b: Budget) => {
    setBudgetState(b);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, b === null ? "null" : String(b));
    }
  }, []);

  return <Ctx.Provider value={{ budget, setBudget }}>{children}</Ctx.Provider>;
}

export const useBudget = () => useContext(Ctx);

export function formatBudget(b: Budget): string {
  return b === null ? "no cap" : `≤ $${b}`;
}
