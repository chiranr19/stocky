// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import Link from "next/link";
import type { BasketMember } from "@/lib/types";
import { GROUP, GROUP_ORDER } from "./shared";

export function RoleLegend({ members, laws }: { members: BasketMember[]; laws: string[] }) {
  return (
    <div className="space-y-6">
      {GROUP_ORDER.map((g) => {
        const list = members.filter((m) => m.group === g);
        if (!list.length) return null;
        return (
          <div key={g}>
            <div className="mb-2 flex items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: GROUP[g].hex }} />
              <h3 className="text-sm font-semibold tracking-tight text-ink">{GROUP[g].label}</h3>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {list.map((m) => (
                <Link
                  key={m.ticker}
                  href={`/stock/${m.ticker}`}
                  className="card group flex flex-col gap-1.5 p-3.5 transition-colors hover:border-white/15"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold tracking-tight text-ink">{m.ticker}</span>
                    <span className={`rounded-md border px-1.5 py-0.5 text-[10px] font-medium ${GROUP[m.group].chip}`}>
                      {m.role}
                    </span>
                  </div>
                  <p className="text-xs leading-relaxed text-muted">{m.role_story}</p>
                  <p className="mt-0.5 text-[11px] italic leading-relaxed text-ink/70">
                    {m.role_lesson}
                  </p>
                </Link>
              ))}
            </div>
          </div>
        );
      })}

      <div className="rounded-xl border border-accent/25 bg-accent/5 p-4">
        <h3 className="mb-2 text-sm font-semibold tracking-tight text-accent">
          Five laws this watchlist keeps teaching
        </h3>
        <ol className="space-y-1.5">
          {laws.map((law, i) => (
            <li key={i} className="flex gap-2 text-sm leading-relaxed text-muted">
              <span className="tnum text-accent/60">{i + 1}.</span>
              {law}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
