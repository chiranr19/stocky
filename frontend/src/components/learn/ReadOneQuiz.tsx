// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { ArrowRight, Check, X } from "lucide-react";
import type { BasketMember } from "@/lib/types";
import { Sparkline } from "@/components/ui/Sparkline";
import { GROUP } from "./shared";

const KEY = "stocky.learn.quiz";

export function ReadOneQuiz({ members }: { members: BasketMember[] }) {
  // Only names with a year of shape AND a known trend state can be graded.
  const pool = useMemo(
    () =>
      members
        .filter((m) => m.measurable && m.above_ma200 != null && m.series_1y.length > 8)
        .sort((a, b) => a.ticker.localeCompare(b.ticker)),
    [members],
  );

  // Deterministic daily rotation so the order is stable within a day.
  const start = pool.length ? new Date().getDate() % pool.length : 0;
  const order = useMemo(
    () => pool.map((_, i) => pool[(start + i) % pool.length]),
    [pool, start],
  );

  const [idx, setIdx] = useState(0);
  const [picked, setPicked] = useState<"sale" | "verdict" | null>(null);
  const [score, setScore] = useState({ correct: 0, total: 0 });

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY);
      if (raw) setScore(JSON.parse(raw));
    } catch {
      /* ignore */
    }
  }, []);

  if (!order.length) return null;
  const q = order[idx % order.length];
  const answer: "sale" | "verdict" = q.above_ma200 ? "sale" : "verdict";
  const revealed = picked != null;
  const correct = picked === answer;

  function choose(choice: "sale" | "verdict") {
    if (revealed) return;
    setPicked(choice);
    const next = { correct: score.correct + (choice === answer ? 1 : 0), total: score.total + 1 };
    setScore(next);
    try {
      localStorage.setItem(KEY, JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }

  function nextQuestion() {
    setPicked(null);
    setIdx((i) => (i + 1) % order.length);
  }

  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted">
          Here&apos;s one year of a real watchlist name, ticker hidden. Sale or verdict?
        </p>
        {score.total > 0 && (
          <span className="tnum text-xs text-faint">
            {score.correct}/{score.total} right
          </span>
        )}
      </div>

      <div className="mb-4 rounded-lg border border-hair bg-elevated/40 p-4">
        <Sparkline data={q.series_1y} width={520} height={90} className="w-full" />
      </div>

      {!revealed ? (
        <div className="grid gap-2 sm:grid-cols-2">
          <button
            onClick={() => choose("sale")}
            className="rounded-lg border border-hair bg-panel px-3 py-2.5 text-sm font-medium text-ink transition-colors hover:border-up/50 hover:bg-up/5"
          >
            A sale — a dip inside a rising trend
          </button>
          <button
            onClick={() => choose("verdict")}
            className="rounded-lg border border-hair bg-panel px-3 py-2.5 text-sm font-medium text-ink transition-colors hover:border-down/50 hover:bg-down/5"
          >
            A verdict — the long trend is broken
          </button>
        </div>
      ) : (
        <div className={`rounded-lg border p-3 ${correct ? "border-up/30 bg-up/5" : "border-down/30 bg-down/5"}`}>
          <div className="mb-1.5 flex items-center gap-2">
            {correct ? (
              <Check className="h-4 w-4 text-up" />
            ) : (
              <X className="h-4 w-4 text-down" />
            )}
            <span className={`text-sm font-semibold ${correct ? "text-up" : "text-down"}`}>
              {correct ? "You read it right" : "Not this time"}
            </span>
            <Link href={`/stock/${q.ticker}`} className="text-sm font-semibold text-ink hover:text-accent">
              {q.ticker}
            </Link>
            <span
              className={`rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${GROUP[q.group].chip}`}
            >
              {q.role}
            </span>
          </div>
          <p className="text-xs leading-relaxed text-muted">
            It was trading{" "}
            <span className={q.above_ma200 ? "text-up" : "text-down"}>
              {q.above_ma200 ? "above" : "below"} its 200-day average
            </span>{" "}
            — so the honest label is{" "}
            <span className="font-medium text-ink">
              {answer === "sale" ? "a sale (a dip inside an uptrend)" : "a verdict (a broken trend)"}
            </span>
            . The 200-day line is where a sale becomes a verdict.
          </p>
          <button
            onClick={nextQuestion}
            className="mt-2.5 inline-flex items-center gap-1 text-xs font-medium text-accent hover:underline"
          >
            Next chart <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      <p className="mt-3 text-[11px] text-faint">
        The chart doesn&apos;t know whether you got it right — this is practice at reading
        shape, not a score that matters.
      </p>
    </div>
  );
}
