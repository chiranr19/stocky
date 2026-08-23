# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
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
    # Curated teaching role (watchlist members only; None for the rest).
    role: str | None = None
    role_story: str | None = None
    role_lesson: str | None = None


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
    # Depth proof — how much history backs the historical stats.
    history_span_days: int | None = None
    median_sessions: int | None = None
    thinnest_ticker: str | None = None
    thinnest_sessions: int | None = None


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
# Reading layer: plain-English interpretation of what the data means
# --------------------------------------------------------------------------- #
class Reading(BaseModel):
    aspect: str = Field(description="trend | rsi | volatility | position | vix | …")
    headline: str
    detail: str = Field(description="What it says + what veterans do with it.")
    tone: str = Field(description="constructive | caution | neutral — never advice.")
    caveat: str = Field(description="What would make this reading wrong.")
    analogy: str = Field(default="", description="Everyday-life metaphor for the pattern.")


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
    readings: list[Reading] = []  # what today's market picture means


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
# Analytics: Entry Radar (pullback setups + historical echoes)
# --------------------------------------------------------------------------- #
class EchoStats(BaseModel):
    """Forward outcomes of past setups like today's — base rates, not predictions."""

    n: int = Field(description="How many similar past episodes were found.")
    median_fwd_pct: float = Field(description="Median return over the next ~month.")
    win_rate: float = Field(description="Share of episodes that ended positive, 0-1.")
    worst_pct: float
    best_pct: float
    kind: str = Field(
        default="exact",
        description="'exact' = same depth bucket; 'at_least' = widened to any dip ≥ min_depth_pct.",
    )
    min_depth_pct: float = 0.0
    bucket_lo: float = 0.0
    bucket_hi: float = 0.0
    n_years: int = Field(default=0, description="Distinct calendar years the episodes span.")
    confidence: str = Field(
        default="low",
        description="high | medium | low — sample size AND spread across market regimes.",
    )
    p25_pct: float | None = Field(default=None, description="25th percentile forward return.")
    p75_pct: float | None = Field(default=None, description="75th percentile forward return.")
    n_benchmarked: int = Field(
        default=0, description="Episodes where VOO had data over the same forward window."
    )
    beat_benchmark: int = Field(
        default=0, description="Of those, how many beat VOO over that window."
    )
    median_excess_pct: float | None = Field(
        default=None, description="Median (stock − VOO) return over the same windows."
    )


class RiskFlag(BaseModel):
    """A named pattern that makes a setup good or bad, with the reasoning."""

    code: str
    label: str
    kind: str = Field(description="risk | strength")
    severity: str = Field(description="high | medium | low")
    why: str
    what_vets_do: str
    analogy: str = Field(default="", description="Everyday-life metaphor for the pattern.")


class WatchoutRow(BaseModel):
    row: StockRow
    risk_score: float = Field(description="Weighted severity of risk flags; higher = poorer setup.")
    flags: list[RiskFlag]


class WatchoutsResponse(BaseModel):
    as_of: date
    budget: float | None
    rows: list[WatchoutRow]


class RadarRow(BaseModel):
    row: StockRow
    depth_pct: float = Field(description="% below the lookback-window high today.")
    depth_rank: float = Field(
        description="Percentile of today's depth within this stock's own history."
    )
    falling_knife: bool = Field(description="True when trading below its MA200.")
    entry_score: float
    entry_factors: dict[str, float]  # depth, trend, rsi, quality (0-100)
    echo: EchoStats | None = None  # None = not enough similar history
    flags: list[RiskFlag] = []  # risks visible even on a good-looking setup


class RadarResponse(BaseModel):
    as_of: date
    budget: float | None
    lookback: str  # '1m' | '2m' | '3m'
    horizon_days: int
    weights: dict[str, float]
    rows: list[RadarRow]


