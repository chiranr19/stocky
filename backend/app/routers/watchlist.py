# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""GET/POST/DELETE /watchlist — the app's first mutations: manage the living list.

Adding a ticker fetches its full history (so echoes work immediately) and is
idempotent — an already-active name returns 200 unchanged, which also settles
double-add races. Removing hides (restorable) rather than deletes.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response

from ..config import display_name
from ..models import WatchlistEntryModel, WatchlistResponse
from ..services import watchlist as watchlist_service
from ..services.market import MarketDataError

router = APIRouter(tags=["watchlist"])


def _to_model(e) -> WatchlistEntryModel:
    return WatchlistEntryModel(
        ticker=e.ticker,
        name=display_name(e.ticker),
        added_at=e.added_at,
        added_price=e.added_price,
        source=e.source,
        active=e.active,
    )


@router.get("/watchlist", response_model=WatchlistResponse)
def get_watchlist() -> WatchlistResponse:
    """The active cast plus the hidden (removed, restorable) names."""
    return WatchlistResponse(
        entries=[_to_model(e) for e in watchlist_service.entries()],
        hidden=[_to_model(e) for e in watchlist_service.hidden()],
    )


@router.post("/watchlist/{ticker}", response_model=WatchlistEntryModel, status_code=201)
def add_ticker(ticker: str, response: Response) -> WatchlistEntryModel:
    """Add (or restore) a ticker. 200 if it was already active, 201 if new/restored."""
    try:
        already = ticker.strip().upper() in watchlist_service.tickers()
        entry = watchlist_service.add(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except MarketDataError:
        raise HTTPException(
            status_code=404,
            detail=f"No price data for '{ticker.strip().upper()}' — check the symbol.",
        ) from None
    if already:
        response.status_code = 200
    return _to_model(entry)


@router.delete("/watchlist/{ticker}", status_code=204)
def remove_ticker(ticker: str) -> Response:
    """Hide a ticker (restorable). 404 if it isn't on the active list."""
    try:
        watchlist_service.remove(ticker)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(status_code=204)
