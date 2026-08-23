"use client";

import Link from "next/link";
import { ExternalLink } from "lucide-react";
import type { DisclosedTrade, FilerBaseRate, FilerNotice } from "@/lib/types";
import { fmtCompact, fmtCurrency, fmtDate, fmtPct } from "@/lib/format";
import { Term } from "@/components/ui/Term";
import { InfoPop } from "@/components/ui/InfoPop";

/** Buy / Sell / Grant / Other as a colored chip. */
export function ActionBadge({ action }: { action: DisclosedTrade["action"] }) {
  const map: Record<string, string> = {
    buy: "border-up/40 bg-up/10 text-up",
    sell: "border-down/40 bg-down/10 text-down",
    grant: "border-hair bg-elevated text-muted",
    other: "border-hair bg-elevated text-faint",
  };
  const label = { buy: "Bought", sell: "Sold", grant: "Granted", other: "Other" }[action];
  return (
    <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[11px] font-semibold ${map[action]}`}>
      {label}
    </span>
  );
}

/** The disclosure lag, framed as the thing it costs you. */
export function LagBadge({ days }: { days: number }) {
  const tone = days <= 4 ? "text-muted" : days <= 20 ? "text-amber-400" : "text-down";
  return (
    <InfoPop
      content={
        `Public ${days} day${days === 1 ? "" : "s"} after the trade. That gap is the ` +
        `disclosure lag — the price has already moved by the time anyone outside can act on it.`
      }
      align="right"
    >
      <span className={`tnum text-[10px] underline decoration-dotted underline-offset-2 ${tone}`}>
        public +{days}d
      </span>
    </InfoPop>
  );
}

/** Amount, honest about precision: shares×price for insiders, a range for Congress. */
function amountLabel(t: DisclosedTrade): string {
  if (t.value_lo !== t.value_hi) {
    return `${fmtCurrency(t.value_lo)}–${fmtCurrency(t.value_hi)}`;
  }
  if (t.shares && t.price) {
    return `${fmtCompact(t.shares)} sh · ~${fmtCurrency(t.value_lo)}`;
  }
  return t.value_lo ? `~${fmtCurrency(t.value_lo)}` : "—";
}

/** The three numbers that turn a name into a lesson: what a follower got, the
 *  lag tax that ate part of it, and what VOO did over the same window. */
function PerfCluster({ t, stacked = false }: { t: DisclosedTrade; stacked?: boolean }) {
  if (!t.priceable) {
    return <span className="text-[10px] text-faint">not priceable here</span>;
  }
  const since = t.since_filed_pct;
  const voo = t.voo_since_filed_pct;
  const tax = t.lag_tax_pct;
  const beatVoo = since != null && voo != null ? since - voo : null;
  return (
    <div className={`${stacked ? "flex flex-wrap items-center gap-x-2 gap-y-0.5" : "text-right"} text-[11px]`}>
      <span className="text-muted">
        since public{" "}
        <span className={`tnum font-semibold ${(since ?? 0) >= 0 ? "text-up" : "text-down"}`}>
          {since != null ? fmtPct(since) : "—"}
        </span>
      </span>
      {!stacked && <br />}
      <span className="text-faint">
        <Term k="lag_tax">lag tax</Term>{" "}
        <span className={`tnum ${(tax ?? 0) >= 0 ? "text-up/80" : "text-down/80"}`}>
          {tax != null ? fmtPct(tax) : "—"}
        </span>
        {" · VOO "}
        <span className="tnum">{voo != null ? fmtPct(voo) : "—"}</span>
        {beatVoo != null && (
          <span className={`tnum ${beatVoo >= 0 ? "text-up" : "text-down"}`}>
            {" "}({beatVoo >= 0 ? "beat" : "lag"} {fmtPct(Math.abs(beatVoo), false)})
          </span>
        )}
      </span>
    </div>
  );
}

/** One disclosed trade. Desktop = one row; below lg the perf cluster and lag
 *  relocate to a second stacked line (parity rule: relocate, never delete). */
export function TradeRow({ t }: { t: DisclosedTrade }) {
  return (
    <div className="border-b border-hair/40 px-2 py-2 last:border-0">
      <div className="flex items-center gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <ActionBadge action={t.action} />
            {t.scheduled && (
              <span className="shrink-0">
                <Term k="tenb5_1">
                  <span className="rounded border border-hair bg-elevated px-1 py-0.5 text-[9px] uppercase tracking-wide text-faint">
                    10b5-1
                  </span>
                </Term>
              </span>
            )}
            <span className="truncate text-sm text-ink">{t.filer}</span>
          </div>
          <div className="mt-0.5 truncate text-[11px] text-faint">{t.filer_role || "Insider"}</div>
        </div>

        <div className="w-24 shrink-0">
          <Link
            href={`/stock/${t.ticker}`}
            className="text-sm font-semibold text-accent hover:underline"
          >
            {t.ticker}
          </Link>
          <div className="truncate text-[10px] text-faint">{t.name}</div>
        </div>

        <div className="hidden w-40 shrink-0 text-[11px] text-muted sm:block">
          <div className="tnum">
            {fmtDate(t.trade_date)} <span className="text-faint">→</span> {fmtDate(t.filed_date)}
          </div>
          <div className="mt-0.5"><LagBadge days={t.lag_days} /></div>
        </div>

        <div className="hidden w-36 shrink-0 text-right text-[11px] text-muted md:block">
          <Term k={t.value_lo !== t.value_hi ? "amount_range" : "form_4"}>
            <span className="tnum">{amountLabel(t)}</span>
          </Term>
        </div>

        <div className="hidden w-52 shrink-0 lg:block">
          <PerfCluster t={t} />
        </div>

        <a
          href={t.url}
          target="_blank"
          rel="noopener noreferrer"
          className="shrink-0 text-faint transition-colors hover:text-accent"
          title="View the original filing on SEC.gov"
        >
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </div>

      {/* Below lg: restore the perf cluster + amount + lag that the grid hid. */}
      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 pl-1 lg:hidden">
        <span className="tnum text-[11px] text-muted sm:hidden">
          {fmtDate(t.trade_date)} → {fmtDate(t.filed_date)}
        </span>
        <span className="sm:hidden"><LagBadge days={t.lag_days} /></span>
        <span className="tnum text-[11px] text-muted md:hidden">{amountLabel(t)}</span>
        <PerfCluster t={t} stacked />
      </div>
    </div>
  );
}

/** A named cross-filing pattern (cluster buying, scheduled sale, …). */
export function NoticeCard({ n }: { n: FilerNotice }) {
  const tone =
    n.tone === "constructive"
      ? "border-up/30 bg-up/5"
      : n.tone === "caution"
        ? "border-down/30 bg-down/5"
        : "border-accent/25 bg-accent/5";
  return (
    <div className={`rounded-xl border p-3.5 ${tone}`}>
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold text-ink">{n.headline}</span>
        {n.tickers.map((tk) => (
          <Link key={tk} href={`/stock/${tk}`} className="text-xs font-semibold text-accent hover:underline">
            {tk}
          </Link>
        ))}
      </div>
      <p className="mt-1 text-xs leading-relaxed text-muted">{n.detail}</p>
      <p className="mt-1.5 text-[11px] leading-relaxed text-faint">
        <span className="font-semibold uppercase tracking-wide">Caveat</span> · {n.caveat}
      </p>
    </div>
  );
}

/** Per-filer base rate — "has copying this person's disclosed buys ever paid?" */
export function BaseRateCard({ r }: { r: FilerBaseRate }) {
  const confTone =
    r.confidence === "high" ? "text-up" : r.confidence === "medium" ? "text-muted" : "text-down";
  const window = r.window_days >= 42 ? "~3 months" : "~1 month";
  const explain =
    `Every open-market BUY ${r.filer} has disclosed, measured from the day it became ` +
    `public (the only day you could act). Over the next ${window}: median ` +
    `${fmtPct(r.median_fwd_pct)}, worst ${fmtPct(r.worst_pct)}, best ${fmtPct(r.best_pct)}. ` +
    `${r.n} cases across ${r.n_years} year(s) — confidence ${r.confidence}. ` +
    `Typical disclosure lag ${r.median_lag_days} days.\n\n` +
    `A base rate over a small sample, not a forecast — a few famous names look ` +
    `brilliant by pure chance (survivorship bias).`;
  return (
    <InfoPop content={explain} align="left" className="block">
      <div className="cursor-help rounded-lg border border-hair bg-elevated/50 px-3 py-2 text-left">
        <div className="flex items-center justify-between gap-2">
          <span className="truncate text-xs font-semibold text-ink">{r.filer}</span>
          <span className={`text-[10px] font-semibold uppercase ${confTone}`}>{r.confidence}</span>
        </div>
        <div className="tnum mt-1 text-sm">
          <span className={r.median_fwd_pct >= 0 ? "text-up" : "text-down"}>
            {fmtPct(r.median_fwd_pct)}
          </span>{" "}
          <span className="text-[11px] text-faint">median · {window}</span>
        </div>
        <div className="tnum mt-0.5 text-[11px] text-faint">
          {Math.round(r.win_rate * r.n)}/{r.n} up · worst{" "}
          <span className="text-down">{fmtPct(r.worst_pct)}</span>
          {r.median_excess_pct != null && (
            <>
              {" · "}
              <span className={r.median_excess_pct >= 0 ? "text-up" : "text-down"}>
                {fmtPct(r.median_excess_pct)} vs VOO
              </span>
            </>
          )}
        </div>
      </div>
    </InfoPop>
  );
}
