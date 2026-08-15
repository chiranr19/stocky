"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Command as CommandIcon } from "lucide-react";
import { useHealth } from "@/lib/useHealth";
import { BudgetControl } from "./BudgetControl";
import { FreshnessBadge } from "./FreshnessBadge";

const LINKS = [
  { href: "/", label: "Pulse" },
  { href: "/radar", label: "Radar" },
  { href: "/watchouts", label: "Watch-outs" },
  { href: "/explore", label: "Explore" },
  { href: "/compare", label: "Compare" },
  { href: "/time-machine", label: "Time Machine" },
  { href: "/calendar", label: "Calendar" },
];

export function Nav() {
  const pathname = usePathname();
  const health = useHealth();

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <header className="sticky top-0 z-40 border-b border-hair bg-bg/80 backdrop-blur-lg">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-6 gap-y-3 px-4 py-3 sm:px-6">
        {/* Wordmark */}
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-accent-dim text-sm font-bold text-white shadow-glow">
            S
          </div>
          <span className="text-lg font-semibold tracking-tight">Stocky</span>
        </Link>

        {/* Primary nav */}
        <nav className="flex items-center gap-1 text-sm">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`rounded-md px-2.5 py-1.5 transition-colors ${
                isActive(l.href)
                  ? "bg-elevated text-ink"
                  : "text-muted hover:text-ink"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>

        {/* Right cluster */}
        <div className="ml-auto flex items-center gap-3">
          <BudgetControl />
          <FreshnessBadge health={health} />
          <button
            onClick={() =>
              document.dispatchEvent(
                new KeyboardEvent("keydown", { key: "k", metaKey: true }),
              )
            }
            className="hidden items-center gap-1.5 rounded-lg border border-hair bg-panel px-2.5 py-1.5 text-xs text-muted transition-colors hover:border-white/15 hover:text-ink lg:flex"
            title="Search (⌘K)"
          >
            <CommandIcon className="h-3.5 w-3.5" />
            <kbd className="tnum text-[10px]">⌘K</kbd>
          </button>
        </div>
      </div>
    </header>
  );
}
