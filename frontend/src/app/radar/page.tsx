"use client";

import { useEffect, useMemo, useState } from "react";
import { Crosshair } from "lucide-react";
import { getRadar } from "@/lib/api";
import { useBudget } from "@/lib/budget";
import type { RadarResponse } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { SectionHeader } from "@/components/ui/primitives";
import { TeachBanner } from "@/components/learn/TeachBanner";
import { Term } from "@/components/ui/Term";
import { WarmingNotice, Loading } from "@/components/ui/States";
import { MethodCard, RadarRowItem } from "@/components/radar/RadarList";

type Lookback = "1m" | "2m" | "3m";
const LOOKBACKS: { key: Lookback; label: string }[] = [
  { key: "1m", label: "1 month" },
  { key: "2m", label: "2 months" },
  { key: "3m", label: "3 months" },
];

export default function RadarPage() {
  const { budget } = useBudget();
  const [lookback, setLookback] = useState<Lookback>("3m");
  const [hideKnives, setHideKnives] = useState(true);
  const [data, setData] = useState<RadarResponse | null>(null);

  useEffect(() => {
    setData(null);
    getRadar(budget, lookback, 50).then(setData).catch(() => {});
  }, [budget, lookback]);

  const rows = useMemo(
    () => (data ? data.rows.filter((r) => !hideKnives || !r.falling_knife) : []),
    [data, hideKnives],
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Entry Radar</h1>
        <p className="text-sm text-muted">
          Affordable stocks in a <Term k="pullback">pullback</Term> — ranked to study,
          validated against their own history{data ? ` · as of ${fmtDate(data.as_of)}` : ""}.
        </p>
      </div>

      <WarmingNotice />

      <TeachBanner>
        A dip in an intact uptrend is a <span className="text-ink">setup worth studying</span> —
        not a promise. The right-hand column shows the <Term k="base_rate">base rate</Term>:
        what this exact stock actually did after dips like today&apos;s. Small samples and
        broken trends are exactly where this lens lies to you.
      </TeachBanner>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex overflow-hidden rounded-lg border border-hair">
          {LOOKBACKS.map((l) => (
            <button
              key={l.key}
              onClick={() => setLookback(l.key)}
              className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                lookback === l.key
                  ? "bg-accent text-white"
                  : "bg-panel text-muted hover:text-ink"
              }`}
            >
              {l.label}
            </button>
          ))}
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-xs text-muted">
          <input
            type="checkbox"
            checked={hideKnives}
            onChange={(e) => setHideKnives(e.target.checked)}
            className="h-3.5 w-3.5 rounded border-hair bg-elevated accent-[#7C6BFF]"
          />
          Hide <Term k="falling_knife">falling knives</Term>
        </label>
        {data && (
          <span className="tnum ml-auto text-xs text-faint">
            {rows.length} setups{hideKnives && data ? ` · ${data.rows.length - rows.length} knives hidden` : ""}
          </span>
        )}
      </div>

      {/* Ranked list */}
      <section>
        <SectionHeader
          icon={Crosshair}
          title="Pullback setups"
          termKey="entry_score"
          sub={`ranked by entry score · dip vs ${lookback.toUpperCase()} high`}
        />
        <div className="card p-1.5">
          {!data ? (
            <Loading label="Measuring pullbacks across the universe…" />
          ) : rows.length === 0 ? (
            <div className="px-3 py-10 text-center text-sm text-faint">
              No qualifying pullbacks right now
              {hideKnives ? " (try showing falling knives, or widen the lookback)" : ""}.
              In a strong market that&apos;s normal — most names are near their highs.
            </div>
          ) : (
            rows.map((r, i) => <RadarRowItem key={r.row.ticker} r={r} rank={i + 1} />)
          )}
        </div>
      </section>

      {data && <MethodCard data={data} />}
    </div>
  );
}
