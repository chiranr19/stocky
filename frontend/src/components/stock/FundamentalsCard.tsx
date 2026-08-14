"use client";

import { useEffect, useState } from "react";
import { getFundamentals } from "@/lib/api";
import type { Fundamentals } from "@/lib/types";
import { fmtCompact } from "@/lib/format";
import { Term } from "@/components/ui/Term";

function Metric({
  label,
  termKey,
  value,
}: {
  label: string;
  termKey?: string;
  value: string | null;
}) {
  return (
    <div className="flex items-center justify-between border-b border-hair/50 py-2 last:border-0">
      <span className="text-xs text-muted">
        {termKey ? <Term k={termKey}>{label}</Term> : label}
      </span>
      <span className="tnum text-sm text-ink">{value ?? "—"}</span>
    </div>
  );
}

// profitMargins / shortPercentOfFloat come back as fractions (0.1968 → 19.68%)…
const pct = (v: number | null) => (v === null ? null : `${(v * 100).toFixed(2)}%`);
// …but yfinance returns dividendYield already in percent units (2.55 → 2.55%).
const pctRaw = (v: number | null) => (v === null ? null : `${v.toFixed(2)}%`);
const num = (v: number | null, d = 2) => (v === null ? null : v.toFixed(d));

export function FundamentalsCard({ ticker }: { ticker: string }) {
  const [data, setData] = useState<Fundamentals | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getFundamentals(ticker)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [ticker]);

  return (
    <div className="card p-4">
      <h3 className="mb-2 text-sm font-semibold tracking-tight">Fundamentals</h3>
      {loading ? (
        <div className="space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-6 animate-pulse rounded bg-elevated" />
          ))}
        </div>
      ) : !data || !data.available ? (
        <p className="text-xs text-faint">
          Fundamentals unavailable for {ticker} right now (source is best-effort).
        </p>
      ) : (
        <div>
          <Metric label="Market cap" termKey="market_cap" value={data.market_cap ? `$${fmtCompact(data.market_cap)}` : null} />
          <Metric label="P/E (trailing)" termKey="pe_ratio" value={num(data.trailing_pe, 1)} />
          <Metric label="P/E (forward)" termKey="pe_ratio" value={num(data.forward_pe, 1)} />
          <Metric label="Beta" termKey="beta" value={num(data.beta)} />
          <Metric label="Dividend yield" termKey="dividends" value={pctRaw(data.dividend_yield)} />
          <Metric label="Profit margin" value={pct(data.profit_margin)} />
          <Metric label="Short % float" value={pct(data.short_percent_of_float)} />
        </div>
      )}
    </div>
  );
}
