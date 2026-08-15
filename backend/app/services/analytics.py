"""Analytics orchestration: turn cached prices into endpoint payloads.

Computes the full metric set for the whole universe once per (data date, warm
progress) and memoizes it, then builds the /overview, /sectors, /movers,
/riskmap, /signals, /compare and /stock payloads on top. Reads only cached
DuckDB rows (never fetches inline) — the background warm-up owns fetching.
"""

from __future__ import annotations

import datetime as dt
import threading

import pandas as pd

from ..config import (
    DEFAULT_BUDGET,
    MACRO_META,
    SCORE_WEIGHTS,
    SECTORS,
    SUBINDUSTRY_BY_TICKER,
    display_name,
    sector_of,
    settings,
)
from ..models import (
    BreadthStats,
    Candle,
    CompareResponse,
    CompareSeries,
    CompareStat,
    IndexTile,
    OverviewResponse,
    PricePoint,
    Reading,
    RiskMapResponse,
    RiskPoint,
    SectorPanel,
    SectorsResponse,
    SeriesPoint,
    RiskFlag,
    SignalsResponse,
    StockDetail,
    StockRow,
    WatchoutRow,
    WatchoutsResponse,
)
from . import market
from .metrics import (
    StockMetrics,
    compute_metrics,
    correlation_matrix,
    moving_average,
    pullback_series,
    return_histogram,
    rsi,
)
from . import flags as flags_service
from . import insights
from .screener import ScoredStock, is_eligible, screen_by_sector
from .simulation import max_drawdown

_ANALYSIS_LOOKBACK = market.HISTORY_LOOKBACK
_TD_1Y = 252

# --------------------------------------------------------------------------- #
# Universe-wide metrics cache
# --------------------------------------------------------------------------- #
_lock = threading.Lock()
_cache: dict = {"key": None, "metrics": {}, "latest": None, "closes": {}}
_screen_cache: dict = {"key": None, "by_budget": {}}


def _max_date() -> dt.date | None:
    from ..db import db_lock

    with db_lock() as con:
        return con.execute("SELECT MAX(date) FROM prices").fetchone()[0]


def _load_metrics() -> tuple[dict[str, StockMetrics], dt.date | None, dict[str, pd.Series]]:
    end = dt.date.today()
    start = end - _ANALYSIS_LOOKBACK
    histories = market.read_cached(market.ALL_TICKERS, start, end)

    metrics: dict[str, StockMetrics] = {}
    closes: dict[str, pd.Series] = {}
    latest: dt.date | None = None
    for ticker, df in histories.items():
        m = compute_metrics(ticker, df)
        if m is not None:
            metrics[ticker] = m
            # Retained for the Entry Radar (pullback depth + historical echoes)
            # so it never has to re-query DuckDB per request.
            closes[ticker] = df["adj_close"].dropna()
        d = df.index.max().date()
        latest = d if latest is None else max(latest, d)
    return metrics, latest, closes


def universe_metrics() -> tuple[dict[str, StockMetrics], dt.date]:
    """Memoized per (data date, warm progress); recomputes as warm-up streams in."""
    key = (_max_date(), market.warm_state().loaded)
    with _lock:
        if _cache["key"] == key and _cache["metrics"]:
            return _cache["metrics"], _cache["latest"]
    metrics, latest, closes = _load_metrics()
    latest = latest or dt.date.today()
    with _lock:
        _cache.update(key=key, metrics=metrics, latest=latest, closes=closes)
    return metrics, latest


def universe_closes() -> dict[str, pd.Series]:
    """Adj-close series per ticker, same cache generation as universe_metrics()."""
    universe_metrics()  # ensure the cache is warm/current
    with _lock:
        return _cache["closes"]


def _sector_scores(budget: float | None) -> dict[str, list[ScoredStock]]:
    metrics, _ = universe_metrics()
    key = (_cache["key"], budget)
    if _screen_cache["key"] != _cache["key"]:
        _screen_cache["key"] = _cache["key"]
        _screen_cache["by_budget"] = {}
    cached = _screen_cache["by_budget"].get(budget)
    if cached is not None:
        return cached
    result = screen_by_sector(metrics, {t: sector_of(t) for t in metrics if sector_of(t)}, budget)
    _screen_cache["by_budget"][budget] = result
    return result


