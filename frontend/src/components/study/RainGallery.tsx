// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useCallback, useMemo, useRef, useState } from "react";
import { CloudRain } from "lucide-react";
import type { BasketMember } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { fmtLens, useLens } from "@/lib/lens";
import { useReducedMotion } from "@/lib/motion";
import { STUDY } from "@/lib/studyCopy";
import { GROUP } from "@/components/learn/shared";

const CLIP = 8; // ±% the strip spans; bigger moves pin at the edge
const STEP = 5; // px between beeswarm levels
const MIN_GAP = 3.2; // %-of-width two dots must clear to share a level

interface Dot {
  dayIdx: number;
  ret: number;
  xPct: number;
  yOff: number;
}

/** Deterministic beeswarm: place dots left→right, stacking onto the lowest level
 *  that's clear, so overlapping days fan out instead of hiding each other. */
function layout(rain: (number | null)[]): Dot[] {
  const raw = rain
    .map((ret, dayIdx) => ({ ret, dayIdx }))
    .filter((d): d is { ret: number; dayIdx: number } => d.ret != null)
    .map((d) => ({
      ...d,
      xPct: ((Math.max(-CLIP, Math.min(CLIP, d.ret)) + CLIP) / (2 * CLIP)) * 100,
    }))
    .sort((a, b) => a.xPct - b.xPct);

  const lastX: number[] = [];
  return raw.map((d) => {
    let level = 0;
    while (level < lastX.length && d.xPct - lastX[level] < MIN_GAP) level++;
    lastX[level] = d.xPct;
    const rung = Math.ceil(level / 2);
    const yOff = level === 0 ? 0 : (level % 2 === 1 ? 1 : -1) * rung * STEP;
    return { ...d, yOff };
  });
}

/** Middle value of the absolute daily moves — a robust "typical day" size. */
function typicalMove(rain: (number | null)[]): number {
  const abs = rain.filter((v): v is number => v != null).map((v) => Math.abs(v)).sort((a, b) => a - b);
  if (!abs.length) return 0;
  return abs[Math.floor(abs.length / 2)];
}

export function RainGallery({
  members,
  rainDates,
}: {
  members: BasketMember[];
  rainDates: string[];
}) {
  const { lens } = useLens();
  const reduced = useReducedMotion();
  const maxDays = rainDates?.length || 60;

  const [reveal, setReveal] = useState(maxDays);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const replay = useCallback(() => {
    if (timer.current) clearInterval(timer.current);
    if (reduced) {
      setReveal(maxDays);
      return;
    }
    setReveal(0);
    timer.current = setInterval(() => {
      setReveal((r) => {
        if (r >= maxDays) {
          if (timer.current) clearInterval(timer.current);
          return r;
        }
        return r + 1;
      });
    }, 48);
  }, [maxDays, reduced]);

  const strips = useMemo(() => {
    const withRain = members.filter((m) => m.rain && m.rain.length > 0 && m.rain.some((v) => v != null));
    const scored = withRain.map((m) => ({ m, dots: layout(m.rain), spread: typicalMove(m.rain) }));
    // VOO (the reference sky) pinned first, then calm → wild.
    scored.sort((a, b) => {
      const av = a.m.group === "benchmark" ? 0 : 1;
      const bv = b.m.group === "benchmark" ? 0 : 1;
      if (av !== bv) return av - bv;
      return a.spread - b.spread;
    });
    return scored;
  }, [members]);

  if (!strips.length) return null;

  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 text-[11px] text-faint">
          <span>calm ← </span>
          <span className="text-muted">−{CLIP}%</span>
          <span className="mx-1 h-3 w-px bg-hair" />
          <span className="text-muted">0</span>
          <span className="mx-1 h-3 w-px bg-hair" />
          <span className="text-muted">+{CLIP}%</span>
          <span> → wild</span>
        </div>
        <button
          type="button"
          onClick={replay}
          className="inline-flex items-center gap-1.5 rounded-lg border border-hair px-2.5 py-1 text-[11px] font-medium text-muted transition-colors hover:bg-elevated hover:text-ink"
        >
          <CloudRain className="h-3.5 w-3.5" />
          Replay the {maxDays} days
        </button>
      </div>

      <div className="space-y-1.5">
        {strips.map(({ m, dots, spread }) => (
          <RainStrip
            key={m.ticker}
            ticker={m.ticker}
            group={m.group}
            dots={dots}
            spread={spread}
            reveal={reveal}
            rainDates={rainDates}
            lens={lens}
          />
        ))}
      </div>

      <p className="mt-3 border-t border-hair pt-2 text-[11px] leading-relaxed text-faint">
        <span className="font-medium text-muted">Where this lies to you:</span> {STUDY.rain.lie}
      </p>
    </div>
  );
}

function RainStrip({
  ticker,
  group,
  dots,
  spread,
  reveal,
  rainDates,
  lens,
}: {
  ticker: string;
  group: BasketMember["group"];
  dots: Dot[];
  spread: number;
  reveal: number;
  rainDates: string[];
  lens: ReturnType<typeof useLens>["lens"];
}) {
  const [sel, setSel] = useState<Dot | null>(null);
  const color = GROUP[group].hex;
  const yesterday = dots.reduce<Dot | null>((a, d) => (!a || d.dayIdx > a.dayIdx ? d : a), null);
  const summary = `${ticker}: a typical day moves about ${spread.toFixed(1)}%`;

  return (
    <div className="flex items-center gap-2">
      <div className="w-12 shrink-0 text-right text-[11px] font-medium text-muted">{ticker}</div>
      <div
        className="relative h-9 flex-1 rounded-md bg-elevated/40"
        role="img"
        aria-label={summary}
      >
        {/* zero line */}
        <div className="absolute left-1/2 top-1 bottom-1 w-px bg-hair" />
        {dots.map((d) => {
          if (d.dayIdx >= reveal) return null;
          const isYesterday = yesterday != null && d.dayIdx === yesterday.dayIdx;
          return (
            <button
              key={d.dayIdx}
              type="button"
              onMouseEnter={() => setSel(d)}
              onMouseLeave={() => setSel((s) => (s === d ? null : s))}
              onClick={() => setSel((s) => (s === d ? null : d))}
              className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full transition-transform hover:scale-150 motion-safe:animate-pop-in"
              style={{
                left: `${d.xPct}%`,
                top: `calc(50% + ${d.yOff}px)`,
                height: isYesterday ? 8 : 6,
                width: isYesterday ? 8 : 6,
                background: isYesterday ? "#7C6BFF" : color,
                opacity: isYesterday ? 1 : 0.7,
                boxShadow: isYesterday ? "0 0 0 2px rgba(124,107,255,0.35)" : undefined,
              }}
              aria-label={`${fmtDate(rainDates[d.dayIdx] ?? "")}: ${d.ret >= 0 ? "+" : ""}${d.ret}%`}
            />
          );
        })}
      </div>
      <div className="w-24 shrink-0 text-[10px] leading-tight text-faint">
        {sel ? (
          <span>
            <span className="text-muted">{fmtDate(rainDates[sel.dayIdx] ?? "")}</span>
            <br />
            <span className={sel.ret >= 0 ? "text-up" : "text-down"}>
              {sel.ret >= 0 ? "+" : ""}
              {sel.ret}% · {fmtLens(sel.ret, lens)}
            </span>
          </span>
        ) : (
          <span>typical ±{spread.toFixed(1)}%</span>
        )}
      </div>
    </div>
  );
}
