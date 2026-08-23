"use client";

import { useEffect, useState } from "react";
import { GraduationCap } from "lucide-react";
import { getLearnBasket } from "@/lib/api";
import type { BasketResponse } from "@/lib/types";
import { ErrorCard, Loading, WarmingNotice } from "@/components/ui/States";
import { ActShell } from "@/components/learn/ActShell";
import { LearnProgress, type Act } from "@/components/learn/LearnProgress";
import { BasketMap } from "@/components/learn/BasketMap";
import { UmbrellaGrid } from "@/components/learn/UmbrellaGrid";
import { DrawdownRide } from "@/components/learn/DrawdownRide";
import { EchoExplainer } from "@/components/learn/EchoExplainer";
import { BoringWinner } from "@/components/learn/BoringWinner";
import { ReadOneQuiz } from "@/components/learn/ReadOneQuiz";
import { RoleLegend } from "@/components/learn/RoleLegend";

const ACTS: Act[] = [
  { id: "act-map", label: "The map" },
  { id: "act-umbrellas", label: "Four umbrellas" },
  { id: "act-ride", label: "The ride" },
  { id: "act-echoes", label: "The last N times" },
  { id: "act-winner", label: "The boring winner" },
  { id: "act-quiz", label: "Now you read one" },
];

export default function LearnPage() {
  const [basket, setBasket] = useState<BasketResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getLearnBasket().then(setBasket).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 text-accent">
          <GraduationCap className="h-5 w-5" />
          <span className="text-[11px] font-semibold uppercase tracking-[0.15em]">Learn</span>
        </div>
        <h1 className="mt-1 text-2xl font-semibold tracking-tight">
          Your watchlist, told as six short lessons
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-muted">
          Not more numbers — a way to read the ones you already have. Each act opens with a
          plain-life picture, shows it live on your own watchlist, then names exactly where the
          picture lies to you.
        </p>
      </div>

      <WarmingNotice />

      {error ? (
        <ErrorCard message={error} onRetry={() => location.reload()} />
      ) : !basket ? (
        <Loading label="Gathering the cast…" />
      ) : (
        <>
          <LearnProgress acts={ACTS} />

          <ActShell
            id="act-map"
            index={1}
            eyebrow="Risk vs reward"
            title="The map: nobody sits in the dream corner"
            metaphor="Up means it paid; right means a wilder ride. The dream is the top-left — high return, calm road — and it is almost always empty. That emptiness is the first lesson."
            lie="One year is a short window. A dot in the calm-and-paid corner today can slide into the wild-and-unpaid corner next year — position is a snapshot, not a verdict."
          >
            <BasketMap members={basket.members} />
          </ActShell>

          <ActShell
            id="act-umbrellas"
            index={2}
            eyebrow="Correlation"
            title="Four umbrellas from the same shop"
            metaphor="Four utilities that look like four different bets. In a real storm they all leak in the same seam — buying all four isn't diversifying, it's buying one bet four times."
            lie="Correlations aren't fixed. Two names that drift apart in calm markets can snap together in a crash — the moment diversification matters most is exactly when it stops working."
          >
            <UmbrellaGrid
              members={basket.members}
              correlation={basket.correlation}
              note={basket.correlation_note}
              benchmark={basket.benchmark_ticker}
            />
          </ActShell>

          <ActShell
            id="act-ride"
            index={3}
            eyebrow="Drawdown"
            title="The ride: could your hands stay on the wheel?"
            metaphor="Every big return is paid for by a stomach-churning valley along the way. This is the deepest one from the past year — the question isn't the destination, it's whether you'd have bailed out in the dip."
            lie="Last year's worst drop is a floor, not a ceiling. A calm year doesn't cap what the next one can do — the valley ahead can always be deeper than the one behind."
          >
            <DrawdownRide members={basket.members} />
          </ActShell>

          <ActShell
            id="act-echoes"
            index={4}
            eyebrow="Base rates"
            title="The last N times this happened"
            metaphor="Before trusting a hunch, check how the last dozen blind dates actually went. Counted history beats a gut feeling — as long as you never hide the sample size or the worst case."
            lie="A small sample lies constantly, and markets change regime. Nine dips in a raging bull all look like genius. The count and the worst case are the honesty check, never the promise."
          >
            <EchoExplainer members={basket.members} />
          </ActShell>

          <ActShell
            id="act-winner"
            index={5}
            eyebrow="The benchmark"
            title="The boring winner in the race"
            metaphor="Race any exciting pick against the most boring thing in the room — owning the whole market. The tortoise wins more of these than anyone expects, and with a far calmer ride."
            lie="A single year can flatter either runner. The point isn't that boring always wins — it's that a pick only earns its extra risk by clearing this bar over the long haul."
          >
            <BoringWinner members={basket.members} />
          </ActShell>

          <ActShell
            id="act-quiz"
            index={6}
            eyebrow="Practice"
            title="Now you read one"
            metaphor="You've watched the moves — here's a real chart with the name hidden. Is this a sale you'd shop, or a verdict you'd respect? Trust the shape."
            lie="Even a perfect read is a probability, not a promise. Getting the label right is the skill; the market still gets the final say on every single chart."
          >
            <ReadOneQuiz members={basket.members} />
          </ActShell>

          <section className="border-t border-hair pt-8">
            <h2 className="mb-1 text-xl font-semibold tracking-tight">The whole cast</h2>
            <p className="mb-4 text-sm text-muted">
              Every name on your watchlist and the role it plays. Stories written{" "}
              {basket.roles_as_of}; the live numbers live on each stock&apos;s page.
            </p>
            <RoleLegend members={basket.members} laws={basket.laws} />
          </section>

          <p className="border-t border-hair pt-4 text-xs text-faint">
            Educational tool for building market intuition — not financial advice. Every story
            here explains what the data shows and where it can fool you, never what to buy.
          </p>
        </>
      )}
    </div>
  );
}
