"""Followed Filers endpoint: public insider & congressional disclosures, studied."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Query

from ..models import FilersResponse
from ..services import filers

router = APIRouter(tags=["filers"])

FilerKind = Literal["all", "insider", "congress"]
FilerAction = Literal["all", "buy", "sell", "grant"]


@router.get("/filers", response_model=FilersResponse)
def followed_filers(
    kind: FilerKind = Query("all", description="all | insider | congress."),
    action: FilerAction = Query("all", description="Filter the table: all | buy | sell | grant."),
    limit: int = Query(60, ge=1, le=200),
) -> FilersResponse:
    """Recent disclosed trades by tracked public figures, with the lag tax and
    historical base rates attached. Educational — never advice."""
    return filers.build_filers(kind, limit, action)
