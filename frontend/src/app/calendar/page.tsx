"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CalendarDays, Landmark, Megaphone } from "lucide-react";
import { getCalendar } from "@/lib/api";
import type { CalendarResponse } from "@/lib/types";
import { fmtDate } from "@/lib/format";
import { SectionHeader } from "@/components/ui/primitives";
import { TeachBanner } from "@/components/learn/TeachBanner";
import { PageLesson } from "@/components/learn/PageLesson";
import { PAGE_LESSONS } from "@/lib/pageLessons";
import { Loading } from "@/components/ui/States";

const KIND_STYLE: Record<string, string> = {
  fed: "border-accent/40 text-accent bg-accent/10",
  cpi: "border-up/40 text-up bg-up/10",
  jobs: "border-down/40 text-down bg-down/10",
};

export default function CalendarPage() {
  const [data, setData] = useState<CalendarResponse | null>(null);

  useEffect(() => {
    getCalendar().then(setData).catch(() => setData({ earnings: [], macro: [] }));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-xl font-semibold tracking-tight">Calendar</h1>
        <p className="text-sm text-muted">
          The dates that move stocks — earnings and the macro releases everyone watches.
        </p>
      </div>

      <PageLesson {...PAGE_LESSONS.calendar} />

      <TeachBanner>
        Stocks often jump on scheduled dates, not random news. Earnings reset a company&apos;s
        story; <span className="text-ink">Fed</span> and <span className="text-ink">CPI</span> days
        move the whole market at once.
      </TeachBanner>

      {!data ? (
        <Loading label="Loading the calendar…" />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <section>
            <SectionHeader icon={Megaphone} title="Upcoming earnings" sub="watchlist + top picks" />
            <div className="card divide-y divide-hair/60">
              {data.earnings.length === 0 ? (
                <div className="px-4 py-8 text-center text-sm text-faint">
                  No earnings dates available right now (source is best-effort).
                </div>
              ) : (
                data.earnings.map((e) => (
                  <Link
                    key={e.ticker + e.date}
                    href={`/stock/${e.ticker}`}
                    className="flex items-center justify-between px-4 py-3 transition-colors hover:bg-elevated/60"
                  >
                    <div>
                      <div className="tnum text-sm font-medium">{e.ticker}</div>
                      <div className="truncate text-xs text-muted">{e.name}</div>
                    </div>
                    <div className="tnum text-sm text-ink">{fmtDate(e.date)}</div>
                  </Link>
                ))
              )}
            </div>
          </section>

          <section>
            <SectionHeader icon={Landmark} title="Macro calendar" sub="Fed · CPI · jobs" />
            <div className="card divide-y divide-hair/60">
              {data.macro.map((m) => (
                <div key={m.date + m.label} className="flex items-center justify-between px-4 py-3">
                  <div className="flex items-center gap-3">
                    <CalendarDays className="h-4 w-4 text-faint" />
                    <span className="text-sm text-ink">{m.label}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-md border px-1.5 py-0.5 text-[10px] uppercase ${KIND_STYLE[m.kind] ?? "border-hair text-muted"}`}
                    >
                      {m.kind}
                    </span>
                    <span className="tnum text-sm text-muted">{fmtDate(m.date)}</span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
