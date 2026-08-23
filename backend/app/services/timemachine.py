# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Build the /timemachine payload: backtest a lump-sum vs the benchmark."""

from __future__ import annotations

import datetime as dt

import pandas as pd

from ..config import display_name, settings
from ..models import (
    BenchmarkResult,
    DrawdownInfo,
    PricePoint,
    TimeMachineResult,
)
from . import market
from .simulation import Investment, simulate_investment

# Cap the number of points sent to the frontend so the chart stays snappy on
# multi-year ranges; we downsample evenly, always keeping the last point.
_MAX_PATH_POINTS = 400


def _to_points(series: pd.Series) -> list[PricePoint]:
    if len(series) > _MAX_PATH_POINTS:
        step = len(series) // _MAX_PATH_POINTS
        sampled = series.iloc[::step]
        if sampled.index[-1] != series.index[-1]:
            sampled = pd.concat([sampled, series.iloc[[-1]]])
        series = sampled
    return [
        PricePoint(date=idx.date(), value=round(float(val), 2))
        for idx, val in series.items()
    ]


def _drawdown_info(inv: Investment) -> DrawdownInfo:
    dd = inv.max_drawdown
    index = inv.path.index
    return DrawdownInfo(
        peak_date=index[dd.peak_idx].date(),
        trough_date=index[dd.trough_idx].date(),
        peak_value=round(dd.peak_value, 2),
        trough_value=round(dd.trough_value, 2),
        drawdown_pct=dd.drawdown_pct,
    )


def run_time_machine(ticker: str, start: dt.date, amount: float) -> TimeMachineResult:
    ticker = ticker.upper()
    today = dt.date.today()
    benchmark = settings.benchmark

    # Fetch a small buffer before the start date so the first trading day on or
    # after `start` is captured even if `start` lands on a weekend/holiday.
    fetch_start = start - dt.timedelta(days=7)

    ticker_df = market.get_history(ticker, fetch_start, today)
    bench_df = market.get_history(benchmark, fetch_start, today)

    # Align to the requested start date (first available session at/after it).
    ticker_prices = ticker_df.loc[ticker_df.index >= pd.Timestamp(start), "adj_close"]
    bench_prices = bench_df.loc[bench_df.index >= pd.Timestamp(start), "adj_close"]

    inv = simulate_investment(ticker_prices, amount)
    bench_inv = simulate_investment(bench_prices, amount)

    start_date = ticker_prices.index[0].date()
    end_date = ticker_prices.index[-1].date()

    benchmark_result = BenchmarkResult(
        ticker=benchmark,
        end_value=bench_inv.end_value,
        total_return_pct=bench_inv.total_return_pct,
        path=_to_points(bench_inv.path),
    )

    return TimeMachineResult(
        ticker=ticker,
        name=display_name(ticker),
        start_date=start_date,
        end_date=end_date,
        amount=round(amount, 2),
        shares=inv.shares,
        start_price=inv.start_price,
        end_price=inv.end_price,
        start_value=inv.start_value,
        end_value=inv.end_value,
        total_return_pct=inv.total_return_pct,
        annualized_return_pct=inv.annualized_return_pct,
        max_drawdown=_drawdown_info(inv),
        path=_to_points(inv.path),
        benchmark=benchmark_result,
        outperformance_pct=round(
            inv.total_return_pct - bench_inv.total_return_pct, 2
        ),
    )
