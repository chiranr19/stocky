// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import { getWatchouts } from "@/lib/api";
import { useBudget } from "@/lib/budget";
import type { WatchoutsResponse } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { SectionHeader } from "@/components/ui/primitives";
import { TeachBanner } from "@/components/learn/TeachBanner";
import { PageLesson } from "@/components/learn/PageLesson";
import { PAGE_LESSONS } from "@/lib/pageLessons";
import { Term } from "@/components/ui/Term";
import { Loading, WarmingNotice } from "@/components/ui/States";
import { WatchoutRowItem } from "@/components/watchouts/WatchoutList";

export default function WatchoutsPage() {
  const { budget } = useBudget();
  const [data, setData] = useState<WatchoutsResponse | null>(null);

  useEffect(() => {
    setData(null);
    getWatchouts(budget, 40).then(setData).catch(() => {});
  }, [budget]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Watch-outs</h1>
        <p className="text-sm text-muted">
          What a <span className="text-down">poor setup</span> looks like, and why —
          the other half of learning to spot a good one
          {data ? ` · as of ${fmtDate(data.as_of)}` : ""}.
        </p>
      </div>

      <PageLesson {...PAGE_LESSONS.watchouts} />

      <WarmingNotice />

      <TeachBanner>
        Studying bad setups is how the patterns become obvious. Each stock below carries
        named hazards — <Term k="falling_knife">falling knives</Term>, value traps, and
        names that paid you in volatility instead of returns. This is a{" "}
        <b>teaching list, not a sell list</b>: plenty of these will recover, and a few
        will be the year&apos;s best performers. Hover any chip for what it means and how
        veterans treat it.
      </TeachBanner>

      <section>
        <SectionHeader
          icon={ShieldAlert}
          title="Heaviest risk patterns"
          sub="ranked by number and severity of hazards"
        />
        <div className="card p-1.5">
          {!data ? (
            <Loading label="Scanning for risk patterns…" />
          ) : data.rows.length === 0 ? (
            <div className="px-3 py-10 text-center text-sm text-faint">
              No stocks at this budget are carrying the standard risk patterns right now.
            </div>
          ) : (
            data.rows.map((r, i) => (
              <WatchoutRowItem key={r.row.ticker} r={r} rank={i + 1} />
            ))
          )}
        </div>
      </section>

      <div className="card p-4 text-xs leading-relaxed text-muted">
        <h3 className="mb-1.5 text-sm font-semibold text-ink">How to use this page</h3>
        <p>
          Open a few of these and compare them against the{" "}
          <a href="/radar" className="text-accent hover:underline">
            Entry Radar
          </a>{" "}
          list. The same stock price falling 20% can be either a setup or a trap, and the
          difference is visible: is the long trend intact, is the volatility being paid
          for, is anyone still trading it? Learning to see that difference on your own is
          the entire point of this app.
        </p>
        <p className="mt-2 font-medium text-ink">
          Nothing here is advice. A high risk score describes hazards present today, not
          a prediction about tomorrow.
        </p>
      </div>
    </div>
  );
}
