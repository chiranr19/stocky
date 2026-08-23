// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, ArrowRight, Clock, Crosshair, GraduationCap, TrendingDown, TrendingUp } from "lucide-react";
import { getLearnBasket, getStock } from "@/lib/api";
import type { BasketMember, StockDetail } from "@/lib/types";
import { fmtCompact, fmtCurrency, fmtPct, toneClass } from "@/lib/format";
import { ChangePct, RangeBar, ScoreBadge, SectionHeader, StatTile } from "@/components/ui/primitives";
import { ConePanel } from "@/components/study/ConePanel";
import { StudyLede } from "@/components/study/StudyLede";
import { STUDY } from "@/lib/studyCopy";
import { Term } from "@/components/ui/Term";
import { ErrorCard, Loading } from "@/components/ui/States";
import { CandleChart } from "@/components/stock/CandleChart";
import { EchoChip, KnifeChip } from "@/components/radar/RadarList";
import { Readings } from "@/components/learn/Readings";
import { FlagChips, FlagPanel } from "@/components/flags/Flags";
import { RsiPanel } from "@/components/stock/RsiPanel";
import { FundamentalsCard } from "@/components/stock/FundamentalsCard";
import { DistributionBars } from "@/components/compare/DistributionBars";

const FACTOR_INFO: Record<string, { label: string; term: string; blurb: string }> = {
  momentum: { label: "Momentum", term: "momentum", blurb: "3-month return vs peers, trend-confirmed." },
  stability: { label: "Stability", term: "volatility", blurb: "Inverse of volatility — calmer ride ranks higher." },
  resilience: { label: "Resilience", term: "drawdown", blurb: "Shallower 1-year drawdown ranks higher." },
  liquidity: { label: "Liquidity", term: "liquidity", blurb: "Dollar volume — how easily you can trade it." },
};

