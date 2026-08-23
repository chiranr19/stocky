// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { History, Loader2, TrendingDown } from "lucide-react";
import type { TimeMachineResult } from "@/lib/types";
import { getTimeMachine } from "@/lib/api";
import { fmtCompact, fmtCurrency, fmtDate, fmtPct, toneClass } from "@/lib/format";

const ASSET_COLOR = "#7C6BFF";
const BENCH_COLOR = "#8B929C";

function ymd(d: Date): string {
  return d.toISOString().slice(0, 10);
}
function ts(iso: string): number {
  return new Date(iso + "T00:00:00").getTime();
}

const twoYearsAgo = () => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 2);
  return ymd(d);
};
const yesterday = () => {
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return ymd(d);
};

function Stat({
  label,
  value,
  tone = "",
  hint,
}: {
  label: string;
  value: string;
  tone?: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-hair bg-elevated/50 px-3 py-2.5">
      <div className="text-[11px] uppercase tracking-wide text-faint">{label}</div>
      <div className={`tnum mt-0.5 text-lg font-semibold ${tone}`}>{value}</div>
      {hint && <div className="text-[11px] text-muted">{hint}</div>}
    </div>
  );
}

interface ChartRow {
  t: number;
  asset?: number;
  bench?: number;
}

function ChartTooltip({
  active,
  payload,
  benchTicker,
  assetTicker,
}: {
  active?: boolean;
  payload?: { payload: ChartRow }[];
  benchTicker: string;
  assetTicker: string;
}) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="rounded-lg border border-hair bg-elevated px-3 py-2 text-xs shadow-card">
      <div className="mb-1 text-faint">{fmtDate(new Date(row.t).toISOString().slice(0, 10))}</div>
      {row.asset != null && (
        <div className="flex items-center justify-between gap-4">
          <span style={{ color: ASSET_COLOR }}>{assetTicker}</span>
          <span className="tnum text-ink">{fmtCurrency(row.asset)}</span>
        </div>
      )}
      {row.bench != null && (
        <div className="flex items-center justify-between gap-4">
          <span style={{ color: BENCH_COLOR }}>{benchTicker}</span>
          <span className="tnum text-ink">{fmtCurrency(row.bench)}</span>
        </div>
      )}
    </div>
  );
}

