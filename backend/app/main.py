# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Hindsight FastAPI application entrypoint.

Run locally with:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from . import __version__
from .config import settings
from .db import get_connection
from .routers import (
    analytics,
    calendar,
    cone,
    filers,
    learn,
    pulse,
    stock,
    system,
    timemachine,
    watchlist,
)
from .services import market

app = FastAPI(
    title="Stocky API",
    version=__version__,
    summary="A stock-market learning instrument — not a trading terminal.",
)

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(system.router)
app.include_router(analytics.router)
app.include_router(stock.router)
app.include_router(calendar.router)
app.include_router(pulse.router)
app.include_router(timemachine.router)
app.include_router(filers.router)
app.include_router(learn.router)
app.include_router(watchlist.router)
app.include_router(cone.router)


@app.on_event("startup")
def _startup() -> None:
    # Open the connection (and create tables) eagerly so the first request is fast.
    get_connection()
    # Kick off the full-universe warm-up in the background (priority tickers
    # first) so the dashboard is usable within seconds while the rest streams in.
    if settings.warm_on_start:
        market.start_background_warm()


@app.get("/", tags=["meta"])
def root() -> dict[str, object]:
    return {
        "name": "Stocky API",
        "version": __version__,
        "disclaimer": "Educational tool. Not financial advice.",
        "endpoints": [
            "/overview", "/sectors", "/movers", "/radar", "/watchouts",
            "/riskmap", "/signals", "/filers", "/learn/basket", "/watchlist",
            "/compare", "/cone", "/stock/{ticker}", "/calendar",
            "/timemachine", "/universe", "/health/data", "/docs",
        ],
    }


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