# --------------------------------------------------------------------------- #
# Row helper
# --------------------------------------------------------------------------- #
def to_row(m: StockMetrics, scored: ScoredStock | None = None) -> StockRow:
    return StockRow(
        ticker=m.ticker,
        name=display_name(m.ticker),
        sector=sector_of(m.ticker),
        price=m.price,
        change_pct=m.change_pct,
        spark=m.spark,
        range_52w_position=m.range_52w_position,
        avg_dollar_volume=m.avg_dollar_volume_20d,
        above_ma50=m.above_ma50,
        above_ma200=m.above_ma200,
        rsi14=m.rsi14,
        vol_90d=m.vol_90d,
        ret_1m=m.ret_1m,
        ret_3m=m.ret_3m,
        ret_1y=m.ret_1y,
        max_drawdown_1y=m.max_drawdown_1y,
        volume_ratio=m.volume_ratio,
        gap_pct=m.gap_pct,
        cross=m.cross,
        cross_date=m.cross_date,
        rsi_signal=m.rsi_signal,
        score=scored.score if scored else None,
        factors=scored.factors if scored else None,
    )


def _sp_members(metrics: dict[str, StockMetrics]) -> list[StockMetrics]:
    return [m for t, m in metrics.items() if sector_of(t) is not None]


# --------------------------------------------------------------------------- #
# /overview
# --------------------------------------------------------------------------- #
def build_overview() -> OverviewResponse:
    metrics, latest = universe_metrics()

    tiles: list[IndexTile] = []
    tile_specs = [
        (settings.benchmark, "S&P 500 (VOO)", "Vanguard S&P 500 ETF", "usd"),
        ("^VIX", MACRO_META["^VIX"]["label"], MACRO_META["^VIX"]["name"], "level"),
        ("^TNX", MACRO_META["^TNX"]["label"], MACRO_META["^TNX"]["name"], "percent"),
    ]
    for ticker, label, name, unit in tile_specs:
        m = metrics.get(ticker)
        if m is None:
            continue
        tiles.append(
            IndexTile(
                ticker=ticker,
                label=label,
                name=name,
                value=m.price,
                change_pct=m.change_pct,
                unit=unit,
                spark=m.spark,
            )
        )

    members = _sp_members(metrics)
    n = len(members) or 1
    breadth = BreadthStats(
        members=len(members),
        pct_above_ma50=round(sum(m.above_ma50 for m in members) / n * 100, 1),
        pct_above_ma200=round(sum(m.above_ma200 for m in members) / n * 100, 1),
        advancers=sum(1 for m in members if m.change_pct > 0),
        decliners=sum(1 for m in members if m.change_pct < 0),
        new_highs_52w=sum(1 for m in members if m.is_new_high_52w),
        new_lows_52w=sum(1 for m in members if m.is_new_low_52w),
    )

    # What today's picture means, in plain English.
    readings: list[Reading] = []
    vix = metrics.get("^VIX")
    if vix is not None:
        readings.append(Reading(**vars(insights.vix_reading(vix.price))))
    readings.append(
        Reading(
            **vars(
                insights.breadth_reading(
                    breadth.pct_above_ma50, breadth.advancers, breadth.decliners
                )
            )
        )
    )
    tnx = metrics.get("^TNX")
    if tnx is not None:
        readings.append(Reading(**vars(insights.yield_reading(tnx.price, tnx.change_pct))))

    return OverviewResponse(as_of=latest, tiles=tiles, breadth=breadth, readings=readings)


