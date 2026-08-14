"use client";

import { useEffect, useState } from "react";
import { getMovers } from "@/lib/api";
import { useBudget } from "@/lib/budget";
import type { StockRow } from "@/lib/types";
import { StockRowItem } from "@/components/stocks/StockRowItem";
import { Loading } from "@/components/ui/States";

const TABS: { key: string; label: string; hint: string }[] = [
  { key: "gainers", label: "Gainers", hint: "Biggest % up today." },
  { key: "losers", label: "Losers", hint: "Biggest % down today." },
  { key: "volume", label: "Unusual volume", hint: "Trading far above their normal volume — someone cares today." },
  { key: "highs", label: "52w highs", hint: "At the top of their 1-year range — momentum, or overextended?" },
  { key: "lows", label: "52w lows", hint: "At the bottom — out of favor, or a falling knife?" },
  { key: "gaps", label: "Gaps", hint: "Opened far from yesterday's close, usually on overnight news." },
];

export function Scanners() {
  const { budget } = useBudget();
  const [tab, setTab] = useState("gainers");
  const [rows, setRows] = useState<StockRow[] | null>(null);

  useEffect(() => {
    setRows(null);
    getMovers(tab, budget, 25).then(setRows).catch(() => setRows([]));
  }, [tab, budget]);

  const active = TABS.find((t) => t.key === tab)!;

  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap gap-1 border-b border-hair p-2">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`rounded-md px-2.5 py-1.5 text-xs transition-colors ${
              tab === t.key ? "bg-accent text-white" : "text-muted hover:bg-elevated hover:text-ink"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="border-b border-hair px-4 py-2 text-xs text-faint">{active.hint}</div>

      <div className="p-1.5">
        {rows === null ? (
          <Loading label={`Scanning ${active.label.toLowerCase()}…`} />
        ) : rows.length === 0 ? (
          <div className="px-3 py-8 text-center text-sm text-faint">
            Nothing matches within your budget.
          </div>
        ) : (
          rows.map((r, i) => <StockRowItem key={r.ticker} row={r} rank={i + 1} />)
        )}
      </div>
    </div>
  );
}
