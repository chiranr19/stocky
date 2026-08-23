// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from "recharts";
import { Sparkles } from "lucide-react";
import { ApiError, getCone } from "@/lib/api";
import type { ConeResponse } from "@/lib/types";
import { useLens } from "@/lib/lens";
import { useReducedMotion } from "@/lib/motion";
import { InfoPop } from "@/components/ui/InfoPop";
import { RUN_FUTURES, RUNNING_FUTURES, STUDY } from "@/lib/studyCopy";

type Horizon = 21 | 63 | 126 | 252;
const HORIZONS: { h: Horizon; label: string }[] = [
  { h: 21, label: "1M" },
  { h: 63, label: "3M" },
  { h: 126, label: "6M" },
  { h: 252, label: "1Y" },
];

function horizonWords(h: number): string {
  if (h <= 21) return "a month";
  if (h <= 63) return "three months";
  if (h <= 126) return "six months";
  return "a year";
}

export function ConePanel({
  ticker,
  defaultHorizon = 126,
}: {
  ticker: string;
  defaultHorizon?: Horizon;
}) {
  const { lens } = useLens();
  const reduced = useReducedMotion();
  const [horizon, setHorizon] = useState<Horizon>(defaultHorizon);
  const [cone, setCone] = useState<ConeResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Theater state: how many sample paths are currently drawn.
  const [running, setRunning] = useState(false);
  const [revealed, setRevealed] = useState(0);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopTimer = useCallback(() => {
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }, []);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setErr(null);
    setRunning(false);
    setRevealed(0);
    stopTimer();
    getCone(ticker, horizon)
      .then((c) => {
        if (alive) {
          setCone(c);
          setLoading(false);
        }
      })
      .catch((e) => {
        if (alive) {
          setErr(e instanceof ApiError ? e.message : "Couldn't build the cone.");
          setCone(null);
          setLoading(false);
        }
      });
    return () => {
      alive = false;
      stopTimer();
    };
  }, [ticker, horizon, stopTimer]);

  const runFutures = useCallback(() => {
    if (!cone) return;
    const n = cone.sample_paths.length;
    setRunning(true);
    if (reduced) {
      setRevealed(n); // no animation — show them all at once
      return;
    }
    setRevealed(0);
    stopTimer();
    timer.current = setInterval(() => {
      setRevealed((r) => {
        if (r >= n) {
          stopTimer();
          return r;
        }
        return r + 1;
      });
    }, 140);
  }, [cone, reduced, stopTimer]);

  return (
    <div className="card p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-ink">{ticker}</span>
          <InfoPop content={STUDY.cone.method} align="left">
            <span className="text-[11px] text-faint underline decoration-dotted underline-offset-2">
              how it&apos;s drawn
            </span>
          </InfoPop>
        </div>
        <div className="flex overflow-hidden rounded-lg border border-hair">
          {HORIZONS.map(({ h, label }) => (
            <button
              key={h}
              type="button"
              onClick={() => setHorizon(h)}
              className={`px-2.5 py-1 text-[11px] font-medium transition-colors ${
                h === horizon
                  ? "bg-accent/15 text-accent"
                  : "text-muted hover:bg-elevated hover:text-ink"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center text-xs text-faint">
          Simulating futures…
        </div>
      ) : err ? (
        <div className="rounded-lg border border-amber-400/25 bg-amber-400/5 px-3 py-3 text-xs leading-relaxed text-muted">
          {err}
        </div>
      ) : cone ? (
        <ConeChart cone={cone} lens={lens} revealed={revealed} reduced={reduced} />
      ) : null}

      {cone && !err && (
        <>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={runFutures}
              className="inline-flex items-center gap-1.5 rounded-lg border border-accent/30 bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent transition-colors hover:bg-accent/15"
            >
              <Sparkles className="h-3.5 w-3.5" />
              {running && revealed < cone.sample_paths.length ? RUNNING_FUTURES : RUN_FUTURES}
            </button>
            {running && (
              <span className="text-xs text-muted">
                <b className="tnum text-ink">{cone.samples_up}</b> of{" "}
                <b className="tnum text-ink">{cone.samples_up + cone.samples_down}</b> sample
                futures ended above where {cone.name.split(" ")[0]} sits today — the cone in
                miniature.
              </span>
            )}
          </div>
          <ConeSummary cone={cone} lens={lens} />
          <p className="mt-2 border-t border-hair pt-2 text-[11px] leading-relaxed text-faint">
            <span className="font-medium text-muted">Where this lies to you:</span>{" "}
            {STUDY.cone.lie.replace("{ticker}", cone.name.split(" ")[0])}
          </p>
        </>
      )}
    </div>
  );
}

function ConeChart({
  cone,
  lens,
  revealed,
  reduced,
}: {
  cone: ConeResponse;
  lens: ReturnType<typeof useLens>["lens"];
  revealed: number;
  reduced: boolean;
}) {
  const dollar = lens !== "pct";
  const basis = dollar ? (lens as number) : cone.start_price;
  const toVal = (m: number) =>
    dollar ? Math.round(basis * m) : +(((m - 1) * 100).toFixed(1));
  const yFmt = (v: number) =>
    dollar ? `$${Math.round(v).toLocaleString()}` : `${v >= 0 ? "+" : ""}${v}%`;

  const vooBands = cone.benchmark?.bands;
  const data = cone.bands.map((b, i) => {
    const row: Record<string, number | number[]> = {
      session: b.session,
      b90: [toVal(b.p10), toVal(b.p90)],
      b50: [toVal(b.p25), toVal(b.p75)],
      mid: toVal(b.p50),
    };
    if (vooBands && vooBands[i]) {
      row.vlo = toVal(vooBands[i].p25);
      row.vhi = toVal(vooBands[i].p75);
    }
    cone.sample_paths.forEach((p, k) => {
      if (k < revealed) row[`s${k}`] = toVal(p[i]);
    });
    return row;
  });

  const startVal = dollar ? basis : 0;

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 6, right: 10, bottom: 4, left: 4 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis
          dataKey="session"
          type="number"
          domain={[0, cone.horizon_sessions]}
          ticks={[0, Math.round(cone.horizon_sessions / 2), cone.horizon_sessions]}
          tickFormatter={(s: number) => (s === 0 ? "today" : `${Math.round(s / 21)}mo`)}
          tick={{ fill: "#5A616B", fontSize: 11 }}
          stroke="rgba(255,255,255,0.08)"
        />
        <YAxis
          tickFormatter={yFmt}
          tick={{ fill: "#5A616B", fontSize: 11 }}
          stroke="rgba(255,255,255,0.08)"
          width={54}
          domain={["auto", "auto"]}
        />
        <ReferenceLine y={startVal} stroke="#5A616B" strokeDasharray="4 4" strokeOpacity={0.6} />

        {/* Widest band (10th–90th) faint, then the middle half deeper. */}
        <Area
          dataKey="b90"
          stroke="none"
          fill="#7C6BFF"
          fillOpacity={0.1}
          isAnimationActive={!reduced}
          animationDuration={500}
        />
        <Area
          dataKey="b50"
          stroke="none"
          fill="#7C6BFF"
          fillOpacity={0.22}
          isAnimationActive={!reduced}
          animationDuration={500}
        />

        {/* Sample futures — the theatrical replay. */}
        {cone.sample_paths.map((_, k) =>
          k < revealed ? (
            <Line
              key={`s${k}`}
              dataKey={`s${k}`}
              stroke="#B7ADFF"
              strokeWidth={1}
              strokeOpacity={0.32}
              dot={false}
              isAnimationActive={!reduced}
              animationDuration={480}
              connectNulls
            />
          ) : null,
        )}

        {/* VOO's middle half, ghosted, for the honest comparison. */}
        {vooBands && (
          <>
            <Line
              dataKey="vlo"
              stroke="#9AA3AD"
              strokeWidth={1}
              strokeDasharray="3 3"
              strokeOpacity={0.55}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              dataKey="vhi"
              stroke="#9AA3AD"
              strokeWidth={1}
              strokeDasharray="3 3"
              strokeOpacity={0.55}
              dot={false}
              isAnimationActive={false}
            />
          </>
        )}

        {/* The middle path. */}
        <Line
          dataKey="mid"
          stroke="#7C6BFF"
          strokeWidth={2}
          dot={false}
          isAnimationActive={!reduced}
          animationDuration={500}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function ConeSummary({
  cone,
  lens,
}: {
  cone: ConeResponse;
  lens: ReturnType<typeof useLens>["lens"];
}) {
  const dollar = lens !== "pct";
  const basis = dollar ? (lens as number) : cone.start_price;
  const toVal = (m: number) =>
    dollar ? `$${Math.round(basis * m).toLocaleString()}` : `${(m - 1) * 100 >= 0 ? "+" : ""}${(((m - 1) * 100)).toFixed(1)}%`;

  const e = cone.end;
  const short = cone.name.split(" ")[0];
  const stake = dollar ? `a $${(lens as number).toLocaleString()} position` : short;
  const words = horizonWords(cone.horizon_sessions);

  return (
    <div className="mt-2 space-y-1.5 text-xs leading-relaxed text-muted">
      <p>
        Over {words}, the middle half of simulated futures for {stake} lands between{" "}
        <b className="tnum text-ink">{toVal(e.p25)}</b> and{" "}
        <b className="tnum text-ink">{toVal(e.p75)}</b>. About 1 in 10 ended below{" "}
        <b className="tnum text-down">{toVal(e.p10)}</b>, 1 in 10 above{" "}
        <b className="tnum text-up">{toVal(e.p90)}</b>.
      </p>
      {cone.benchmark && (
        <p className="text-faint">
          VOO&apos;s middle half spans{" "}
          <span className="tnum">{toVal(cone.benchmark.end.p25)}</span>–
          <span className="tnum">{toVal(cone.benchmark.end.p75)}</span>; {short}&apos;s spans{" "}
          <span className="tnum">{toVal(e.p25)}</span>–<span className="tnum">{toVal(e.p75)}</span>.
          A wider cone is a wilder ride, not better odds.
        </p>
      )}
    </div>
  );
}
