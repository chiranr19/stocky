"use client";

import { useCallback, useEffect, useState } from "react";
import { GitCompare, Plus, X } from "lucide-react";
import { getCompare } from "@/lib/api";
import type { CompareResponse } from "@/lib/types";
import { fmtPct, toneClass } from "@/lib/format";
import { SectionHeader } from "@/components/ui/primitives";
import { Term } from "@/components/ui/Term";
import { TeachBanner } from "@/components/learn/TeachBanner";
import { ErrorCard, Loading } from "@/components/ui/States";
import { NormalizedChart, colorFor } from "@/components/compare/NormalizedChart";
import { CorrelationGrid } from "@/components/compare/CorrelationGrid";
import { DistributionBars } from "@/components/compare/DistributionBars";

const BENCHMARK = "VOO";

export default function ComparePage() {
  const [tickers, setTickers] = useState<string[]>(["NVDA", "AMD"]);
  const [input, setInput] = useState("");
  const [data, setData] = useState<CompareResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback((list: string[]) => {
    if (list.length === 0) {
      setData(null);
      return;
    }
    setLoading(true);
    setError(null);
    getCompare(list)
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    run(tickers);
  }, [tickers, run]);

  const add = () => {
    const t = input.trim().toUpperCase();
    if (t && !tickers.includes(t) && t !== BENCHMARK && tickers.length < 3) {
      setTickers([...tickers, t]);
    }
    setInput("");
  };
  const remove = (t: string) => setTickers(tickers.filter((x) => x !== t));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Compare</h1>
        <p className="text-sm text-muted">
          Put up to 3 stocks head-to-head against{" "}
          <Term k="voo">VOO</Term> — growth, risk, and how alike they really are.
        </p>
      </div>

      {/* Picker */}
      <div className="card flex flex-wrap items-center gap-2 p-3">
        {tickers.map((t, i) => (
          <span
            key={t}
            className="flex items-center gap-1.5 rounded-lg border border-hair bg-elevated px-2.5 py-1.5 text-sm"
          >
            <span className="h-2 w-2 rounded-full" style={{ background: colorFor(t, i, BENCHMARK) }} />
            <span className="tnum font-medium">{t}</span>
            <button onClick={() => remove(t)} className="text-faint hover:text-down">
              <X className="h-3.5 w-3.5" />
            </button>
          </span>
        ))}
        <span className="flex items-center gap-1.5 rounded-lg border border-dashed border-hair px-2.5 py-1.5 text-sm text-faint">
          <span className="h-2 w-2 rounded-full bg-muted" />
          VOO <span className="text-[10px]">(always)</span>
        </span>
        {tickers.length < 3 && (
          <div className="flex items-center gap-1">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && add()}
              placeholder="add ticker"
              className="tnum w-28 rounded-lg border border-hair bg-elevated px-2.5 py-1.5 text-sm uppercase outline-none focus:border-accent"
            />
            <button
              onClick={add}
              className="rounded-lg bg-accent p-2 text-white transition-opacity hover:opacity-90"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>

      {error && <ErrorCard message={error} onRetry={() => run(tickers)} />}
      {loading && !data && <Loading label="Crunching the comparison…" />}

      {data && (
        <>
          <section>
            <SectionHeader icon={GitCompare} title="Growth of an equal investment" termKey="opportunity_cost" />
            <TeachBanner>
              Every line starts at 100 on the same day, so you&apos;re comparing{" "}
              <span className="text-ink">percentage journeys</span>, not share prices. The
              gap to VOO is your <Term k="opportunity_cost">opportunity cost</Term>.
            </TeachBanner>
            <NormalizedChart series={data.series} benchmark={BENCHMARK} />
          </section>

          <section className="grid gap-3 lg:grid-cols-[1.3fr_1fr]">
            <StatTable data={data} />
            <CorrelationGrid corr={data.correlation} />
          </section>

          <section>
            <SectionHeader title="Return distributions" termKey="volatility" sub="wider = more volatile" />
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {data.stats.map((s, i) => (
                <DistributionBars
                  key={s.ticker}
                  hist={data.histograms[s.ticker] ?? { counts: [], edges: [] }}
                  color={colorFor(s.ticker, i, BENCHMARK)}
                  label={s.ticker}
                />
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function StatTable({ data }: { data: CompareResponse }) {
  const cols: { key: string; label: string; term?: string; fmt: (s: (typeof data.stats)[0]) => React.ReactNode }[] = [
    { key: "total", label: "Total return", term: "total_return", fmt: (s) => <span className={toneClass(s.total_return_pct ?? 0)}>{s.total_return_pct != null ? fmtPct(s.total_return_pct) : "—"}</span> },
    { key: "ann", label: "Annualized", term: "annualized_return", fmt: (s) => <span className={toneClass(s.annualized_return_pct ?? 0)}>{s.annualized_return_pct != null ? fmtPct(s.annualized_return_pct) : "—"}</span> },
    { key: "vol", label: "Volatility", term: "volatility", fmt: (s) => <span>{s.vol_90d != null ? `${s.vol_90d}%` : "—"}</span> },
    { key: "dd", label: "Max drawdown", term: "drawdown", fmt: (s) => <span className="text-down">{fmtPct(s.max_drawdown_pct)}</span> },
  ];

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hair text-left text-[11px] uppercase tracking-wide text-faint">
              <th className="px-4 py-2.5 font-medium">Stock</th>
              {cols.map((c) => (
                <th key={c.key} className="px-3 py-2.5 text-right font-medium">
                  {c.term ? <Term k={c.term}>{c.label}</Term> : c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.stats.map((s) => (
              <tr key={s.ticker} className="border-b border-hair/50 last:border-0">
                <td className="px-4 py-2.5">
                  <div className="tnum font-medium">{s.ticker}</div>
                  <div className="truncate text-xs text-faint">{s.name}</div>
                </td>
                {cols.map((c) => (
                  <td key={c.key} className="tnum px-3 py-2.5 text-right">
                    {c.fmt(s)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
