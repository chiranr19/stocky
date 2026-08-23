"use client";

import { useEffect, useState } from "react";
import { Radar, ScanLine, Waypoints } from "lucide-react";
import { getRiskMap, getSignals } from "@/lib/api";
import { useBudget } from "@/lib/budget";
import type { RiskMapResponse, SignalsResponse } from "@/lib/types";
import { SectionHeader } from "@/components/ui/primitives";
import { TeachBanner } from "@/components/learn/TeachBanner";
import { PageLesson } from "@/components/learn/PageLesson";
import { PAGE_LESSONS } from "@/lib/pageLessons";
import { WarmingNotice, Loading } from "@/components/ui/States";
import { RiskMap } from "@/components/explore/RiskMap";
import { Scanners } from "@/components/explore/Scanners";
import { Signals } from "@/components/explore/Signals";

export default function ExplorePage() {
  const { budget } = useBudget();
  const [riskmap, setRiskmap] = useState<RiskMapResponse | null>(null);
  const [signals, setSignals] = useState<SignalsResponse | null>(null);

  useEffect(() => {
    setRiskmap(null);
    setSignals(null);
    getRiskMap(budget).then(setRiskmap).catch(() => {});
    getSignals(budget).then(setSignals).catch(() => {});
  }, [budget]);

  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Explore</h1>
        <p className="text-sm text-muted">
          The veteran&apos;s toolkit — every tool captioned with when it lies to you.
        </p>
      </div>

      <PageLesson {...PAGE_LESSONS.explore} />

      <WarmingNotice />

      {/* Risk / reward */}
      <section>
        <SectionHeader icon={Radar} title="Risk vs reward" termKey="volatility" />
        <TeachBanner>
          The single most important lesson in one picture:{" "}
          <span className="text-ink">more risk does not guarantee more reward</span>. Hunt
          for names up-and-left of VOO.
        </TeachBanner>
        {riskmap ? <RiskMap data={riskmap} /> : <Loading label="Plotting the universe…" />}
      </section>

      {/* Scanners */}
      <section>
        <SectionHeader icon={ScanLine} title="Scanners" sub="how vets find what's moving" />
        <TeachBanner>
          These are the lists a trader checks every morning to spot where money and
          attention are flowing today.
        </TeachBanner>
        <Scanners />
      </section>

      {/* Signals */}
      <section>
        <SectionHeader icon={Waypoints} title="Trend signals" termKey="moving_average" />
        <TeachBanner>
          Widely-watched technical signals — useful precisely <i>because</i> so many people
          watch them, and dangerous for the same reason.
        </TeachBanner>
        {signals ? <Signals data={signals} /> : <Loading label="Scanning for signals…" />}
      </section>
    </div>
  );
}