# --------------------------------------------------------------------------- #
# Learn: the watchlist through the teaching lens (powers /learn + the digest)
# --------------------------------------------------------------------------- #
class BasketMember(BaseModel):
    """One watchlist name as a teaching subject: its curated role + live numbers."""

    ticker: str
    name: str
    role: str = Field(description="Short label, e.g. 'The anchor tenant'.")
    group: str = Field(description="mega | umbrella | wildcard | benchmark | scout — narrative family.")
    role_story: str
    role_lesson: str
    role_source: str = Field(default="curated", description="curated | archetype (derived from the numbers).")
    source: str = Field(default="seed", description="seed | user — how it joined the watchlist.")
    added_at: date | None = None
    # Live numbers — all optional so a young listing (XE) degrades to 'unmeasurable'.
    price: float | None = None
    change_pct: float | None = None
    vol_90d: float | None = None
    ret_1y: float | None = None
    above_ma200: bool | None = None
    depth_pct: float | None = None
    max_drawdown_1y: float | None = None
    range_52w_position: float | None = None
    since_added_pct: float | None = Field(default=None, description="Return since it joined the list.")
    since_added_voo_pct: float | None = Field(default=None, description="VOO over the identical window.")
    spark: list[float] = Field(default=[], description="Recent closes, oldest → newest.")
    series_1y: list[float] = Field(
        default=[], description="~60 downsampled adj-closes for the underwater/race charts."
    )
    series_start: date | None = Field(
        default=None, description="Date of series_1y's first point — for aligning the race."
    )
    regime_1y: list[bool] = Field(
        default=[], description="Above (True) / below its 200-day line at each series_1y point."
    )
    rain: list[float | None] = Field(
        default=[], description="Daily % returns aligned to rain_dates (None = didn't trade that day)."
    )
    echo: EchoStats | None = None
    flag_codes: list[str] = Field(default=[], description="Flag codes in play (labels resolve client-side).")
    attention: float = Field(default=0.0, description="Needs-attention score: fresh events + hazards float up.")
    measurable: bool = Field(
        default=True, description="False when history is too thin to compute risk — a lesson, not an error."
    )


class WatchEvent(BaseModel):
    """One plain-English day-over-day change on a watchlist name."""

    ticker: str
    name: str
    code: str
    headline: str
    detail: str
    tone: str = Field(description="constructive | caution | neutral")
    severity: int = Field(description="1..5 ordering weight; higher = more urgent.")


class BasketResponse(BaseModel):
    as_of: date
    roles_as_of: str = Field(description="Date the curated stories were written; their numbers are frozen there.")
    laws: list[str] = Field(description="The transferable lessons this watchlist keeps teaching.")
    members: list[BasketMember]  # watchlist order
    correlation: dict = Field(description="{labels, matrix} over members with enough history + VOO.")
    correlation_note: str = Field(default="", description="Which members were left out of the matrix and why.")
    benchmark_ticker: str
    events: list[WatchEvent] = Field(default=[], description="What changed on the watchlist since yesterday.")
    rain_dates: list[date] = Field(
        default=[], description="The shared last-60 trading calendar the rain strips align to."
    )
    constellation: dict = Field(
        default={},
        description="{nodes:[{ticker,x,y}], mst:[{a,b,r}]} — the correlation map + its skeleton.",
    )


# --------------------------------------------------------------------------- #
# Watchlist management (the app's first mutations)
# --------------------------------------------------------------------------- #
class WatchlistEntryModel(BaseModel):
    ticker: str
    name: str
    added_at: date
    added_price: float | None = None
    source: str  # 'seed' | 'user'
    active: bool


class WatchlistResponse(BaseModel):
    entries: list[WatchlistEntryModel]
    hidden: list[WatchlistEntryModel]


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
# Cone of uncertainty (v1.0) — the only honest "forecast": a range of plausible
# futures resampled from the stock's OWN past daily moves, never a point call.
# All band/path values are MULTIPLIERS of the start price (1.0 = today), so the
# frontend renders them lens-native (× a hypothetical $ position, or as %).
# --------------------------------------------------------------------------- #
class ConePoint(BaseModel):
    session: int = Field(description="Trading days ahead (0 = today).")
    p10: float = Field(description="10th percentile multiplier of the start price.")
    p25: float
    p50: float = Field(description="The middle path (50th percentile).")
    p75: float
    p90: float


class ConeBenchmark(BaseModel):
    ticker: str
    name: str
    bands: list[ConePoint]
    end: ConePoint


