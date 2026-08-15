"use client";

import { AlertTriangle } from "lucide-react";
import type { RadarResponse, RadarRow } from "@/lib/types";
import { fmtPct } from "@/lib/format";
import { Term } from "@/components/ui/Term";
import { InfoPop } from "@/components/ui/InfoPop";
import { ScoreBadge } from "@/components/ui/primitives";
import { StockRowItem } from "@/components/stocks/StockRowItem";
import { FlagChips } from "@/components/flags/Flags";

/** Tiny horizontal bar showing pullback depth (capped at 30% for scale). */
function DepthBar({ depth }: { depth: number }) {
  const pct = Math.min(100, (depth / 30) * 100);
  return (
    <div className="w-16">
      <div className="tnum text-right text-xs font-semibold text-down">
        −{depth.toFixed(1)}%
      </div>
      <div className="mt-0.5 h-1 rounded-full bg-elevated">
        <div
          className="h-1 rounded-full bg-down/70"
          style={{ width: `${Math.max(6, pct)}%` }}
        />
      </div>
    </div>
  );
}

const NO_ECHO_NOTE =
  "Fewer than 6 comparable dips in this stock's ~5 years of history. " +
  "Today's pullback is genuinely unusual for it — which cuts both ways: " +
  "unusual is not the same as opportunity, it means history has less to say here.";

/** Shared derivation so the desktop chip and the phone line never disagree. */
function echoParts(e: NonNullable<RadarRow["echo"]>) {
  // "exact" = same depth bucket; "at_least" = widened superset, must be labeled.
  // Fields are optional-safe: an older cached payload must not break the page.
  const match =
    e.kind === "at_least" && e.min_depth_pct != null
      ? `dips ≥${e.min_depth_pct.toFixed(0)}%`
      : e.bucket_lo != null && e.bucket_hi != null
        ? `dips of ${e.bucket_lo.toFixed(0)}–${e.bucket_hi.toFixed(0)}%`
        : "similar dips";
  // Sample quality: 9 cases all from one bull year is weak evidence, and the
  // UI must say so rather than letting the number look authoritative.
  const conf = e.confidence ?? "low";
  const confNote =
    conf === "high"
      ? `Spread across ${e.n_years} different years — the strongest sample this stock offers.`
      : conf === "medium"
        ? `Covers ${e.n_years} years; decent, but not many market regimes.`
        : `Thin or clustered in ${e.n_years ?? 1} year(s) — treat as a hint, not evidence.`;
  const explain =
    `Past episodes where this stock was ${match} below its high, in the same trend ` +
    `state. Median next-month move ${fmtPct(e.median_fwd_pct)}, best ${fmtPct(e.best_pct)}, ` +
    `worst ${fmtPct(e.worst_pct)}. A base rate over ${e.n} cases — not a forecast.\n\n` +
    `Sample confidence: ${conf}. ${confNote}`;
  return { match, conf, explain, ups: Math.round(e.win_rate * e.n) };
}

/**
 * "What happened after similar dips" — base rates with N and worst case.
 *
 * Only rendered at `lg` and up, where hover exists, so the explanation stays a
 * `title`. It also carries nested `Term` buttons, which could not live inside
 * an InfoPop's button without producing invalid HTML. Touch devices get
 * {@link EchoLine} instead, which is tappable.
 */
export function EchoChip({ r, compact = false }: { r: RadarRow; compact?: boolean }) {
  if (!r.echo) {
    return (
      <span className="text-[10px] text-faint" title={NO_ECHO_NOTE}>
        <Term k="sample_size">rare setup — too few past cases</Term>
      </span>
    );
  }
  const e = r.echo;
  const { match, conf, explain, ups } = echoParts(e);
  const confTone =
    conf === "high" ? "text-up" : conf === "medium" ? "text-muted" : "text-down";

  return (
    <div className={`text-right ${compact ? "text-[10px]" : "text-xs"}`} title={explain}>
      <div className="text-muted">
        <span className="tnum text-ink">{e.n}</span> {match} →{" "}
        <span className={`tnum font-semibold ${e.median_fwd_pct >= 0 ? "text-up" : "text-down"}`}>
          {fmtPct(e.median_fwd_pct)}
        </span>{" "}
        <Term k="forward_return">next mo</Term>
      </div>
      <div className="text-[10px] text-faint">
        <span className="tnum">{ups}↑ {e.n - ups}↓</span> · worst{" "}
        <span className="tnum text-down">{fmtPct(e.worst_pct)}</span> ·{" "}
        <span className={confTone}>{conf} conf</span>
      </div>
    </div>
  );
}

/**
 * Single-line echo for the phone layout.
 *
 * The desktop grid hides depth and echo behind `md:`/`lg:` breakpoints — on a
 * phone that removed exactly the evidence this page exists to show, leaving a
 * bare score. This restores it in one wrapping line.
 */
