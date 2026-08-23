# Stocky gotchas

Repo-specific quirks. Machine-wide ones live in `~/.claude/GOTCHAS.md`.

## Frontend shows "Can't reach the API at http://localhost:8000" while uvicorn seems fine  (2026-08-21)
- **Context:** Opening the dashboard through the Claude Code browser pane (or any time another local project is running).
- **Cause:** Port 8000 was held by a *different* project's dev server, so the backend either failed to bind or died; Chrome reports the dead connection as a CORS error ("No 'Access-Control-Allow-Origin' header"), which misdirects debugging toward `cors_origins` — that config was fine.
- **Fix:** The backend now runs on **8010** (`.claude/launch.json`), and `frontend/.env.local` sets `NEXT_PUBLIC_API_URL=http://localhost:8010`. If the API URL ever changes, remember `NEXT_PUBLIC_*` vars are baked at dev-server start — restart `npm run dev` *and* hard-reload the tab (the old bundle keeps the old URL).
- **Scope:** this repo

## Pytest hangs on `db_lock.__enter__` → `_lock.acquire()` only when a TestClient test runs after certain others  (2026-08-22)
- **Context:** The app's first `fastapi.testclient.TestClient` tests (v0.9 `/watchlist` router). They pass in isolation but hang the whole suite when they run after `test_filers.py`. faulthandler shows a worker thread stuck at `db.py` `_lock.acquire()`.
- **Cause:** `db._lock` is a module-global `RLock`. Some code path (a filers ingest background thread) acquires it and the thread **terminates without releasing** — the RLock stays owned by a dead thread. Reentrancy hides this: every later main-thread test re-acquires fine, so it's invisible. FastAPI runs sync endpoints on a **worker thread**, which is the first non-owner to try `acquire()` → blocks forever; the main thread waits on the request → deadlock.
- **Fix:** The `db` fixture in `tests/conftest.py` now rebinds `db_module._lock = threading.RLock()` at setup, so every DB-touching test starts with a pristine lock (`db_lock`/`get_connection` read the global each call, so rebinding is safe). Real root cause worth fixing at the source: whatever thread leaks the acquire in the filers path should use `with db_lock():` and never outlive it.
- **Scope:** this repo

## Next dev throws `Cannot find module './NNN.js'` + a wall of 404/500s after many edits  (2026-08-23)
- **Context:** After a long editing session (adding several components), the `/watchlist` browser tab filled with `Cannot find module './624.js'` (from `next/dist/server/lib/start-server.js`), 404s for `_next/static` chunks, a failed `webpack-hmr` WebSocket, and a spurious React error boundary firing in a component that was actually fine. `preview_logs` showed the route **compiled 200** — so the *server* was healthy; the browser was requesting stale chunk hashes.
- **Cause:** Next 14's dev build cache (`.next/`) desynchronized from the running bundle after rapid HMR churn. Chunk hashes changed but a cached manifest kept pointing at the old ones; the missing-chunk error then cascades into misleading component-level errors.
- **Fix:** Stop the frontend dev server, `rm -rf frontend/.next`, restart it, then hard-reload the tab (a soft `navigate` can keep the stale manifest). Independently, harden any chart component that reads `.length` on an API field with optional chaining (`x?.length ?? 0`) so a partial/old payload degrades instead of throwing.
- **Scope:** this repo

## Page renders unstyled / React never hydrates — core chunks (`main-app.js`, `layout.css`) 404 on every load  (2026-08-22)
- **Context:** Frontend dev server appears healthy (pages return 200) but the browser shows raw unstyled HTML, no data ever loads ("Reading the filings…" forever, freshness badge stuck at "connecting…"), and the console shows repeated 404s.
- **Cause:** A corrupted `.next` build cache — happens when two `next dev` instances briefly overlap on the same folder (parallel Claude sessions both starting "frontend"), or a dev server is killed mid-write. The chunk manifest then references files that don't exist; every page load 404s `main-app.js`/`layout.css`, so React never boots and zero API calls fire. Misdirects debugging toward the API/CORS — the API is fine.
- **Fix:** Stop the dev server, `rm -rf frontend/.next`, restart. Diagnose with DevTools ≫ Network: 404s on `_next/static/chunks/main-app.js` = this problem, not an API problem. Prevention: only one session should own the frontend dev server at a time.
- **Scope:** this repo

## IOException "File is already open in python.exe (PID …)" running a warm/ingest script  (2026-08-22)
- **Context:** Running `scripts/warm_filings.py` (or `warm_data.py`, or any script that opens `data/stocky.duckdb`) while the FastAPI preview backend is up.
- **Cause:** DuckDB is **single-writer** — one process at a time may open the file read-write. The running uvicorn backend holds it, so a second process (the script, or an ad-hoc `duckdb.connect`) errors immediately. This serializes CLI ingest against the live server.
- **Fix:** Stop the preview/uvicorn backend first (`preview_stop`, or Ctrl-C), run the script, then restart the backend. The DuckDB file persists between them, so the backend picks up whatever the script wrote (e.g. `disclosed_trades`). For tests, the `db` fixture in `tests/conftest.py` swaps an in-memory connection so suites never touch the locked file.
- **Scope:** this repo
