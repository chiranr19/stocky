"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowDown, ArrowUp, ChevronsUpDown, X } from "lucide-react";
import type { BasketMember } from "@/lib/types";
import { fmtCurrency } from "@/lib/format";
import { fmtLens, lensBasis, useLens } from "@/lib/lens";
import { GROUP } from "@/components/learn/shared";

type Key =
  | "name" | "price" | "change_pct" | "ret_1y" | "since_added_pct"
  | "vol_90d" | "above_ma200" | "max_drawdown_1y" | "attention";

interface Col {
  key: Key;
  label: string;
  numeric: boolean;
  essential?: boolean; // shown at every width (others collapse to a second line)
  sortValue: (m: BasketMember) => number | string | null;
}

const prettyFlag = (code: string) =>
  code.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());

export function WatchTable({
  members,
  onRemove,
}: {
  members: BasketMember[];
  onRemove: (ticker: string) => void;
}) {
  const { lens } = useLens();
  const [sort, setSort] = useState<{ key: Key; dir: "asc" | "desc" }>({
    key: "attention",
    dir: "desc",
  });

  const cols: Col[] = [
    { key: "name", label: "Name", numeric: false, essential: true, sortValue: (m) => m.ticker },
    { key: "price", label: "Price", numeric: true, essential: true, sortValue: (m) => m.price },
    { key: "change_pct", label: "Day", numeric: true, essential: true, sortValue: (m) => m.change_pct },
    { key: "ret_1y", label: `1y ${lensBasis(lens)}`.trim(), numeric: true, sortValue: (m) => m.ret_1y },
    { key: "since_added_pct", label: `Since added ${lensBasis(lens)}`.trim(), numeric: true, sortValue: (m) => m.since_added_pct },
    { key: "vol_90d", label: "Volatility", numeric: true, sortValue: (m) => m.vol_90d },
    { key: "above_ma200", label: "Trend", numeric: false, sortValue: (m) => (m.above_ma200 == null ? null : m.above_ma200 ? 1 : 0) },
    { key: "max_drawdown_1y", label: `Worst drop ${lensBasis(lens)}`.trim(), numeric: true, sortValue: (m) => m.max_drawdown_1y },
    { key: "attention", label: "Attention", numeric: true, essential: true, sortValue: (m) => m.attention },
  ];

  const sorted = useMemo(() => {
    const col = cols.find((c) => c.key === sort.key)!;
    const dir = sort.dir === "asc" ? 1 : -1;
    return [...members].sort((a, b) => {
      const av = col.sortValue(a);
      const bv = col.sortValue(b);
      if (av == null && bv == null) return 0;
      if (av == null) return 1; // nulls always sink
      if (bv == null) return -1;
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
      return (Math.abs(b.change_pct ?? 0) - Math.abs(a.change_pct ?? 0)); // tie-break
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [members, sort, lens]);

  const toggle = (key: Key) =>
    setSort((s) => (s.key === key ? { key, dir: s.dir === "asc" ? "desc" : "asc" } : { key, dir: "desc" }));

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-sm">
          <thead>
            <tr className="border-b border-hair text-[11px] uppercase tracking-wide text-faint">
              {cols.map((c) => {
                const active = sort.key === c.key;
                const Arrow = !active ? ChevronsUpDown : sort.dir === "asc" ? ArrowUp : ArrowDown;
                return (
                  <th
                    key={c.key}
                    aria-sort={active ? (sort.dir === "asc" ? "ascending" : "descending") : "none"}
                    className={`px-2.5 py-2 font-medium ${c.numeric ? "text-right" : "text-left"} ${
                      c.essential ? "" : "hidden xl:table-cell"
                    }`}
                  >
                    <button
                      onClick={() => toggle(c.key)}
                      className={`inline-flex items-center gap-1 hover:text-ink ${active ? "text-ink" : ""} ${
                        c.numeric ? "flex-row-reverse" : ""
                      }`}
                    >
                      <Arrow className="h-3 w-3" />
                      {c.label}
                    </button>
                  </th>
                );
              })}
              <th className="px-2 py-2" />
            </tr>
          </thead>
          <tbody>
            {sorted.map((m) => (
              <tr key={m.ticker} className="border-b border-hair/60 last:border-0 hover:bg-elevated/40">
                {/* Name — links to the deep dive; role chip below. */}
                <td className="px-2.5 py-2">
                  <Link href={`/stock/${m.ticker}`} className="group block">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-semibold text-ink group-hover:text-accent">{m.ticker}</span>
                      {m.source === "user" && (
                        <span className="h-1.5 w-1.5 rounded-full bg-teal-400" title="You added this" />
                      )}
                    </div>
                    <span className="block truncate text-xs text-faint">{m.name}</span>
                  </Link>
                  <span className={`mt-1 inline-block rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${GROUP[m.group].chip}`}>
                    {m.role}
                  </span>
                  {/* Mobile-only second line: the collapsed columns, house idiom. */}
                  <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-0.5 text-[11px] text-muted xl:hidden">
                    <span>1y <span className="tnum text-ink">{fmtLens(m.ret_1y, lens)}</span></span>
                    <span>since <span className="tnum text-ink">{fmtLens(m.since_added_pct, lens)}</span></span>
                    <span className={m.above_ma200 ? "text-up" : "text-down"}>{m.above_ma200 == null ? "—" : m.above_ma200 ? "trend intact" : "trend broken"}</span>
                    <span>worst <span className="tnum text-down">{fmtLens(m.max_drawdown_1y, lens)}</span></span>
                    <span>vol <span className="tnum text-ink">{m.vol_90d != null ? `${m.vol_90d}%` : "—"}</span></span>
                  </div>
                </td>
                <td className="tnum px-2.5 py-2 text-right">{m.price != null ? fmtCurrency(m.price) : "—"}</td>
                <td className={`tnum px-2.5 py-2 text-right ${toneOf(m.change_pct)}`}>{fmtLens(m.change_pct, lens)}</td>
                <td className={`tnum hidden px-2.5 py-2 text-right xl:table-cell ${toneOf(m.ret_1y)}`}>{fmtLens(m.ret_1y, lens)}</td>
                <td className="hidden px-2.5 py-2 text-right xl:table-cell">
                  <div className={`tnum ${toneOf(m.since_added_pct)}`}>{fmtLens(m.since_added_pct, lens)}</div>
                  {m.since_added_voo_pct != null && (
                    <div className="tnum text-[10px] text-faint">vs VOO {fmtLens(m.since_added_voo_pct, lens)}</div>
                  )}
                </td>
                <td className="tnum hidden px-2.5 py-2 text-right text-muted xl:table-cell">{m.vol_90d != null ? `${m.vol_90d}%` : "—"}</td>
                <td className="hidden px-2.5 py-2 text-right xl:table-cell">
                  {m.above_ma200 == null ? (
                    <span className="text-faint">—</span>
                  ) : (
                    <span className={`rounded-md border px-1.5 py-0.5 text-[10px] ${m.above_ma200 ? "border-up/30 bg-up/5 text-up" : "border-down/30 bg-down/5 text-down"}`}>
                      {m.above_ma200 ? "intact" : "broken"}
                    </span>
                  )}
                </td>
                <td className="tnum hidden px-2.5 py-2 text-right text-down xl:table-cell">{fmtLens(m.max_drawdown_1y, lens)}</td>
                <td className="px-2.5 py-2 text-right">
                  <div className="flex flex-col items-end gap-1">
                    <span className={`tnum rounded-md px-1.5 py-0.5 text-[10px] font-medium ${attentionClass(m.attention)}`}>
                      {m.attention.toFixed(0)}
                    </span>
                    {m.flag_codes.length > 0 && (
                      <span className="text-[10px] text-faint">{prettyFlag(m.flag_codes[0])}{m.flag_codes.length > 1 ? ` +${m.flag_codes.length - 1}` : ""}</span>
                    )}
                  </div>
                </td>
                <td className="px-2 py-2 text-right">
                  <button
                    onClick={() => onRemove(m.ticker)}
                    aria-label={`Remove ${m.ticker} from watchlist`}
                    className="rounded-md p-1 text-faint transition-colors hover:bg-down/10 hover:text-down"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="border-t border-hair px-3 py-2 text-[11px] text-faint">
        Sorted by attention — fresh changes and hazards float up. Tap any column to re-sort.
        Numbers are descriptive, never advice.
      </p>
    </div>
  );
}

function toneOf(v: number | null): string {
  if (v == null) return "text-muted";
  return v > 0 ? "text-up" : v < 0 ? "text-down" : "text-muted";
}

function attentionClass(score: number): string {
  if (score >= 12) return "bg-down/15 text-down";
  if (score >= 4) return "bg-amber-400/15 text-amber-300";
  return "bg-elevated text-muted";
}
