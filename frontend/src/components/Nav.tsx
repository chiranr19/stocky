"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Command as CommandIcon } from "lucide-react";
import { useHealth } from "@/lib/useHealth";
import { BudgetControl } from "./BudgetControl";
import { LensControl } from "./LensControl";
import { FreshnessBadge } from "./FreshnessBadge";

const LINKS = [
  { href: "/", label: "Pulse" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/learn", label: "Learn" },
  { href: "/radar", label: "Radar" },
  { href: "/watchouts", label: "Watch-outs" },
  { href: "/filers", label: "Filers" },
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
      <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6">
        {/* Top row: wordmark + controls. On desktop the nav joins this row.
            Wraps rather than overflowing when the controls don't fit. */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 lg:gap-x-6">
          <Link href="/" className="flex shrink-0 items-center gap-2.5">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-accent-dim text-sm font-bold text-white shadow-glow">
              S
            </div>
            <span className="text-lg font-semibold tracking-tight">Stocky</span>
          </Link>

          {/* Desktop nav sits inline; on phones it moves to its own scroll row. */}
          <nav className="hidden items-center gap-1 text-sm lg:flex">
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

          <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-3">
            <BudgetControl />
            <LensControl />
            <FreshnessBadge health={health} />
            <button
              onClick={() =>
                document.dispatchEvent(
                  new KeyboardEvent("keydown", { key: "k", metaKey: true }),
                )
              }
              className="flex items-center gap-1.5 rounded-lg border border-hair bg-panel px-2.5 py-1.5 text-xs text-muted transition-colors hover:border-white/15 hover:text-ink"
              title="Search (⌘K)"
              aria-label="Search"
            >
              <CommandIcon className="h-3.5 w-3.5" />
              <kbd className="tnum hidden text-[10px] lg:inline">⌘K</kbd>
            </button>
          </div>
        </div>

        {/* Phone nav: one horizontally scrollable row — never wraps, never hides
            a destination behind a menu the user has to discover. */}
        <nav className="-mx-4 mt-2.5 flex gap-1 overflow-x-auto px-4 pb-0.5 text-sm [scrollbar-width:none] sm:-mx-6 sm:px-6 lg:hidden [&::-webkit-scrollbar]:hidden">
          {LINKS.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`shrink-0 whitespace-nowrap rounded-md px-2.5 py-1.5 transition-colors ${
                isActive(l.href)
                  ? "bg-elevated text-ink"
                  : "text-muted hover:text-ink"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