class ConeResponse(BaseModel):
    ticker: str
    name: str
    as_of: date
    horizon_sessions: int
    start_price: float = Field(description="Today's share price — the anchor the multipliers scale.")
    n_paths: int = Field(description="How many simulated futures were drawn.")
    n_history_sessions: int = Field(description="Past daily moves the simulation resampled from.")
    vol_annualized_pct: float = Field(description="Annualized volatility of those daily moves.")
    bands: list[ConePoint] = Field(description="Pointwise percentile envelope, downsampled.")
    sample_paths: list[list[float]] = Field(
        description="A handful of individual simulated futures (multipliers) for the replay."
    )
    end: ConePoint = Field(description="The percentile spread at the final session.")
    samples_up: int = Field(description="Of the sample paths, how many ended above today.")
    samples_down: int
    benchmark: ConeBenchmark | None = None
    caveat: str = Field(description="Where this lies to you — always attached.")


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
    entry: RadarRow | None = None  # Entry Radar position (3M lookback)
    readings: list[Reading] = []  # how to read this stock's current chart
    flags: list[RiskFlag] = []  # named risk/strength patterns
    risk_score: float = 0.0


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


# --------------------------------------------------------------------------- #
# Followed Filers (v0.8): public insider (SEC Form 4) + congressional (STOCK Act)
# disclosures, studied — never a copy-trade signal. Every row keeps a provenance
# URL, and every enriched number traces to our own price cache.
# --------------------------------------------------------------------------- #
class DisclosedTrade(BaseModel):
    source: str = Field(description="edgar | house | senate")
    filing_id: str = Field(description="Accession / DocID — the provenance key.")
    filer: str
    filer_role: str
    ticker: str
    name: str
    asset_class: str = Field(description="equity | option | other (only equity is priceable).")
    action: str = Field(description="buy | sell | grant | other.")
    trade_date: date
    filed_date: date = Field(description="When the public could first know it.")
    lag_days: int = Field(description="filed_date − trade_date: the disclosure lag.")
    shares: float | None = None
    price: float | None = None
    value_lo: float = Field(description="Disclosed dollar range low (congress) or shares×price.")
    value_hi: float = Field(description="Disclosed dollar range high (congress) or shares×price.")
    scheduled: bool = Field(description="10b5-1 pre-arranged plan — not a reaction to news.")
    url: str = Field(description="Link to the original official filing.")
    priceable: bool = Field(description="Equity mapped to our price universe (enrichment valid).")
    # Enrichment — all from our own price cache, None when unavailable.
    since_trade_pct: float | None = Field(
        default=None, description="Price change from the trade date to now."
    )
    since_filed_pct: float | None = Field(
        default=None, description="Price change from the disclosure date to now (what a follower gets)."
    )
    lag_tax_pct: float | None = Field(
        default=None, description="Price move between trade and disclosure — the copier's built-in cost."
    )
    voo_since_filed_pct: float | None = Field(
        default=None, description="VOO over the same since-disclosure window (opportunity cost)."
    )


class FilerBaseRate(BaseModel):
    """Has following this filer's *disclosed buys* actually paid, historically?

    Forward outcomes measured from each buy's disclosure date (the only date a
    follower could act), pooled across every ticker they bought. Base rates with
    N and confidence always attached — never a prediction, never advice.
    """

    filer: str
    window_days: int
    n: int = Field(description="Disclosed buys with a full forward window.")
    median_fwd_pct: float
    win_rate: float = Field(description="Share of those buys up after the window, 0-1.")
    worst_pct: float
    best_pct: float
    p25_pct: float | None = None
    p75_pct: float | None = None
    n_years: int = Field(default=0, description="Distinct calendar years the buys span.")
    confidence: str = Field(description="high | medium | low — sample size AND spread.")
    n_benchmarked: int = 0
    beat_benchmark: int = Field(default=0, description="Of those, how many beat VOO.")
    median_excess_pct: float | None = Field(
        default=None, description="Median (stock − VOO) over the same windows."
    )
    median_lag_days: int = Field(default=0, description="Typical disclosure lag for this filer.")


class FilerNotice(BaseModel):
    """A named, caveated pattern across the filings — the 'flags' for disclosures."""

    code: str = Field(description="cluster_buying | scheduled_sale | filer_sold_radar_name")
    headline: str
    detail: str
    tone: str = Field(description="constructive | caution | neutral — never advice.")
    caveat: str = Field(description="What would make this reading wrong.")
    tickers: list[str] = []
    filers: list[str] = []


class FilersResponse(BaseModel):
    as_of: date
    kind: str = Field(description="all | insider | congress")
    source_label: str = Field(description="Which official sources backed this payload.")
    filings_through: date | None = Field(
        default=None, description="Freshest filing date on record (honest freshness)."
    )
    note: str = Field(description="Persistent honesty note (e.g. no per-trade Trump data exists).")
    trades: list[DisclosedTrade]
    base_rates: list[FilerBaseRate]
    notices: list[FilerNotice]