export function TimeMachine({
  ticker,
  onTickerChange,
}: {
  ticker: string;
  onTickerChange: (t: string) => void;
}) {
  const [tickerField, setTickerField] = useState(ticker);
  const [dateField, setDateField] = useState(twoYearsAgo);
  const [amountField, setAmountField] = useState("500");

  const [data, setData] = useState<TimeMachineResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(
    async (t = tickerField, d = dateField, a = amountField) => {
      const amount = Number(a);
      if (!t.trim() || !d || !amount || amount <= 0) {
        setError("Enter a ticker, a past date, and a positive dollar amount.");
        return;
      }
      setLoading(true);
      setError(null);
      try {
        setData(await getTimeMachine(t, d, amount));
      } catch (e) {
        setData(null);
        setError(e instanceof Error ? e.message : "Something went wrong.");
      } finally {
        setLoading(false);
      }
    },
    [tickerField, dateField, amountField],
  );

  // Run once on mount with defaults.
  const didMount = useRef(false);
  useEffect(() => {
    run(ticker);
    didMount.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Re-run when a ticker is picked elsewhere (card / ⌘K palette).
  useEffect(() => {
    if (!didMount.current) return;
    setTickerField(ticker);
    run(ticker);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticker]);

  const chartData: ChartRow[] = useMemo(() => {
    if (!data) return [];
    const map = new Map<number, ChartRow>();
    for (const p of data.path) {
      const t = ts(p.date);
      map.set(t, { ...(map.get(t) ?? { t }), t, asset: p.value });
    }
    for (const p of data.benchmark.path) {
      const t = ts(p.date);
      map.set(t, { ...(map.get(t) ?? { t }), t, bench: p.value });
    }
    return [...map.values()].sort((x, y) => x.t - y.t);
  }, [data]);

  const beatBenchmark = data ? data.outperformance_pct >= 0 : false;

  return (
    <div className="card p-5">
      {/* Header */}
      <div className="mb-4 flex items-center gap-2">
        <History className="h-4 w-4 text-accent" />
        <h2 className="text-sm font-semibold tracking-tight">Time Machine</h2>
        <span className="text-xs text-faint">what if you'd invested…</span>
      </div>

      {/* Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onTickerChange(tickerField.trim().toUpperCase());
          run();
        }}
        className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4"
      >
        <label className="col-span-1 flex flex-col gap-1">
          <span className="text-[11px] text-faint">Ticker</span>
          <input
            value={tickerField}
            onChange={(e) => setTickerField(e.target.value.toUpperCase())}
            placeholder="NVDA"
            className="tnum rounded-lg border border-hair bg-elevated px-3 py-2 text-sm uppercase outline-none focus:border-accent"
          />
        </label>
        <label className="col-span-1 flex flex-col gap-1">
          <span className="text-[11px] text-faint">Date</span>
          <input
            type="date"
            value={dateField}
            max={yesterday()}
            onChange={(e) => setDateField(e.target.value)}
            className="tnum rounded-lg border border-hair bg-elevated px-3 py-2 text-sm outline-none focus:border-accent [color-scheme:dark]"
          />
        </label>
        <label className="col-span-1 flex flex-col gap-1">
          <span className="text-[11px] text-faint">Amount ($)</span>
          <input
            type="number"
            min={1}
            step={50}
            value={amountField}
            onChange={(e) => setAmountField(e.target.value)}
            className="tnum rounded-lg border border-hair bg-elevated px-3 py-2 text-sm outline-none focus:border-accent"
          />
        </label>
        <button
          type="submit"
          disabled={loading}
          className="col-span-1 mt-auto flex items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Run"}
        </button>
      </form>

      {error && (
        <div className="rounded-lg border border-down/30 bg-down/10 px-3 py-2 text-sm text-down">
          {error}
        </div>
      )}

      {data && !error && (
        <div className="animate-fade-in space-y-4">
          {/* Stat row */}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <Stat
              label="Value today"
              value={fmtCurrency(data.end_value)}
              hint={`from ${fmtCurrency(data.amount)}`}
            />
            <Stat
              label="Total return"
              value={fmtPct(data.total_return_pct)}
              tone={toneClass(data.total_return_pct)}
              hint={
                data.annualized_return_pct != null
                  ? `${fmtPct(data.annualized_return_pct)} / yr`
                  : undefined
              }
            />
            <Stat
              label={`vs ${data.benchmark.ticker}`}
              value={fmtPct(data.outperformance_pct)}
              tone={toneClass(data.outperformance_pct)}
              hint={`${data.benchmark.ticker} → ${fmtCurrency(data.benchmark.end_value)}`}
            />
            <Stat
              label="Shares"
              value={data.shares.toLocaleString("en-US", {
                maximumFractionDigits: 4,
              })}
              hint={`@ ${fmtCurrency(data.start_price)}`}
            />
          </div>

          {/* Dual-path chart */}
          <div className="rounded-lg border border-hair bg-elevated/30 p-3">
            <div className="mb-2 flex items-center gap-4 text-xs">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: ASSET_COLOR }} />
                {data.ticker}
              </span>
              <span className="flex items-center gap-1.5 text-muted">
                <span className="h-0.5 w-3" style={{ background: BENCH_COLOR }} />
                {data.benchmark.ticker} (benchmark)
              </span>
              <span className="ml-auto text-faint">
                {fmtDate(data.start_date)} → {fmtDate(data.end_date)}
              </span>
            </div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
                <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis
                  dataKey="t"
                  type="number"
                  scale="time"
                  domain={["dataMin", "dataMax"]}
                  tickFormatter={(t) => fmtDate(new Date(t).toISOString().slice(0, 10))}
                  tick={{ fill: "#5A616B", fontSize: 11 }}
                  minTickGap={48}
                  stroke="rgba(255,255,255,0.08)"
                />
                <YAxis
                  tickFormatter={(v) => `$${fmtCompact(v)}`}
                  tick={{ fill: "#5A616B", fontSize: 11 }}
                  width={52}
                  stroke="rgba(255,255,255,0.08)"
                  domain={["auto", "auto"]}
                />
                <Tooltip
                  content={
                    <ChartTooltip
                      assetTicker={data.ticker}
                      benchTicker={data.benchmark.ticker}
                    />
                  }
                />
                {/* The dip that would've scared you out. */}
                <ReferenceArea
                  x1={ts(data.max_drawdown.peak_date)}
                  x2={ts(data.max_drawdown.trough_date)}
                  fill="#F6465D"
                  fillOpacity={0.1}
                  stroke="#F6465D"
                  strokeOpacity={0.25}
                />
                <Line
                  type="monotone"
                  dataKey="bench"
                  stroke={BENCH_COLOR}
                  strokeWidth={1.5}
                  strokeDasharray="4 3"
                  dot={false}
                  connectNulls
                  animationDuration={900}
                />
                <Line
                  type="monotone"
                  dataKey="asset"
                  stroke={ASSET_COLOR}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                  animationDuration={900}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Drawdown callout */}
          <div className="flex items-start gap-2 rounded-lg border border-down/25 bg-down/5 px-3 py-2.5 text-sm">
            <TrendingDown className="mt-0.5 h-4 w-4 shrink-0 text-down" />
            <div>
              <span className="font-medium text-down">
                Max drawdown {fmtPct(data.max_drawdown.drawdown_pct)}
              </span>{" "}
              <span className="text-muted">
                ({fmtDate(data.max_drawdown.peak_date)} →{" "}
                {fmtDate(data.max_drawdown.trough_date)}) — this is the dip that
                would&apos;ve scared you out. Sitting through it is the whole game.
              </span>
            </div>
          </div>

          <p className="text-xs text-faint">
            {beatBenchmark
              ? `${data.ticker} beat ${data.benchmark.ticker} by ${fmtPct(
                  data.outperformance_pct,
                )} over this window — but look at the drawdown you'd have had to stomach.`
              : `You'd have done ${fmtPct(
                  Math.abs(data.outperformance_pct),
                  false,
                )} worse than just buying ${data.benchmark.ticker} — the opportunity cost of a single-name bet.`}
          </p>
        </div>
      )}
    </div>
  );
}
