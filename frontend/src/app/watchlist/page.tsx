// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, Star } from "lucide-react";
import { clearApiCache, getLearnBasket, getOverview, getWatchlist } from "@/lib/api";
import type { BasketResponse, OverviewResponse, WatchlistResponse } from "@/lib/types";
import { ErrorCard, Loading, WarmingNotice } from "@/components/ui/States";
import { SectionHeader } from "@/components/ui/primitives";
import { WeatherStation } from "@/components/weather/WeatherStation";
import { BasketMap } from "@/components/learn/BasketMap";
import { RoleLegend } from "@/components/learn/RoleLegend";
import { WhatChangedFeed } from "@/components/watchlist/WhatChangedFeed";
import { WatchTable } from "@/components/watchlist/WatchTable";
import { AddTickerBox, HiddenStrip } from "@/components/watchlist/AddTickerBox";
import { RaceChart } from "@/components/study/RaceChart";
import { RainGallery } from "@/components/study/RainGallery";
import { Constellation } from "@/components/study/Constellation";
import { ConeSection } from "@/components/study/ConeSection";
import { StudyLede } from "@/components/study/StudyLede";
import { STUDY } from "@/lib/studyCopy";
import { fmtLens, useLens } from "@/lib/lens";
import type { BasketMember, CorrelationMatrix } from "@/lib/types";

function bestWorst1y(members: BasketMember[]) {
  const m = members.filter((x) => x.measurable && x.ret_1y != null && x.group !== "benchmark");
  if (m.length < 2) return null;
  const s = [...m].sort((a, b) => (b.ret_1y as number) - (a.ret_1y as number));
  return { best: s[0], worst: s[s.length - 1] };
}
function calmWild(members: BasketMember[]) {
  const m = members.filter((x) => x.measurable && x.vol_90d != null && x.group !== "benchmark");
  if (m.length < 2) return null;
  const s = [...m].sort((a, b) => (a.vol_90d as number) - (b.vol_90d as number));
  return { calm: s[0], wild: s[s.length - 1] };
}
function tightestPair(corr: CorrelationMatrix) {
  let best: { a: string; b: string; r: number } | null = null;
  for (let i = 0; i < corr.labels.length; i++) {
    for (let j = i + 1; j < corr.labels.length; j++) {
      const r = corr.matrix[i]?.[j];
      if (r != null && (best === null || r > best.r)) {
        best = { a: corr.labels[i], b: corr.labels[j], r };
      }
    }
  }
  return best;
}

