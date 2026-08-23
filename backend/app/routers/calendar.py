# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Calendar endpoint: upcoming earnings + macro dates."""

from __future__ import annotations

from fastapi import APIRouter

from ..models import CalendarResponse
from ..services import calendar as calendar_service

router = APIRouter(tags=["calendar"])


@router.get("/calendar", response_model=CalendarResponse)
def calendar() -> CalendarResponse:
    return calendar_service.build_calendar()
