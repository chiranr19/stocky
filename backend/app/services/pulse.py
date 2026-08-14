"""Build the /pulse payload: sector heatmap + watchlist cards."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from ..config import (
    BIG_MOVER_PCT,
    SECTORS,
    UNUSUAL_VOLUME_RATIO,
    WATCHLIST,
    display_name,
    settings,
)
from ..models import PulseResponse, SectorTile, WatchlistCard
from . import market

# ~14 months of calendar days: enough for a 52-week range plus a 30-day volume
# average with room for weekends/holidays.
_WATCHLIST_LOOKBACK = dt.timedelta(days=430)
# Sector tiles only need a couple of trading days to compute today's move.
_SECTOR_LOOKBACK = dt.timedelta(days=12)
_SPARKLINE_POINTS = 30


def _daily_change_pct(close: pd.Series) -> float:
    if len(close) < 2:
        return 0.0
    prev, last = float(close.iloc[-2]), float(close.iloc[-1])
    return (last / prev - 1.0) * 100.0 if prev else 0.0


def build_card(ticker: str, df: pd.DataFrame) -> WatchlistCard:
    """Compute a single watchlist card from that ticker's price history."""
    df = df.sort_index()
    close = df["close"]
    volume = df["volume"]

    price = float(close.iloc[-1])
    prev = float(close.iloc[-2]) if len(close) > 1 else price
    change_abs = price - prev
    change_pct = _daily_change_pct(close)

    window_52w = close.tail(252)
    low_52w = float(window_52w.min())
    high_52w = float(window_52w.max())
    span = high_52w - low_52w
    position = (price - low_52w) / span if span > 0 else 0.5
    position = min(1.0, max(0.0, position))

    volume_today = int(volume.iloc[-1])
    # Average of the prior 30 sessions, excluding today.
    prior = volume.iloc[-31:-1]
    avg_volume_30d = float(prior.mean()) if len(prior) else float(volume.mean())
    volume_ratio = volume_today / avg_volume_30d if avg_volume_30d else 1.0

    sparkline = [round(float(x), 2) for x in close.tail(_SPARKLINE_POINTS)]

    return WatchlistCard(
        ticker=ticker,
        name=display_name(ticker),
        price=round(price, 2),
        change_abs=round(change_abs, 2),
        change_pct=round(change_pct, 2),
        range_52w_low=round(low_52w, 2),
        range_52w_high=round(high_52w, 2),
        range_52w_position=round(position, 4),
        volume=volume_today,
        avg_volume_30d=round(avg_volume_30d, 0),
        volume_ratio=round(volume_ratio, 2),
        unusual_volume=volume_ratio >= UNUSUAL_VOLUME_RATIO,
        big_mover=abs(change_pct) >= BIG_MOVER_PCT,
        sparkline=sparkline,
    )


def build_sector_tiles(end: dt.date) -> list[SectorTile]:
    etfs = [str(s["etf"]) for s in SECTORS]
    histories = market.get_histories(etfs, end - _SECTOR_LOOKBACK, end)

    tiles: list[SectorTile] = []
    for spec in SECTORS:
        etf = str(spec["etf"])
        df = histories.get(etf)
        change_pct = _daily_change_pct(df["close"]) if df is not None and not df.empty else 0.0
        tiles.append(
            SectorTile(
                etf=etf,
                sector=str(spec["label"]),
                change_pct=round(change_pct, 2),
                weight=float(spec["weight"]),  # type: ignore[arg-type]
            )
        )
    return tiles


def build_pulse() -> PulseResponse:
    today = dt.date.today()

    tiles = build_sector_tiles(today)

    histories = market.get_histories(WATCHLIST, today - _WATCHLIST_LOOKBACK, today)
    cards: list[WatchlistCard] = []
    as_of = today
    for ticker in WATCHLIST:
        df = histories.get(ticker)
        if df is None or df.empty:
            continue
        cards.append(build_card(ticker, df))
        as_of = max(as_of, df.index.max().date()) if not df.empty else as_of

    # as_of should reflect the latest *actual* trading day we have data for.
    latest_dates = [df.index.max().date() for df in histories.values() if not df.empty]
    if latest_dates:
        as_of = max(latest_dates)

    return PulseResponse(
        as_of=as_of,
        benchmark=settings.benchmark,
        sectors=tiles,
        watchlist=cards,
    )
