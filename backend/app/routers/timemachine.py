"""GET /timemachine — backtest a lump-sum investment vs the benchmark."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, HTTPException, Query

from ..models import TimeMachineResult
from ..services import timemachine as tm_service
from ..services.market import MarketDataError

router = APIRouter(tags=["timemachine"])


@router.get("/timemachine", response_model=TimeMachineResult)
def get_time_machine(
    ticker: str = Query(..., min_length=1, max_length=10, description="e.g. NVDA"),
    date: dt.date = Query(..., description="Purchase date, YYYY-MM-DD."),
    amount: float = Query(..., gt=0, description="Dollars invested on that date."),
) -> TimeMachineResult:
    """What would ``amount`` invested in ``ticker`` on ``date`` be worth today?"""
    today = dt.date.today()
    if date >= today:
        raise HTTPException(status_code=400, detail="Date must be in the past.")

    try:
        return tm_service.run_time_machine(ticker, date, amount)
    except MarketDataError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        # e.g. not enough price history between `date` and today.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
