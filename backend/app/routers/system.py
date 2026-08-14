"""System endpoints: data health + the searchable universe."""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter

from ..config import (
    SP500_SNAPSHOT_DATE,
    UNIVERSE,
    display_name,
    sector_of,
    settings,
)
from ..models import DataHealth, UniverseItem
from ..services import market
from ..services.trading_calendar import most_recent_session, sessions_behind

router = APIRouter(tags=["system"])


@router.get("/health/data", response_model=DataHealth)
def health_data() -> DataHealth:
    """Warm-up progress + how current the cached data is vs the NYSE calendar."""
    h = market.data_health()
    today = dt.date.today()
    latest = h["latest_trading_date"]
    expected = most_recent_session(today)
    behind = sessions_behind(latest, today) if latest is not None else 9999

    return DataHealth(
        status=h["status"],
        tickers_loaded=h["tickers_loaded"],
        tickers_total=h["tickers_total"],
        priority_total=h["priority_total"],
        warm_loaded=h["warm_loaded"],
        latest_trading_date=latest,
        expected_session=expected,
        sessions_behind=behind,
        is_fresh=(latest is not None and behind <= 1),
        last_ingest_at=h["last_ingest_at"],
        anomalies_count=h["anomalies_count"],
        failed_count=len(h["failed_tickers"]),
        snapshot_date=SP500_SNAPSHOT_DATE,
    )


@router.get("/universe", response_model=list[UniverseItem])
def universe() -> list[UniverseItem]:
    """Every searchable ticker (S&P 500 + the benchmark) for the ⌘K palette."""
    tickers = list(dict.fromkeys([*UNIVERSE, settings.benchmark]))
    return [
        UniverseItem(ticker=t, name=display_name(t), sector=sector_of(t))
        for t in tickers
    ]
