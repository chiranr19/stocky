"""Pydantic response models for the API.

These mirror the TypeScript types in ``frontend/src/lib/types.ts`` — keep the
two in sync when changing shapes.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Pulse
# --------------------------------------------------------------------------- #
class SectorTile(BaseModel):
    etf: str
    sector: str
    change_pct: float
    weight: float = Field(description="Relative treemap sizing, ~S&P 500 share.")


class WatchlistCard(BaseModel):
    ticker: str
    name: str
    price: float
    change_abs: float
    change_pct: float
    range_52w_low: float
    range_52w_high: float
    range_52w_position: float = Field(ge=0, le=1, description="0 = at low, 1 = at high.")
    volume: int
    avg_volume_30d: float
    volume_ratio: float
    unusual_volume: bool
    big_mover: bool
    sparkline: list[float] = Field(description="Recent closes, oldest → newest.")


class PulseResponse(BaseModel):
    as_of: date
    benchmark: str
    sectors: list[SectorTile]
    watchlist: list[WatchlistCard]


# --------------------------------------------------------------------------- #
# Time Machine
# --------------------------------------------------------------------------- #
class PricePoint(BaseModel):
    date: date
    value: float


class DrawdownInfo(BaseModel):
    peak_date: date
    trough_date: date
    peak_value: float
    trough_value: float
    drawdown_pct: float = Field(description="Signed, e.g. -34.2 means a 34.2% dip.")


class BenchmarkResult(BaseModel):
    ticker: str
    end_value: float
    total_return_pct: float
    path: list[PricePoint]


class TimeMachineResult(BaseModel):
    ticker: str
    name: str
    start_date: date
    end_date: date
    amount: float
    shares: float
    start_price: float
    end_price: float
    start_value: float
    end_value: float
    total_return_pct: float
    annualized_return_pct: float | None
    max_drawdown: DrawdownInfo
    path: list[PricePoint]
    benchmark: BenchmarkResult
    outperformance_pct: float = Field(
        description="Ticker total return minus benchmark total return, in points."
    )


# --------------------------------------------------------------------------- #
# System: data health + universe
# --------------------------------------------------------------------------- #
class DataHealth(BaseModel):
    status: str = Field(description="warming | ready | idle (background warm-up state).")
    tickers_loaded: int
    tickers_total: int
    priority_total: int
    warm_loaded: int
    latest_trading_date: date | None
    expected_session: date
    sessions_behind: int
    is_fresh: bool = Field(description="True when we're at most one session behind.")
    last_ingest_at: datetime | None
    anomalies_count: int
    failed_count: int
    snapshot_date: str = Field(description="Date the S&P 500 membership was snapshotted.")


class UniverseItem(BaseModel):
    ticker: str
    name: str
    sector: str | None


# --------------------------------------------------------------------------- #
# Analytics: shared stock row (reused across sectors / movers / riskmap / signals)
# --------------------------------------------------------------------------- #
class StockRow(BaseModel):
    ticker: str
    name: str
    sector: str | None
    price: float
    change_pct: float
    spark: list[float]
    range_52w_position: float
    avg_dollar_volume: float
    above_ma50: bool
    above_ma200: bool
    rsi14: float | None
    vol_90d: float | None
    ret_1m: float | None
    ret_3m: float | None
    ret_1y: float | None
    max_drawdown_1y: float
    volume_ratio: float
    gap_pct: float
    cross: str | None
    cross_date: date | None
    rsi_signal: str | None
    # Present only where the stock was scored by the screener.
    score: float | None = None
    factors: dict[str, float] | None = None


# --------------------------------------------------------------------------- #
# Analytics: market overview
# --------------------------------------------------------------------------- #
class IndexTile(BaseModel):
    ticker: str
    label: str
    name: str
    value: float
    change_pct: float
    unit: str
    spark: list[float]


class BreadthStats(BaseModel):
    members: int
    pct_above_ma50: float
    pct_above_ma200: float
    advancers: int
    decliners: int
    new_highs_52w: int
    new_lows_52w: int


class OverviewResponse(BaseModel):
    as_of: date
    tiles: list[IndexTile]
    breadth: BreadthStats


# --------------------------------------------------------------------------- #
# Analytics: sectors
# --------------------------------------------------------------------------- #
class SectorPanel(BaseModel):
    gics: str
    label: str
    etf: str
    etf_change_pct: float
    members_total: int
    members_affordable: int
    breadth_pct_up: float
    avg_change_pct: float
    top: list[StockRow]  # full ranked list; UI shows top-N + "show all"


class SectorsResponse(BaseModel):
    as_of: date
    budget: float | None
    weights: dict[str, float]
    sectors: list[SectorPanel]


# --------------------------------------------------------------------------- #
# Analytics: risk/reward map
# --------------------------------------------------------------------------- #
class RiskPoint(BaseModel):
    ticker: str
    name: str
    sector: str
    vol_90d: float
    ret_1y: float
    price: float
    score: float | None = None


class RiskMapResponse(BaseModel):
    as_of: date
    budget: float | None
    points: list[RiskPoint]
    benchmark: RiskPoint | None


# --------------------------------------------------------------------------- #
# Analytics: trend signals
# --------------------------------------------------------------------------- #
class SignalsResponse(BaseModel):
    as_of: date
    budget: float | None
    golden_crosses: list[StockRow]
    death_crosses: list[StockRow]
    overbought: list[StockRow]
    oversold: list[StockRow]


# --------------------------------------------------------------------------- #
# Analytics: compare
# --------------------------------------------------------------------------- #
class CompareSeries(BaseModel):
    ticker: str
    name: str
    points: list[PricePoint]  # normalized to 100 at the window start


class CompareStat(BaseModel):
    ticker: str
    name: str
    total_return_pct: float | None
    annualized_return_pct: float | None
    vol_90d: float | None
    max_drawdown_pct: float
    ret_1y: float | None


class CompareResponse(BaseModel):
    start_date: date
    end_date: date
    series: list[CompareSeries]
    stats: list[CompareStat]
    correlation: dict  # {labels: [...], matrix: [[...]]}
    histograms: dict[str, dict]  # ticker -> {counts, edges}


# --------------------------------------------------------------------------- #
# Analytics: stock deep dive
# --------------------------------------------------------------------------- #
class Candle(BaseModel):
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int


class SeriesPoint(BaseModel):
    date: date
    value: float | None


class StockDetail(BaseModel):
    ticker: str
    name: str
    sector: str | None
    sub_industry: str | None
    row: StockRow
    candles: list[Candle]
    ma50: list[SeriesPoint]
    ma200: list[SeriesPoint]
    rsi: list[SeriesPoint]
    histogram: dict
    benchmark_histogram: dict


class Fundamentals(BaseModel):
    ticker: str
    available: bool
    market_cap: float | None = None
    trailing_pe: float | None = None
    forward_pe: float | None = None
    beta: float | None = None
    dividend_yield: float | None = None
    profit_margin: float | None = None
    short_percent_of_float: float | None = None
    fifty_two_week_high: float | None = None
    fifty_two_week_low: float | None = None
    fetched_at: datetime | None = None


# --------------------------------------------------------------------------- #
# Calendar
# --------------------------------------------------------------------------- #
class EarningsEvent(BaseModel):
    ticker: str
    name: str
    date: date


class MacroEvent(BaseModel):
    date: date
    label: str
    kind: str  # 'fed' | 'cpi' | 'jobs' | ...


class CalendarResponse(BaseModel):
    earnings: list[EarningsEvent]
    macro: list[MacroEvent]
