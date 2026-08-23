# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Stock deep-dive + on-demand fundamentals."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import Fundamentals, StockDetail
from ..services import analytics, fundamentals
from ..services.market import MarketDataError

router = APIRouter(tags=["stock"])


@router.get("/stock/{ticker}", response_model=StockDetail)
def stock_detail(ticker: str) -> StockDetail:
    try:
        return analytics.build_stock_detail(ticker)
    except MarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/stock/{ticker}/fundamentals", response_model=Fundamentals)
def stock_fundamentals(ticker: str) -> Fundamentals:
    return fundamentals.get_fundamentals(ticker)