function EchoLine({ r }: { r: RadarRow }) {
  if (!r.echo) {
    return (
      <InfoPop content={NO_ECHO_NOTE} align="left">
        <span className="text-[10px] text-faint underline decoration-dotted underline-offset-2">
          rare setup — too few past cases
        </span>
      </InfoPop>
    );
  }
  const e = r.echo;
  const { match, conf, explain } = echoParts(e);
  const confTone =
    conf === "high" ? "text-up" : conf === "medium" ? "text-muted" : "text-down";

  return (
    <InfoPop content={explain} align="left">
      <span className="text-[10px] leading-relaxed text-muted underline decoration-dotted underline-offset-2">
        <span className="tnum text-ink">{e.n}</span> {match} →{" "}
        <span className={`tnum font-semibold ${e.median_fwd_pct >= 0 ? "text-up" : "text-down"}`}>
          {fmtPct(e.median_fwd_pct)}
        </span>{" "}
        next mo · worst{" "}
        <span className="tnum text-down">{fmtPct(e.worst_pct)}</span> ·{" "}
        <span className={confTone}>{conf} conf</span>
      </span>
    </InfoPop>
  );
}

/** Plain-English explanation of an entry score, from its factor breakdown. */
export function explainEntry(r: RadarRow): string {
  const f = r.entry_factors;
  const parts = [
    `Deeper than ${(f.depth ?? 0).toFixed(0)}% of this stock's own dips`,
    r.falling_knife ? "trend BROKEN (below 200-day)" : "long trend intact",
    `RSI factor ${(f.rsi ?? 0).toFixed(0)}/100 (lower RSI scores higher)`,
    `1-year strength ranks ${(f.quality ?? 0).toFixed(0)}/100 vs other candidates`,
  ];
  return `Entry score ${r.entry_score.toFixed(0)}: ${parts.join(" · ")}. Ranked to study, not a recommendation.`;
}

export function KnifeChip() {
  return (
    <span className="inline-flex items-center gap-1 rounded-md border border-down/40 bg-down/10 px-1.5 py-0.5 text-[10px] font-medium text-down">
      <AlertTriangle className="h-3 w-3" />
      <Term k="falling_knife">knife</Term>
    </span>
  );
}

/** One radar row: the standard stock row + depth, entry score, echo, knife. */
export function RadarRowItem({ r, rank }: { r: RadarRow; rank?: number }) {
  // Any risk pattern beyond the knife flag gets surfaced here too — a strong
  // entry score must never quietly hide a hazard.
  const otherRisks = (r.flags ?? []).filter((f) => f.code !== "falling_knife");
  return (
    <div className="border-b border-hair/40 last:border-0">
      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <StockRowItem row={r.row} rank={rank} />
        </div>
        <div className="hidden shrink-0 md:block">
          <DepthBar depth={r.depth_pct} />
        </div>
        <div className="hidden w-44 shrink-0 lg:block">
          <EchoChip r={r} />
        </div>
        <div className="hidden max-w-[190px] shrink-0 justify-end xl:flex">
          <FlagChips flags={otherRisks} max={2} compact />
        </div>
        <div className="flex shrink-0 items-center gap-1.5 pr-2">
          {r.falling_knife && <KnifeChip />}
          <InfoPop content={explainEntry(r)}>
            <ScoreBadge score={r.entry_score} />
          </InfoPop>
        </div>
      </div>

      {/* Phone/tablet: the columns above are hidden below xl, so restore their
          content here rather than shipping a score with no evidence behind it. */}
      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1 px-2.5 pb-2 pl-9 xl:hidden">
        <span className="tnum shrink-0 text-[11px] font-semibold text-down md:hidden">
          −{r.depth_pct.toFixed(1)}% dip
        </span>
        <span className="lg:hidden">
          <EchoLine r={r} />
        </span>
        {otherRisks.length > 0 && <FlagChips flags={otherRisks} max={2} compact />}
      </div>
    </div>
  );
}

/** The formula, spelled out — nothing hidden, nothing promised. */
export function MethodCard({ data }: { data: RadarResponse }) {
  const w = data.weights;
  return (
    <div className="card p-4 text-xs leading-relaxed text-muted">
      <h3 className="mb-1.5 text-sm font-semibold text-ink">
        <Term k="entry_score">How this list is ranked</Term>
      </h3>
      <p>
        Every affordable, liquid stock trading ≥5% below its {data.lookback.toUpperCase()}{" "}
        high gets an entry score:{" "}
        <span className="text-ink">
          Depth {Math.round((w.depth ?? 0) * 100)}%
        </span>{" "}
        (how unusual this <Term k="pullback">pullback</Term> is vs the stock&apos;s own
        history) ·{" "}
        <span className="text-ink">Trend {Math.round((w.trend ?? 0) * 100)}%</span>{" "}
        (above its 200-day average, i.e. not a{" "}
        <Term k="falling_knife">falling knife</Term>) ·{" "}
        <span className="text-ink">RSI {Math.round((w.rsi ?? 0) * 100)}%</span> (how
        washed-out it is) ·{" "}
        <span className="text-ink">Quality {Math.round((w.quality ?? 0) * 100)}%</span>{" "}
        (1-year return rank — dips in strong stocks first).
      </p>
      <p className="mt-2">
        The &quot;similar dips&quot; column is a <Term k="base_rate">base rate</Term>:
        we find every past episode with the same depth bucket and trend state, then
        measure the actual <Term k="forward_return">forward return</Term> over the
        next {data.horizon_days} sessions — with the{" "}
        <Term k="sample_size">sample size</Term>, <Term k="win_rate">win rate</Term> and
        worst case always shown.
      </p>
      <p className="mt-2 font-medium text-ink">
        These are setups worth studying, ranked transparently — not buy signals, and
        never a prediction. Past behavior does not guarantee anything.
      </p>
    </div>
  );
}
