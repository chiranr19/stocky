// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useEffect, useState } from "react";
import { Landmark, TrendingUp, ScrollText } from "lucide-react";
import { getFilers } from "@/lib/api";
import type { FilersResponse } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { SectionHeader } from "@/components/ui/primitives";
import { TeachBanner } from "@/components/learn/TeachBanner";
import { Term } from "@/components/ui/Term";
import { Loading, WarmingNotice } from "@/components/ui/States";
import { TradeRow, NoticeCard, BaseRateCard } from "@/components/filers/FilerParts";

type Kind = "all" | "insider" | "congress";
type Action = "all" | "buy" | "sell";

const KINDS: { key: Kind; label: string }[] = [
  { key: "all", label: "Everyone" },
  { key: "insider", label: "Company insiders" },
  { key: "congress", label: "Congress" },
];
const ACTIONS: { key: Action; label: string }[] = [
  { key: "all", label: "All activity" },
  { key: "buy", label: "Purchases" },
  { key: "sell", label: "Sales" },
];

function Toggle<T extends string>({
  options,
  value,
  onChange,
}: {
  options: { key: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div className="inline-flex flex-wrap gap-1 rounded-lg border border-hair bg-panel p-1">
      {options.map((o) => (
        <button
          key={o.key}
          onClick={() => onChange(o.key)}
          className={`rounded-md px-2.5 py-1 text-xs transition-colors ${
            value === o.key ? "bg-elevated text-ink" : "text-muted hover:text-ink"
          }`}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

export default function FilersPage() {
  const [kind, setKind] = useState<Kind>("all");
  const [action, setAction] = useState<Action>("all");
  const [data, setData] = useState<FilersResponse | null>(null);

  useEffect(() => {
    setData(null);
    getFilers(kind, action, 80).then(setData).catch(() => {});
  }, [kind, action]);

  const oneMonth = (data?.base_rates ?? []).filter((r) => r.window_days <= 21);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Followed Filers</h1>
        <p className="text-sm text-muted">
          What the powerful legally disclosed buying and selling — and the{" "}
          <Term k="lag_tax">lag tax</Term> on knowing
          {data?.filings_through ? ` · filings through ${fmtDate(data.filings_through)}` : ""}.
        </p>
      </div>

      <WarmingNotice />

      <TeachBanner>
        These are <b>legally-required public disclosures</b>, studied for learning — never
        advice or a signal to copy. Company insiders file a <Term k="form_4">Form 4</Term>{" "}
        within two days; members of Congress file under the{" "}
        <Term k="stock_act">STOCK Act</Term> with a 30–45 day{" "}
        <Term k="disclosure_lag">lag</Term>. Presidents disclose only once a year, so there
        is <b>no per-trade Trump data</b> — the closest public proxy is Form 4 activity by
        Trump Media (DJT) insiders, shown here.
      </TeachBanner>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <Toggle options={KINDS} value={kind} onChange={setKind} />
        <Toggle options={ACTIONS} value={action} onChange={setAction} />
      </div>

      {/* Notices */}
      {data && data.notices.length > 0 && (
        <section className="space-y-2">
          <SectionHeader icon={ScrollText} title="Worth noticing" sub="named patterns across the filings" />
          <div className="grid gap-2 sm:grid-cols-2">
            {data.notices.map((n, i) => (
              <NoticeCard key={i} n={n} />
            ))}
          </div>
        </section>
      )}

      {/* Base rates */}
      <section>
        <SectionHeader
          icon={TrendingUp}
          title="Has following their buys ever paid?"
          termKey="base_rate"
          sub="forward outcomes from the disclosure date, vs VOO"
        />
        {oneMonth.length > 0 ? (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {oneMonth
              .sort((a, b) => b.n - a.n)
              .map((r) => (
                <BaseRateCard key={r.filer} r={r} />
              ))}
          </div>
        ) : (
          <div className="card p-4 text-xs leading-relaxed text-muted">
            Not enough disclosed <b>open-market purchases</b> by any single filer yet to
            compute an honest base rate. That is itself the lesson: corporate insiders
            mostly receive shares as pay and <span className="text-down">sell</span> — they
            rarely buy with their own cash. The base rates fill in as Congress data (which
            is far more purchase-heavy) comes online, and any small sample here would be{" "}
            <Term k="survivorship_bias">mostly noise</Term> anyway.
          </div>
        )}
      </section>

      {/* The ledger */}
      <section>
        <SectionHeader icon={Landmark} title="Disclosed trades" sub="most recently filed first" />
        <div className="card p-1.5">
          {!data ? (
            <Loading label="Reading the filings…" />
          ) : data.trades.length === 0 ? (
            <div className="px-3 py-10 text-center text-sm text-faint">
              {kind === "congress"
                ? "Congressional STOCK Act filings arrive in a later phase — the insider feed is live now."
                : "No filings match this filter yet."}
            </div>
          ) : (
            data.trades.map((t) => <TradeRow key={`${t.filing_id}-${t.ticker}-${t.trade_date}-${t.action}`} t={t} />)
          )}
        </div>
      </section>

      {/* Method + honesty footer */}
      <div className="card p-4 text-xs leading-relaxed text-muted">
        <h3 className="mb-1.5 text-sm font-semibold text-ink">How to read this page</h3>
        <p>
          Every row links to the <b>original filing</b> on SEC.gov — the source of record,
          never a third-party aggregator. The three performance numbers all measure from the{" "}
          <b>day the trade became public</b>, because that is the earliest anyone outside
          could have acted. &quot;Lag tax&quot; is how much the price already moved in the
          gap between the trade and its disclosure — the built-in cost of copying anyone
          famous. VOO over the same window is the boring benchmark every move is judged
          against.
        </p>
        <p className="mt-2 font-medium text-ink">
          Nothing here is advice. Insiders sell for taxes and diversification far more than
          for a view, buys are rarer than they look, and a great-looking track record over a
          handful of trades is <Term k="survivorship_bias">mostly luck</Term>. This is a
          window for studying how disclosure works — not a list to follow.
        </p>
        {data && <p className="mt-2 text-faint">Source: {data.source_label}.</p>}
      </div>
    </div>
  );
}
