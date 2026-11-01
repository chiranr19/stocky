// ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Loader2, Plus, RotateCcw } from "lucide-react";
import { addToWatchlist, getUniverse } from "@/lib/api";
import type { UniverseItem, WatchlistEntry } from "@/lib/types";

/** Inline add-a-ticker box with universe autocomplete + free-text fallback. */
export function AddTickerBox({ onChanged }: { onChanged: () => void }) {
  const [universe, setUniverse] = useState<UniverseItem[]>([]);
  const [input, setInput] = useState("");
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getUniverse().then(setUniverse).catch(() => setUniverse([]));
  }, []);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const q = input.trim().toUpperCase();
  const matches = useMemo(() => {
    if (!q) return [];
    return universe
      .filter((u) => u.ticker.startsWith(q) || u.name.toUpperCase().includes(q))
      .slice(0, 6);
  }, [q, universe]);

  async function submit(ticker: string) {
    const t = ticker.trim().toUpperCase();
    if (!t) return;
    setOpen(false);
    setInput("");
    setError(null);
    setPending(t);
    try {
      await addToWatchlist(t);
      onChanged();
    } catch (e) {
      // A 404 carries the server's reason: an unknown symbol, or a stopped feed
      // with the date its data ends.
      const msg = (e as { status?: number }).status === 404
        ? (e as Error).message || `No price data for '${t}' — check the symbol.`
        : (e as { status?: number }).status === 422
          ? "That doesn't look like a ticker."
          : (e as Error).message;
      setError(msg);
    } finally {
      setPending(null);
    }
  }

  return (
    <div ref={ref} className="relative">
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <input
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              setOpen(true);
              setError(null);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit(matches[0]?.ticker ?? input);
              if (e.key === "Escape") setOpen(false);
            }}
            placeholder="Add a ticker (e.g. DVA, KO)…"
            className="w-full rounded-lg border border-hair bg-elevated px-3 py-2 text-sm uppercase outline-none placeholder:normal-case placeholder:text-faint focus:border-accent"
            aria-label="Add a ticker to your watchlist"
          />
          {open && (matches.length > 0 || q.length >= 1) && (
            <div className="absolute left-0 right-0 top-full z-30 mt-1 overflow-hidden rounded-lg border border-hair bg-elevated shadow-glow">
              {matches.map((u) => (
                <button
                  key={u.ticker}
                  onClick={() => submit(u.ticker)}
                  className="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-panel"
                >
                  <span className="font-medium text-ink">{u.ticker}</span>
                  <span className="truncate pl-3 text-xs text-faint">{u.name}</span>
                </button>
              ))}
              {q.length >= 1 && q.length <= 6 && !matches.some((u) => u.ticker === q) && (
                <button
                  onClick={() => submit(q)}
                  className="flex w-full items-center gap-2 border-t border-hair px-3 py-2 text-left text-sm text-accent hover:bg-panel"
                >
                  <Plus className="h-3.5 w-3.5" /> Add “{q}”
                </button>
              )}
            </div>
          )}
        </div>
        <button
          onClick={() => submit(matches[0]?.ticker ?? input)}
          disabled={!q || pending != null}
          className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {pending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
        </button>
      </div>
      {pending && (
        <p className="mt-1.5 flex items-center gap-1.5 text-xs text-muted">
          <Loader2 className="h-3 w-3 animate-spin" /> Warming {pending} — fetching its history…
        </p>
      )}
      {error && <p className="mt-1.5 text-xs text-down">{error}</p>}
    </div>
  );
}

/** Chips of removed names; clicking restores them (a re-add reactivates). */
export function HiddenStrip({
  hidden,
  onChanged,
}: {
  hidden: WatchlistEntry[];
  onChanged: () => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  if (!hidden.length) return null;

  async function restore(ticker: string) {
    setBusy(ticker);
    try {
      await addToWatchlist(ticker);
      onChanged();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs">
      <span className="text-faint">Hidden:</span>
      {hidden.map((h) => (
        <button
          key={h.ticker}
          onClick={() => restore(h.ticker)}
          disabled={busy === h.ticker}
          className="inline-flex items-center gap-1 rounded-md border border-hair bg-panel px-2 py-1 text-muted transition-colors hover:border-accent/40 hover:text-accent"
        >
          {busy === h.ticker ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
          {h.ticker}
        </button>
      ))}
    </div>
  );
}
