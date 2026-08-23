"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, GraduationCap, X } from "lucide-react";
import { Term } from "@/components/ui/Term";

const KEY = "stocky.starthere.dismissed";

export function StartHere() {
  const [dismissed, setDismissed] = useState(true); // assume dismissed until we read storage

  useEffect(() => {
    setDismissed(window.localStorage.getItem(KEY) === "1");
  }, []);

  const dismiss = () => {
    setDismissed(true);
    window.localStorage.setItem(KEY, "1");
  };
  const reopen = () => {
    setDismissed(false);
    window.localStorage.removeItem(KEY);
  };

  if (dismissed) {
    return (
      <button
        onClick={reopen}
        className="inline-flex items-center gap-1.5 text-xs text-faint transition-colors hover:text-accent"
      >
        <GraduationCap className="h-3.5 w-3.5" />
        New here? What am I looking at?
      </button>
    );
  }

  return (
    <div className="card relative animate-fade-in overflow-hidden p-5">
      <div
        className="pointer-events-none absolute inset-0 opacity-60"
        style={{
          background:
            "radial-gradient(600px 200px at 12% -20%, rgba(124,107,255,0.18), transparent 70%)",
        }}
      />
      <button
        onClick={dismiss}
        className="absolute right-3 top-3 rounded-md p-1 text-faint transition-colors hover:bg-elevated hover:text-ink"
        aria-label="Dismiss"
      >
        <X className="h-4 w-4" />
      </button>

      <div className="relative">
        <div className="mb-2 flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-accent" />
          <h2 className="text-sm font-semibold tracking-tight">What am I looking at?</h2>
        </div>
        <p className="mb-3 max-w-2xl text-sm text-muted">
          Stocky is a place to <b>learn the market by using it</b> — not a place to get
          tips. Everything here is educational. Any dotted-underlined word is clickable
          for a plain-English explanation (try it).
        </p>
        <ul className="grid max-w-3xl gap-2 text-sm text-muted sm:grid-cols-2">
          <li className="flex gap-2">
            <span className="text-accent">1.</span>
            <span>
              Everything is compared to <Term k="voo">VOO</Term> — a single fund that
              owns all 500 big U.S. companies at once. It&apos;s the &quot;just buy the
              whole market&quot; baseline every pick has to beat.
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent">2.</span>
            <span>
              The <Term k="score">Stocky score</Term> ranks affordable stocks in each{" "}
              <Term k="sector">sector</Term>. It&apos;s a transparent starting point —{" "}
              <b>not a recommendation</b>.
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent">3.</span>
            <span>
              The <b>Max/share</b> control up top hides anything pricier than your budget,
              so you only see stocks you could actually buy a whole share of.
            </span>
          </li>
          <li className="flex gap-2">
            <span className="text-accent">4.</span>
            <span>
              <b>Explore</b> and <b>Compare</b> hold the veteran tools —{" "}
              <Term k="rsi">RSI</Term>, <Term k="golden_cross">crosses</Term>,{" "}
              <Term k="correlation">correlation</Term>, risk-vs-reward — each with a
              caption on when it lies to you.
            </span>
          </li>
        </ul>
        <Link
          href="/learn"
          className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-accent/30 bg-accent/10 px-3 py-1.5 text-sm font-medium text-accent transition-colors hover:bg-accent/20"
        >
          Prefer stories to charts? Take the guided tour
          <ArrowRight className="h-3.5 w-3.5" />
        </Link>
      </div>
    </div>
  );
}
