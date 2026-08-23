"use client";

import { Suspense, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Term } from "@/components/ui/Term";
import { TeachBanner } from "@/components/learn/TeachBanner";
import { PageLesson } from "@/components/learn/PageLesson";
import { PAGE_LESSONS } from "@/lib/pageLessons";
import { TimeMachine } from "@/components/timemachine/TimeMachine";

function TimeMachineInner() {
  const params = useSearchParams();
  const [ticker, setTicker] = useState((params.get("ticker") || "NVDA").toUpperCase());
  return <TimeMachine ticker={ticker} onTickerChange={setTicker} />;
}

export default function TimeMachinePage() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Time Machine</h1>
        <p className="text-sm text-muted">
          What would a past investment be worth today — and could you have stomached the
          ride?
        </p>
      </div>
      <PageLesson {...PAGE_LESSONS.timeMachine} />
      <TeachBanner>
        The number that matters isn&apos;t the return — it&apos;s the{" "}
        <Term k="drawdown">max drawdown</Term>. Great long-run gains are worthless if the
        dip would&apos;ve shaken you out first. Always measured against{" "}
        <Term k="voo">VOO</Term>.
      </TeachBanner>
      <Suspense fallback={<div className="h-40 animate-pulse rounded-xl border border-hair bg-panel" />}>
        <TimeMachineInner />
      </Suspense>
    </div>
  );
}
