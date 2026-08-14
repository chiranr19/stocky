# Stocky — Frontend

Next.js (App Router, TypeScript) + Tailwind. Dark fintech "analyst's workbench".

## Run

```bash
npm install
cp .env.local.example .env.local
npm run dev        # http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL` in `.env.local` if the backend isn't on
`http://localhost:8000`.

## Structure

```
src/
  app/
    layout.tsx              nav + budget provider + ⌘K palette + footer
    page.tsx                Pulse: overview + sector breakdown + movers + watchlist
    explore/page.tsx        risk map + scanners + signals
    compare/page.tsx        normalized growth + stats + correlation + distributions
    stock/[ticker]/page.tsx deep dive: candles + RSI + score + fundamentals
    time-machine/page.tsx   backtest vs VOO
    calendar/page.tsx       earnings + macro dates
  components/
    Nav, CommandPalette, BudgetControl, FreshnessBadge
    overview/  sectors/  explore/  compare/  stock/  pulse/  stocks/  learn/
    ui/        Term (glossary popover), primitives, Sparkline, States, Disclaimer
  lib/
    api.ts       typed fetchers          types.ts   mirrors backend models
    budget.tsx   global affordability cap  glossary.ts  ~35 teaching terms
    useHealth.ts data-freshness polling    format.ts    formatters
```

## Notes

- **Charts:** Recharts (scatter/line/area/histogram) + `lightweight-charts`
  (deep-dive candlesticks). See the root `README.md` for why (vs Tremor).
- The whole app is dark by design; semantic Tailwind tokens (`bg`, `panel`, `up`,
  `down`, `accent`, …) live in `tailwind.config.ts`.
- Every metric label is wrapped in `<Term k="…">` → click for a plain-English
  popover sourced from `lib/glossary.ts`.
- The **Max/share** budget control (global, persisted) drives every budget-aware
  endpoint; `useHealth` polls `/health/data` for the freshness badge + warm-up bar.
- `npm run build` skips ESLint (no config shipped) — see `next.config.mjs`.
