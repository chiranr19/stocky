"""Analytics endpoints: overview, sectors, movers, riskmap, signals, compare."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from ..config import DEFAULT_BUDGET
from ..models import (
    CompareResponse,
    OverviewResponse,
    RadarResponse,
    RiskMapResponse,
    SectorsResponse,
    SignalsResponse,
    StockRow,
    WatchoutsResponse,
)
from ..services import analytics, radar

router = APIRouter(tags=["analytics"])

MoverType = Literal["gainers", "losers", "volume", "highs", "lows", "gaps"]
RadarLookback = Literal["1m", "2m", "3m"]


def resolve_budget(budget: float | None) -> float | None:
    """None → default $200 cap; ≤0 → no cap; else the given cap."""
    if budget is None:
        return DEFAULT_BUDGET
    if budget <= 0:
        return None
    return budget


@router.get("/overview", response_model=OverviewResponse)
def overview() -> OverviewResponse:
    return analytics.build_overview()


@router.get("/sectors", response_model=SectorsResponse)
def sectors(budget: float | None = Query(None, description="Max share price; ≤0 = no cap.")):
    return analytics.build_sectors(resolve_budget(budget))


@router.get("/movers", response_model=list[StockRow])
def movers(
    type: MoverType = Query("gainers"),
    budget: float | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
) -> list[StockRow]:
    return analytics.build_movers(type, resolve_budget(budget), limit)


@router.get("/riskmap", response_model=RiskMapResponse)
def riskmap(budget: float | None = Query(None)) -> RiskMapResponse:
    return analytics.build_riskmap(resolve_budget(budget))


@router.get("/signals", response_model=SignalsResponse)
def signals(budget: float | None = Query(None)) -> SignalsResponse:
    return analytics.build_signals(resolve_budget(budget))


@router.get("/radar", response_model=RadarResponse)
def entry_radar(
    budget: float | None = Query(None, description="Max share price; ≤0 = no cap."),
    lookback: RadarLookback = Query("3m", description="Pullback window: 1m/2m/3m."),
    limit: int = Query(30, ge=1, le=100),
) -> RadarResponse:
    """Pullback setups ranked by entry score, with historical echo stats."""
    return radar.build_radar(resolve_budget(budget), lookback, limit)


@router.get("/watchouts", response_model=WatchoutsResponse)
def watchouts(
    budget: float | None = Query(None, description="Max share price; ≤0 = no cap."),
    limit: int = Query(30, ge=1, le=100),
) -> WatchoutsResponse:
    """Stocks carrying the heaviest named risk patterns — the bad-setup showcase."""
    return analytics.build_watchouts(resolve_budget(budget), limit)


@router.get("/compare", response_model=CompareResponse)
def compare(
    tickers: str = Query(..., description="Comma-separated, e.g. NVDA,AMD,PLTR (VOO auto-added)."),
) -> CompareResponse:
    parsed = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    if not parsed:
        raise HTTPException(status_code=400, detail="Provide at least one ticker.")
    if len(parsed) > 4:
        raise HTTPException(status_code=400, detail="Compare at most 4 tickers.")
    return analytics.build_compare(parsed)
