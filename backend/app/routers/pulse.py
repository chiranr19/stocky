# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""GET /pulse — sector heatmap + watchlist metrics."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import PulseResponse
from ..services import pulse as pulse_service
from ..services.market import MarketDataError

router = APIRouter(tags=["pulse"])


@router.get("/pulse", response_model=PulseResponse)
def get_pulse() -> PulseResponse:
    """Today's market pulse for the seeded watchlist and sector ETFs."""
    try:
        return pulse_service.build_pulse()
    except MarketDataError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