export default function WatchlistPage() {
  const { lens } = useLens();
  const [basket, setBasket] = useState<BasketResponse | null>(null);
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [wl, setWl] = useState<WatchlistResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    getLearnBasket().then(setBasket).catch((e) => setError(e.message));
    getWatchlist().then(setWl).catch(() => setWl(null));
  }, []);

  useEffect(() => {
    getOverview().then(setOverview).catch(() => setOverview(null));
    load();
  }, [load]);

  // After any add/remove: drop cached analytics payloads and refetch everything.
  const refetch = useCallback(() => {
    clearApiCache();
    load();
  }, [load]);

  const removeTicker = useCallback(
    async (ticker: string) => {
      const { removeFromWatchlist } = await import("@/lib/api");
      await removeFromWatchlist(ticker).catch(() => {});
      refetch();
    },
    [refetch],
  );

  return (
    <div className="space-y-8">
      <div>
        <div className="flex items-center gap-2 text-accent">
          <Star className="h-5 w-5" />
          <span className="text-[11px] font-semibold uppercase tracking-[0.15em]">Watchlist</span>
        </div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">Your living watchlist</h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Everything about your names in one place — what changed today, the weather they trade in,
          where each one sits on the risk map, and the numbers, sortable any way you like.
        </p>
      </div>

      <WarmingNotice />

      {error ? (
        <ErrorCard message={error} onRetry={refetch} />
      ) : !basket ? (
        <Loading label="Gathering your watchlist…" />
      ) : (
        <>
          {/* 1 — What changed */}
          <section>
            <SectionHeader title="What changed" sub="since yesterday, on your names" />
            <WhatChangedFeed events={basket.events} />
          </section>

          {/* 2 — Market weather */}
          {overview && (
            <section>
              <SectionHeader title="Market weather" termKey="vix" sub="the conditions your names trade in" />
              <WeatherStation tiles={overview.tiles} breadth={overview.breadth} readings={overview.readings} />
            </section>
          )}

          {/* 3 — The map */}
          <section>
            <SectionHeader title="Risk vs reward" termKey="benchmark" sub="up-and-left of VOO is the dream corner" />
            <BasketMap members={basket.members} />
          </section>

          {/* 4 — The year they ran (race + trend barcode) */}
          <section>
            <SectionHeader title={STUDY.race.eyebrow} sub="a year of price, one starting line" />
            <StudyLede
              copy={STUDY.race}
              computed={(() => {
                const bw = bestWorst1y(basket.members);
                if (!bw) return null;
                return (
                  <>
                    Over the past year, {bw.best.ticker} ran furthest ({fmtLens(bw.best.ret_1y, lens)})
                    and {bw.worst.ticker} trailed ({fmtLens(bw.worst.ret_1y, lens)}).
                  </>
                );
              })()}
            />
            <RaceChart members={basket.members} />
          </section>

          {/* 5 — Their daily weather (rain gallery) */}
          <section>
            <SectionHeader title={STUDY.rain.eyebrow} sub="sixty days of moves, as weather" />
            <StudyLede
              copy={STUDY.rain}
              computed={(() => {
                const cw = calmWild(basket.members);
                if (!cw) return null;
                return (
                  <>
                    {cw.calm.ticker} traded calmest (≈{cw.calm.vol_90d}% swings) and {cw.wild.ticker}{" "}
                    wildest (≈{cw.wild.vol_90d}%) — watch the clusters versus the scatter.
                  </>
                );
              })()}
            />
            <RainGallery members={basket.members} rainDates={basket.rain_dates} />
          </section>

          {/* 6 — The constellation */}
          <section>
            <SectionHeader title={STUDY.constellation.eyebrow} sub="who moves with whom" />
            <StudyLede
              copy={STUDY.constellation}
              computed={(() => {
                const tp = tightestPair(basket.correlation);
                if (!tp) return null;
                return (
                  <>
                    {tp.a} and {tp.b} move almost in lockstep ({tp.r.toFixed(2)}); the stars sitting
                    far apart are your real diversification.
                  </>
                );
              })()}
            />
            <Constellation
              data={basket.constellation}
              members={basket.members}
              correlation={basket.correlation}
              note={basket.correlation_note}
            />
          </section>

          {/* 7 — The honest forecast (cone) */}
          <section>
            <SectionHeader title={STUDY.cone.eyebrow} sub="a range of futures, never a call" />
            <StudyLede copy={STUDY.cone} />
            <ConeSection members={basket.members} />
          </section>

          {/* 8 — The table */}
          <section>
            <SectionHeader title="Every name, sortable" sub="needs-attention first" />
            <WatchTable members={basket.members} onRemove={removeTicker} />
          </section>

          {/* 9 — Manage */}
          <section className="space-y-3">
            <SectionHeader title="Manage your list" sub="add anything; remove anything (restorable)" />
            <AddTickerBox onChanged={refetch} />
            {wl && <HiddenStrip hidden={wl.hidden} onChanged={refetch} />}
          </section>

          {/* 10 — The cast + the lessons */}
          <section>
            <div className="mb-4 flex items-center justify-between">
              <SectionHeader title="The cast" sub="every name and the role it plays" />
              <Link href="/learn" className="flex shrink-0 items-center gap-1 text-xs text-muted hover:text-accent">
                Take the six lessons <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            <RoleLegend members={basket.members} laws={basket.laws} />
          </section>

          <p className="border-t border-hair pt-4 text-xs text-faint">
            Educational tool for building market intuition — not financial advice. Every number here
            describes what the data shows and where it can fool you, never what to buy.
          </p>
        </>
      )}
    </div>
  );
}