export default function StockPage() {
  const params = useParams();
  const ticker = String(params.ticker || "").toUpperCase();
  const [data, setData] = useState<StockDetail | null>(null);
  const [role, setRole] = useState<BasketMember | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!ticker) return;
    setData(null);
    setError(null);
    setRole(null);
    getStock(ticker).then(setData).catch((e) => setError(e.message));
    // Curated watchlist role, if this ticker is one of the cast (cached fetch,
    // shared with /learn). A miss is silent — most tickers aren't on the list.
    getLearnBasket()
      .then((b) => setRole(b.members.find((m) => m.ticker === ticker && m.role_story) ?? null))
      .catch(() => setRole(null));
  }, [ticker]);

  if (error) return <ErrorCard message={error} />;
  if (!data) return <Loading label={`Loading ${ticker}…`} />;

  const r = data.row;

  return (
    <div className="space-y-6">
      <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-ink">
        <ArrowLeft className="h-3.5 w-3.5" /> Back to Pulse
      </Link>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold tracking-tight">{data.ticker}</h1>
            {r.score !== null && <ScoreBadge score={r.score} size="lg" />}
            {r.cross === "golden" && <TrendingUp className="h-5 w-5 text-up" />}
            {r.cross === "death" && <TrendingDown className="h-5 w-5 text-down" />}
          </div>
          <p className="text-sm text-muted">
            {data.name}
            {data.sector && <> · <Term k="sector">{data.sector}</Term></>}
            {data.sub_industry && <span className="text-faint"> · {data.sub_industry}</span>}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="tnum text-2xl font-semibold">{fmtCurrency(r.price)}</div>
            <ChangePct value={r.change_pct} className="justify-end text-sm" />
          </div>
          <Link
            href={`/time-machine?ticker=${data.ticker}`}
            className="flex items-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90"
          >
            <Clock className="h-4 w-4" /> Time Machine
          </Link>
        </div>
      </div>

      {/* Metrics grid */}
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        <StatTile label="RSI (14)" termKey="rsi" value={r.rsi14?.toFixed(0) ?? "—"} tone={r.rsi14 ? (r.rsi14 >= 70 ? "text-up" : r.rsi14 <= 30 ? "text-down" : "") : ""} />
        <StatTile label="Volatility" termKey="volatility" value={r.vol_90d != null ? `${r.vol_90d}%` : "—"} />
        <StatTile label="1M" termKey="total_return" value={r.ret_1m != null ? fmtPct(r.ret_1m) : "—"} tone={toneClass(r.ret_1m ?? 0)} />
        <StatTile label="3M" termKey="momentum" value={r.ret_3m != null ? fmtPct(r.ret_3m) : "—"} tone={toneClass(r.ret_3m ?? 0)} />
        <StatTile label="1Y" termKey="total_return" value={r.ret_1y != null ? fmtPct(r.ret_1y) : "—"} tone={toneClass(r.ret_1y ?? 0)} />
        <StatTile label="Max drawdown" termKey="drawdown" value={fmtPct(r.max_drawdown_1y)} tone="text-down" />
      </div>

      {/* 52w range + trend flags */}
      <div className="card flex flex-wrap items-center gap-6 p-4">
        <div className="min-w-[220px] flex-1">
          <div className="mb-1 flex justify-between text-xs">
            <span className="text-faint"><Term k="range_52w">52-week range</Term></span>
            <span className="tnum text-muted">{Math.round(r.range_52w_position * 100)}%</span>
          </div>
          <RangeBar position={r.range_52w_position} />
        </div>
        <div className="flex gap-4 text-xs">
          <span className={r.above_ma50 ? "text-up" : "text-down"}>
            {r.above_ma50 ? "Above" : "Below"} <Term k="moving_average">MA50</Term>
          </span>
          <span className={r.above_ma200 ? "text-up" : "text-down"}>
            {r.above_ma200 ? "Above" : "Below"} <Term k="moving_average">MA200</Term>
          </span>
          <span className="text-muted">
            <Term k="dollar_volume">$Vol</Term> {fmtCompact(r.avg_dollar_volume)}
          </span>
        </div>
      </div>

      {/* Entry position (Entry Radar lens, 3M lookback) */}
      <div className="card flex flex-wrap items-center gap-x-6 gap-y-3 p-4">
        <div className="flex items-center gap-2">
          <Crosshair className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-semibold tracking-tight">
            <Term k="pullback">Entry position</Term>
          </h3>
        </div>
        {data.entry ? (
          <>
            <div className="text-xs text-muted">
              <span className="tnum font-semibold text-down">
                −{data.entry.depth_pct.toFixed(1)}%
              </span>{" "}
              below its 3-month high — deeper than{" "}
              <span className="tnum text-ink">{data.entry.depth_rank.toFixed(0)}%</span>{" "}
              of its own history
            </div>
            {data.entry.falling_knife && <KnifeChip />}
            <div className="ml-auto flex items-center gap-4">
              <EchoChip r={data.entry} />
              <Link
                href="/radar"
                className="flex items-center gap-1 text-xs text-muted transition-colors hover:text-accent"
              >
                All setups <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          </>
        ) : (
          <p className="text-xs text-faint">
            No meaningful <Term k="pullback">pullback</Term> right now — {data.ticker} is
            trading within ~5% of its 3-month high (or has too little history to judge).
          </p>
        )}
      </div>

      {/* Its role in your watchlist — the curated teaching story */}
      {role && (
        <div className="card overflow-hidden p-4">
          <div className="mb-1.5 flex items-center gap-2">
            <GraduationCap className="h-4 w-4 text-accent" />
            <h3 className="text-sm font-semibold tracking-tight">Its role in your watchlist</h3>
            <span className="rounded-md border border-accent/30 bg-accent/10 px-1.5 py-0.5 text-[11px] font-medium text-accent">
              {role.role}
            </span>
          </div>
          <p className="text-sm leading-relaxed text-muted">{role.role_story}</p>
          {role.role_lesson && (
            <p className="mt-2 border-t border-hair pt-2 text-xs leading-relaxed text-ink/80">
              <span className="font-medium text-accent">The lesson: </span>
              {role.role_lesson}
            </p>
          )}
          <p className="mt-2 text-[11px] text-faint">
            A hand-written story to build intuition — the numbers inside it are frozen to
            when it was written; the live figures above are current.{" "}
            <Link href="/learn" className="text-muted underline-offset-2 hover:text-accent hover:underline">
              See the whole cast →
            </Link>
          </p>
        </div>
      )}

      {/* The reading layer — what this chart actually means */}
      <Readings
        readings={data.readings}
        title={`How to read ${data.ticker} right now`}
        columns={2}
      />

      {/* Named good/bad patterns */}
      <FlagPanel flags={data.flags} />

      {/* Candles + RSI */}
      <CandleChart candles={data.candles} ma50={data.ma50} ma200={data.ma200} />
      <RsiPanel rsi={data.rsi} />

      {/* The honest forecast — a cone of plausible futures from its own past moves */}
      <section>
        <SectionHeader title={STUDY.cone.eyebrow} termKey="volatility" sub="a range of futures, never a call" />
        <StudyLede copy={STUDY.cone} />
        <ConePanel ticker={data.ticker} />
      </section>

      {/* Score breakdown + fundamentals */}
      <div className="grid gap-3 lg:grid-cols-[1.3fr_1fr]">
        <div className="card p-4">
          <div className="mb-1 flex items-center justify-between">
            <h3 className="text-sm font-semibold tracking-tight">
              <Term k="score">Stocky score</Term>
            </h3>
            {r.score !== null ? <ScoreBadge score={r.score} size="lg" /> : null}
          </div>
          {r.factors ? (
            <div className="mt-3 space-y-3">
              {Object.entries(FACTOR_INFO).map(([key, info]) => {
                const v = r.factors?.[key] ?? 0;
                return (
                  <div key={key}>
                    <div className="mb-1 flex items-center justify-between text-xs">
                      <span className="text-ink">
                        <Term k={info.term}>{info.label}</Term>
                      </span>
                      <span className="tnum text-muted">{v.toFixed(0)}</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-elevated">
                      <div className="h-full rounded-full bg-accent" style={{ width: `${v}%` }} />
                    </div>
                    <div className="mt-0.5 text-[11px] text-faint">{info.blurb}</div>
                  </div>
                );
              })}
              <p className="pt-1 text-[11px] text-faint">
                Ranked within {data.sector}. Backward-looking — a transparent starting
                point, <b>not</b> a recommendation.
              </p>
            </div>
          ) : (
            <p className="mt-2 text-xs text-faint">
              {data.ticker} isn&apos;t in the affordable screen (price above your cap, or
              too little history to score). It&apos;s still fully analyzable here.
            </p>
          )}
        </div>

        <FundamentalsCard ticker={data.ticker} />
      </div>

      {/* Return distribution vs VOO */}
      <section>
        <h3 className="mb-2 text-sm font-semibold tracking-tight">
          <Term k="volatility">Return distribution</Term> vs the market
        </h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <DistributionBars hist={data.histogram} color="#7C6BFF" label={data.ticker} />
          <DistributionBars hist={data.benchmark_histogram} color="#8B929C" label="VOO (market)" />
        </div>
        <p className="mt-2 text-xs text-faint">
          A wider spread of daily moves means a wilder ride. Compare how far{" "}
          {data.ticker}&apos;s bars fan out versus VOO&apos;s.
        </p>
      </section>
    </div>
  );
}
