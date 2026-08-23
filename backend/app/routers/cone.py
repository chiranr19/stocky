# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""GET /cone — the cone of uncertainty for one ticker.

A range of plausible futures resampled from the stock's own past daily moves —
never a point prediction. See ``services/cone.py`` for the method.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..models import ConeResponse
from ..services import cone as cone_service

router = APIRouter(tags=["analytics"])


@router.get("/cone", response_model=ConeResponse)
def get_cone(
    ticker: str = Query(..., description="Ticker to simulate."),
    horizon: int = Query(
        126, description="Trading days ahead: 21 (1m), 63 (3m), 126 (6m), or 252 (1y)."
    ),
) -> ConeResponse:
    """Percentile bands + a few sample paths for the requested horizon."""
    try:
        return cone_service.build_cone(ticker, horizon)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"'{ticker.upper()}' isn't in the analyzed universe yet — "
            "add it to your watchlist to bring it in.",
        ) from None
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
