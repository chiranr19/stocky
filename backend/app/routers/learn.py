"""GET /learn/basket — the watchlist told as teaching stories with live numbers.

Budget-free by design: the watchlist is a fixed cast, so unlike the S&P-wide
/riskmap it never filters affordable names out (VOO, AMZN, VIST, XE all stay in).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import BasketResponse
from ..services import learn as learn_service
from ..services.market import MarketDataError

router = APIRouter(tags=["learn"])


@router.get("/learn/basket", response_model=BasketResponse)
def get_basket() -> BasketResponse:
    """Every watchlist name as a teaching subject: curated role + live metrics."""
    try:
        return learn_service.build_basket()
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