# --------------------------------------------------------------------------- #
# /sectors
# --------------------------------------------------------------------------- #
def build_sectors(budget: float | None) -> SectorsResponse:
    metrics, latest = universe_metrics()
    scores = _sector_scores(budget)

    panels: list[SectorPanel] = []
    for spec in SECTORS:
        gics = str(spec["gics"])
        etf = str(spec["etf"])
        etf_m = metrics.get(etf)
        members = [m for t, m in metrics.items() if sector_of(t) == gics]
        n = len(members)
        up = sum(1 for m in members if m.change_pct > 0)
        avg_change = sum(m.change_pct for m in members) / n if n else 0.0
        ranked = scores.get(gics, [])
        panels.append(
            SectorPanel(
                gics=gics,
                label=str(spec["label"]),
                etf=etf,
                etf_change_pct=round(etf_m.change_pct, 2) if etf_m else 0.0,
                members_total=n,
                members_affordable=len(ranked),
                breadth_pct_up=round(up / n * 100, 1) if n else 0.0,
                avg_change_pct=round(avg_change, 2),
                top=[to_row(s.metrics, s) for s in ranked],
            )
        )
    return SectorsResponse(
        as_of=latest, budget=budget, weights=SCORE_WEIGHTS, sectors=panels
    )


# --------------------------------------------------------------------------- #
# /movers
# --------------------------------------------------------------------------- #
def build_movers(kind: str, budget: float | None, limit: int) -> list[StockRow]:
    metrics, _ = universe_metrics()
    eligible = [
        m for t, m in metrics.items() if sector_of(t) is not None and is_eligible(m, budget)
    ]

    if kind == "gainers":
        rows = sorted(eligible, key=lambda m: m.change_pct, reverse=True)
    elif kind == "losers":
        rows = sorted(eligible, key=lambda m: m.change_pct)
    elif kind == "volume":
        rows = sorted(eligible, key=lambda m: m.volume_ratio, reverse=True)
    elif kind == "highs":
        rows = sorted(
            [m for m in eligible if m.is_new_high_52w],
            key=lambda m: m.change_pct,
            reverse=True,
        )
    elif kind == "lows":
        rows = sorted([m for m in eligible if m.is_new_low_52w], key=lambda m: m.change_pct)
    elif kind == "gaps":
        rows = sorted(eligible, key=lambda m: abs(m.gap_pct), reverse=True)
    else:
        rows = []
    return [to_row(m) for m in rows[:limit]]


# --------------------------------------------------------------------------- #
# /riskmap
# --------------------------------------------------------------------------- #
def build_riskmap(budget: float | None) -> RiskMapResponse:
    metrics, latest = universe_metrics()
    points: list[RiskPoint] = []
    for t, m in metrics.items():
        gics = sector_of(t)
        if gics is None or not is_eligible(m, budget):
            continue
        if m.vol_90d is None or m.ret_1y is None:
            continue
        points.append(
            RiskPoint(
                ticker=t,
                name=display_name(t),
                sector=gics,
                vol_90d=m.vol_90d,
                ret_1y=m.ret_1y,
                price=m.price,
                score=None,
            )
        )

    bench = metrics.get(settings.benchmark)
    benchmark = None
    if bench and bench.vol_90d is not None and bench.ret_1y is not None:
        benchmark = RiskPoint(
            ticker=settings.benchmark,
            name=display_name(settings.benchmark),
            sector="Benchmark",
            vol_90d=bench.vol_90d,
            ret_1y=bench.ret_1y,
            price=bench.price,
        )
    return RiskMapResponse(as_of=latest, budget=budget, points=points, benchmark=benchmark)


# --------------------------------------------------------------------------- #
# /signals
# --------------------------------------------------------------------------- #
def build_signals(budget: float | None, limit: int = 40) -> SignalsResponse:
    metrics, latest = universe_metrics()
    eligible = [
        m for t, m in metrics.items() if sector_of(t) is not None and is_eligible(m, budget)
    ]

    golden = sorted(
        [m for m in eligible if m.cross == "golden"],
        key=lambda m: m.cross_date or dt.date.min,
        reverse=True,
    )
    death = sorted(
        [m for m in eligible if m.cross == "death"],
        key=lambda m: m.cross_date or dt.date.min,
        reverse=True,
    )
    overbought = sorted(
        [m for m in eligible if m.rsi_signal == "overbought"],
        key=lambda m: m.rsi14 or 0,
        reverse=True,
    )
    oversold = sorted(
        [m for m in eligible if m.rsi_signal == "oversold"], key=lambda m: m.rsi14 or 100
    )
    return SignalsResponse(
        as_of=latest,
        budget=budget,
        golden_crosses=[to_row(m) for m in golden[:limit]],
        death_crosses=[to_row(m) for m in death[:limit]],
        overbought=[to_row(m) for m in overbought[:limit]],
        oversold=[to_row(m) for m in oversold[:limit]],
    )


