"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowRight,
  Crosshair,
  Flame,
  Grid3x3,
  ShieldAlert,
  Star,
} from "lucide-react";
import {
  getMovers,
  getOverview,
  getPulse,
  getRadar,
  getSectors,
  getWatchouts,
} from "@/lib/api";
import { useBudget } from "@/lib/budget";
import type {
  OverviewResponse,
  PulseResponse,
  RadarResponse,
  SectorsResponse,
  StockRow,
  WatchoutsResponse,
} from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { SectionHeader } from "@/components/ui/primitives";
import { StartHere } from "@/components/learn/StartHere";
import { TeachBanner } from "@/components/learn/TeachBanner";
import { MarketStrip } from "@/components/overview/MarketStrip";
import { SectorHeatmapStrip } from "@/components/sectors/SectorHeatmapStrip";
import { SectorSection } from "@/components/sectors/SectorSection";
import { WatchlistStrip } from "@/components/pulse/WatchlistStrip";
import { StockRowItem } from "@/components/stocks/StockRowItem";
import { RadarRowItem } from "@/components/radar/RadarList";
import { Readings } from "@/components/learn/Readings";
import { WatchoutRowItem } from "@/components/watchouts/WatchoutList";
import { ErrorCard, WarmingNotice } from "@/components/ui/States";

export default function PulsePage() {
  const { budget } = useBudget();
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [pulse, setPulse] = useState<PulseResponse | null>(null);
  const [sectors, setSectors] = useState<SectorsResponse | null>(null);
  const [movers, setMovers] = useState<StockRow[] | null>(null);
  const [radar, setRadar] = useState<RadarResponse | null>(null);
  const [watchouts, setWatchouts] = useState<WatchoutsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setError(null);
    getOverview().then(setOverview).catch((e) => setError(e.message));
    getPulse().then(setPulse).catch(() => {});
  }, []);

  useEffect(load, [load]);

  useEffect(() => {
    getSectors(budget).then(setSectors).catch(() => {});
    getMovers("gainers", budget, 6).then(setMovers).catch(() => {});
    getRadar(budget, "3m", 12).then(setRadar).catch(() => {});
    getWatchouts(budget, 8).then(setWatchouts).catch(() => {});
  }, [budget]);

  if (error && !overview) return <ErrorCard message={error} onRetry={load} />;

  return (
    <div className="space-y-10">
      {/* Intro */}
      {/* Stacks on phones — side by side the heading collapses to a few chars wide. */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Market Pulse</h1>
          <p className="text-sm text-muted">
            The whole market at a glance{overview ? ` · as of ${fmtDate(overview.as_of)}` : ""}.
          </p>
        </div>
        <StartHere />
      </div>

      <WarmingNotice />

      {/* Market overview */}
      <section>
        <SectionHeader icon={Activity} title="Market overview" termKey="benchmark" />
        <TeachBanner>
          Check the weather before picking stocks: is the whole market up or down, is{" "}
          fear (<span className="text-ink">VIX</span>) high, and is participation{" "}
          <span className="text-ink">broad or narrow</span>?
        </TeachBanner>
        {overview ? (
          <div className="space-y-3">
            <MarketStrip tiles={overview.tiles} breadth={overview.breadth} />
            <Readings
              readings={overview.readings}
              title="What today's market picture means"
              columns={2}
            />
          </div>
        ) : (
          <SkeletonRow />
        )}
      </section>

      {/* Entry Radar preview */}
      <section>
        <SectionHeader
          icon={Crosshair}
          title="Entry Radar"
          termKey="pullback"
          sub="dips worth studying, validated by history"
          right={
            <Link
              href="/radar"
              className="flex items-center gap-1 text-xs text-muted transition-colors hover:text-accent"
            >
              Open Entry Radar <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          }
        />
        <TeachBanner>
          Affordable stocks pulled back from their 3-month high with the long trend
          intact — plus the <span className="text-ink">base rate</span>: what each stock
          actually did after similar dips. Setups to study, <b>not</b> buy signals.
        </TeachBanner>
        <div className="card p-1.5">
          {radar ? (
            radar.rows.filter((r) => !r.falling_knife).length ? (
              radar.rows
                .filter((r) => !r.falling_knife)
                .slice(0, 5)
                .map((r, i) => <RadarRowItem key={r.row.ticker} r={r} rank={i + 1} />)
            ) : (
              <div className="px-3 py-6 text-center text-sm text-faint">
                No trend-intact pullbacks at this budget right now — most names are near
                their highs. That&apos;s worth knowing too.
              </div>
            )
          ) : (
            <SkeletonRow />
          )}
        </div>
      </section>

      {/* The contrast: what a poor setup looks like */}
      <section>
        <SectionHeader
          icon={ShieldAlert}
          title="Watch-outs"
          sub="the same market, filtered for hazards"
          right={
            <Link
              href="/watchouts"
              className="flex items-center gap-1 text-xs text-muted transition-colors hover:text-accent"
            >
              See all watch-outs <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          }
        />
        <TeachBanner>
          Set against the radar above: these carry named hazards — broken trends, value
          traps, volatility that wasn&apos;t paid for. Comparing the two lists is the
          fastest way to learn what separates a dip from a trap. A <b>teaching list</b>,
          not a sell list.
        </TeachBanner>
        <div className="card p-1.5">
          {watchouts ? (
            watchouts.rows.length ? (
              watchouts.rows
                .slice(0, 5)
                .map((r, i) => (
                  <WatchoutRowItem key={r.row.ticker} r={r} rank={i + 1} />
                ))
            ) : (
              <div className="px-3 py-6 text-center text-sm text-faint">
                Nothing at this budget is carrying the standard risk patterns.
              </div>
            )
          ) : (
            <SkeletonRow />
          )}
        </div>
      </section>

      {/* Sector pulse */}
      <section>
        <SectionHeader
          icon={Grid3x3}
          title="Sector pulse"
          termKey="sector"
          sub="affordable, ranked — click a tile to jump"
        />
        <TeachBanner>
          Each sector broken into the best affordable names by{" "}
          <span className="text-ink">Stocky score</span> — a transparent blend of momentum,
          stability, resilience and liquidity. Ranked to learn from, <b>not</b> a
          recommendation.
        </TeachBanner>
        {sectors ? (
          <>
            <div className="mb-4">
              <SectorHeatmapStrip sectors={sectors.sectors} />
            </div>
            <div className="grid gap-3 lg:grid-cols-2">
              {sectors.sectors.map((p) => (
                <SectorSection key={p.etf} panel={p} />
              ))}
            </div>
          </>
        ) : (
          <SkeletonRow />
        )}
      </section>

      {/* Movers preview */}
      <section>
        <SectionHeader
          icon={Flame}
          title="Today's movers"
          sub="biggest affordable gainers"
          right={
            <Link
              href="/explore"
              className="flex items-center gap-1 text-xs text-muted transition-colors hover:text-accent"
            >
              All scanners <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          }
        />
        <div className="card p-1.5">
          {movers?.length ? (
            movers.map((r) => <StockRowItem key={r.ticker} row={r} />)
          ) : (
            <div className="px-3 py-6 text-center text-sm text-faint">No movers yet.</div>
          )}
        </div>
      </section>

      {/* Watchlist */}
      <section>
        <SectionHeader icon={Star} title="Watchlist" sub="seeded highlights" />
        {pulse ? (
          <WatchlistStrip cards={pulse.watchlist} />
        ) : (
          <SkeletonRow />
        )}
      </section>
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-28 animate-pulse rounded-xl border border-hair bg-panel" />
      ))}
    </div>
  );
}
