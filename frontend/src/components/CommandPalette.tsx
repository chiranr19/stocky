// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import {
  BarChart3,
  CalendarDays,
  Clock,
  Crosshair,
  GitCompare,
  GraduationCap,
  Search,
  ShieldAlert,
  Star,
  TrendingUp,
} from "lucide-react";
import { getUniverse } from "@/lib/api";
import type { UniverseItem } from "@/lib/types";

const PAGES = [
  { label: "Pulse — market overview", href: "/", icon: BarChart3 },
  { label: "Watchlist — your living cast", href: "/watchlist", icon: Star },
  { label: "Learn — the market, told as stories", href: "/learn", icon: GraduationCap },
  { label: "Entry Radar — pullback setups", href: "/radar", icon: Crosshair },
  { label: "Watch-outs — what a bad setup looks like", href: "/watchouts", icon: ShieldAlert },
  { label: "Explore — scanners, risk map, signals", href: "/explore", icon: TrendingUp },
  { label: "Compare stocks", href: "/compare", icon: GitCompare },
  { label: "Time Machine", href: "/time-machine", icon: Clock },
  { label: "Calendar — earnings & macro dates", href: "/calendar", icon: CalendarDays },
];

export function CommandPalette() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [universe, setUniverse] = useState<UniverseItem[]>([]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  useEffect(() => {
    if (open && universe.length === 0) getUniverse().then(setUniverse).catch(() => {});
  }, [open, universe.length]);

  const go = (href: string) => {
    router.push(href);
    setOpen(false);
    setSearch("");
  };

  const typed = search.trim().toUpperCase();
  const hasExact = universe.some((u) => u.ticker === typed);

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Search stocks and pages"
      shouldFilter
      className="fixed inset-0 z-50 flex items-start justify-center bg-black/60 p-4 pt-[16vh] backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) setOpen(false);
      }}
    >
      <div className="w-full max-w-xl overflow-hidden rounded-xl border border-hair bg-panel shadow-glow">
        <div className="flex items-center gap-2 border-b border-hair px-3">
          <Search className="h-4 w-4 text-faint" />
          <Command.Input
            autoFocus
            value={search}
            onValueChange={setSearch}
            placeholder="Search any of 500 stocks, or jump to a page…"
            className="w-full bg-transparent py-3 text-sm text-ink outline-none placeholder:text-faint"
          />
          <kbd className="rounded border border-hair px-1.5 py-0.5 text-[10px] text-faint">
            ESC
          </kbd>
        </div>

        <Command.List className="max-h-80 overflow-y-auto p-2">
          <Command.Empty className="px-3 py-6 text-center text-sm text-faint">
            No matches.
          </Command.Empty>

          {typed && !hasExact && typed.length <= 6 && (
            <Command.Item
              value={`open ${typed}`}
              onSelect={() => go(`/stock/${typed}`)}
              className="flex cursor-pointer items-center gap-2 rounded-lg px-3 py-2 text-sm text-ink data-[selected=true]:bg-elevated"
            >
              <TrendingUp className="h-4 w-4 text-accent" />
              Open <span className="tnum font-medium">{typed}</span>
            </Command.Item>
          )}

          <Command.Group
            heading="Pages"
            className="[&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wide [&_[cmdk-group-heading]]:text-faint"
          >
            {PAGES.map((p) => (
              <Command.Item
                key={p.href}
                value={`page ${p.label}`}
                onSelect={() => go(p.href)}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm data-[selected=true]:bg-elevated"
              >
                <p.icon className="h-4 w-4 text-faint" />
                {p.label}
              </Command.Item>
            ))}
          </Command.Group>

          <Command.Group
            heading="Stocks"
            className="[&_[cmdk-group-heading]]:px-3 [&_[cmdk-group-heading]]:py-1.5 [&_[cmdk-group-heading]]:text-[11px] [&_[cmdk-group-heading]]:uppercase [&_[cmdk-group-heading]]:tracking-wide [&_[cmdk-group-heading]]:text-faint"
          >
            {universe.map((u) => (
              <Command.Item
                key={u.ticker}
                value={`${u.ticker} ${u.name}`}
                onSelect={() => go(`/stock/${u.ticker}`)}
                className="flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2 text-sm data-[selected=true]:bg-elevated"
              >
                <span className="tnum w-16 font-medium text-ink">{u.ticker}</span>
                <span className="truncate text-muted">{u.name}</span>
                <span className="ml-auto truncate text-[11px] text-faint">
                  {u.sector ?? ""}
                </span>
              </Command.Item>
            ))}
          </Command.Group>
        </Command.List>
      </div>
    </Command.Dialog>
  );
}