# --------------------------------------------------------------------------- #
# /watchouts — the "what a poor setup looks like" showcase
# --------------------------------------------------------------------------- #
def build_watchouts(budget: float | None, limit: int) -> WatchoutsResponse:
    """Stocks carrying the heaviest named risk patterns, worst first.

    The deliberate mirror of the Entry Radar: seeing *why* a setup is bad is
    what makes the good ones legible. Educational — not a sell list.
    """
    metrics, latest = universe_metrics()
    closes = universe_closes()

    rows: list[WatchoutRow] = []
    for ticker, m in metrics.items():
        if sector_of(ticker) is None:
            continue
        # Affordability still applies — these are the names they'd otherwise be
        # tempted by at this budget.
        if budget is not None and m.price > budget:
            continue

        # Pullback depth (3M) gives the falling-knife rule its teeth.
        depth_pct = None
        adj = closes.get(ticker)
        if adj is not None and len(adj) > 70:
            d = pullback_series(adj, 63)
            if not pd.isna(d.iloc[-1]):
                depth_pct = float(d.iloc[-1])

        found = flags_service.evaluate(m, depth_pct)
        risks = [f for f in found if f.kind == "risk"]
        if not risks:
            continue
        score = flags_service.risk_score(found)
        rows.append(
            WatchoutRow(
                row=to_row(m),
                risk_score=score,
                flags=[RiskFlag(**vars(f)) for f in risks],
            )
        )

    # Many names max out the same flag set, so break ties by actual damage done
    # (worst year first) — alphabetical order would teach nothing.
    rows.sort(
        key=lambda r: (
            -r.risk_score,
            r.row.ret_1y if r.row.ret_1y is not None else 0.0,
            r.row.ticker,
        )
    )
    return WatchoutsResponse(as_of=latest, budget=budget, rows=rows[:limit])


# --------------------------------------------------------------------------- #
# /compare
# --------------------------------------------------------------------------- #
def _downsample(series: pd.Series, max_points: int = 220) -> pd.Series:
    if len(series) <= max_points:
        return series
    step = len(series) // max_points
    sampled = series.iloc[::step]
    if sampled.index[-1] != series.index[-1]:
        sampled = pd.concat([sampled, series.iloc[[-1]]])
    return sampled


def build_compare(tickers: list[str]) -> CompareResponse:
    tickers = list(dict.fromkeys([t.upper() for t in tickers]))
    if settings.benchmark not in tickers:
        tickers.append(settings.benchmark)

    end = dt.date.today()
    start = end - dt.timedelta(days=400)
    histories = market.get_histories(tickers, start, end)

    # Align to the common window so normalization starts everyone at the same date.
    valid = {t: histories[t] for t in tickers if t in histories and len(histories[t]) > 30}
    if not valid:
        return CompareResponse(
            start_date=start, end_date=end, series=[], stats=[],
            correlation={"labels": [], "matrix": []}, histograms={},
        )
    common_start = max(df.index.min() for df in valid.values())

    series: list[CompareSeries] = []
    stats: list[CompareStat] = []
    adj_by_ticker: dict[str, pd.Series] = {}
    histograms: dict[str, dict] = {}

    for ticker, df in valid.items():
        adj = df.loc[df.index >= common_start, "adj_close"].dropna()
        if len(adj) < 2:
            continue
        adj_by_ticker[ticker] = adj
        normalized = adj / float(adj.iloc[0]) * 100.0
        ds = _downsample(normalized)
        series.append(
            CompareSeries(
                ticker=ticker,
                name=display_name(ticker),
                points=[
                    PricePoint(date=idx.date(), value=round(float(v), 2))
                    for idx, v in ds.items()
                ],
            )
        )

        total_return = (float(adj.iloc[-1]) / float(adj.iloc[0]) - 1.0) * 100.0
        days = (adj.index[-1] - adj.index[0]).days
        annualized = (
            ((float(adj.iloc[-1]) / float(adj.iloc[0])) ** (365.25 / days) - 1.0) * 100.0
            if days > 0
            else None
        )
        dd = max_drawdown(adj.to_numpy())
        rets = adj.pct_change().dropna()
        vol = float(rets.tail(90).std(ddof=1) * (252**0.5) * 100) if len(rets) > 2 else None
        ret_1y = (
            (float(adj.iloc[-1]) / float(adj.iloc[-1 - _TD_1Y]) - 1.0) * 100.0
            if len(adj) > _TD_1Y
            else None
        )
        stats.append(
            CompareStat(
                ticker=ticker,
                name=display_name(ticker),
                total_return_pct=round(total_return, 2),
                annualized_return_pct=round(annualized, 2) if annualized is not None else None,
                vol_90d=round(vol, 1) if vol is not None else None,
                max_drawdown_pct=dd.drawdown_pct,
                ret_1y=round(ret_1y, 2) if ret_1y is not None else None,
            )
        )
        histograms[ticker] = return_histogram(adj)

    correlation = correlation_matrix(adj_by_ticker, window=126)
    return CompareResponse(
        start_date=common_start.date(),
        end_date=end,
        series=series,
        stats=stats,
        correlation=correlation,
        histograms=histograms,
    )


# --------------------------------------------------------------------------- #
# /stock/{ticker}
# --------------------------------------------------------------------------- #
def build_stock_detail(ticker: str) -> StockDetail:
    ticker = ticker.upper()
    end = dt.date.today()
    start = end - _ANALYSIS_LOOKBACK
    df = market.get_history(ticker, start, end)  # raises MarketDataError if unknown
    df = df.sort_index()

    m = compute_metrics(ticker, df)
    if m is None:
        raise ValueError(f"Not enough price history for {ticker}.")

    # Scored only if it's an affordable S&P member at the default budget.
    scored = None
    gics = sector_of(ticker)
    if gics is not None:
        for s in _sector_scores(DEFAULT_BUDGET).get(gics, []):
            if s.ticker == ticker:
                scored = s
                break

    window = df.tail(_TD_1Y)
    candles = [
        Candle(
            date=idx.date(),
            open=round(float(r.open), 2),
            high=round(float(r.high), 2),
            low=round(float(r.low), 2),
            close=round(float(r.close), 2),
            volume=int(r.volume),
        )
        for idx, r in window.iterrows()
    ]

    ma50 = moving_average(df["close"], 50).tail(_TD_1Y)
    ma200 = moving_average(df["close"], 200).tail(_TD_1Y)
    rsi_s = rsi(df["adj_close"], 14).tail(_TD_1Y)

    def _pts(s: pd.Series) -> list[SeriesPoint]:
        return [
            SeriesPoint(
                date=idx.date(),
                value=None if pd.isna(v) else round(float(v), 2),
            )
            for idx, v in s.items()
        ]

    hist = return_histogram(df["adj_close"])
    bench_df = market.read_cached([settings.benchmark], start, end).get(settings.benchmark)
    bench_hist = (
        return_histogram(bench_df["adj_close"])
        if bench_df is not None and not bench_df.empty
        else {"counts": [], "edges": []}
    )

    # Local import: radar depends on this module, so the reverse edge stays lazy.
    from .radar import radar_for_ticker

    entry = radar_for_ticker(ticker)
    depth_pct = entry.depth_pct if entry else None
    readings = [Reading(**vars(r)) for r in insights.stock_readings(m, depth_pct)]
    found = flags_service.evaluate(m, depth_pct)

    return StockDetail(
        ticker=ticker,
        name=display_name(ticker),
        sector=gics,
        sub_industry=SUBINDUSTRY_BY_TICKER.get(ticker),
        row=to_row(m, scored),
        candles=candles,
        ma50=_pts(ma50),
        ma200=_pts(ma200),
        rsi=_pts(rsi_s),
        histogram=hist,
        benchmark_histogram=bench_hist,
        entry=entry,
        readings=readings,
        flags=[RiskFlag(**vars(f)) for f in found],
        risk_score=flags_service.risk_score(found),
    )
