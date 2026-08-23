# ✦ @chiranr19 · © 2026 All Rights Reserved · proprietary · sigil:5FENNYU3G7KNXVL7
"""Pure simulation math for the Time Machine.

Everything here is deliberately free of network or database access so it can be
unit-tested with hand-computed fixtures (see ``tests/test_simulation.py``).
Functions take plain pandas Series / numpy arrays and return plain dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

_TRADING_DAYS_PER_YEAR = 365.25  # calendar basis for annualization


@dataclass(frozen=True)
class Drawdown:
    """The worst peak-to-trough decline along a value path."""

    peak_idx: int
    trough_idx: int
    peak_value: float
    trough_value: float
    drawdown_pct: float  # signed, e.g. -34.2


@dataclass(frozen=True)
class Investment:
    """Result of putting ``amount`` into an asset at the first price."""

    shares: float
    start_price: float
    end_price: float
    start_value: float
    end_value: float
    total_return_pct: float
    annualized_return_pct: float | None
    path: pd.Series  # value over time, indexed like the input prices
    max_drawdown: Drawdown


def max_drawdown(values: "pd.Series | np.ndarray | list[float]") -> Drawdown:
    """Largest drawdown of a value series.

    The drawdown at time *t* is ``value[t] / running_max[t] - 1``. We report the
    deepest one — this is "the dip that would've scared you out".
    """
    arr = np.asarray(values, dtype=float)
    if arr.size == 0:
        raise ValueError("Cannot compute drawdown of an empty series.")

    running_max = np.maximum.accumulate(arr)
    drawdowns = arr / running_max - 1.0
    trough_idx = int(np.argmin(drawdowns))
    # The peak is the highest value at or before the trough.
    peak_idx = int(np.argmax(arr[: trough_idx + 1]))

    return Drawdown(
        peak_idx=peak_idx,
        trough_idx=trough_idx,
        peak_value=float(arr[peak_idx]),
        trough_value=float(arr[trough_idx]),
        drawdown_pct=round(float(drawdowns[trough_idx]) * 100.0, 4),
    )


def simulate_investment(prices: pd.Series, amount: float) -> Investment:
    """Simulate investing ``amount`` at the first price in ``prices``.

    ``prices`` should be adjusted closes (dividends + splits) indexed by date,
    oldest first. Fractional shares are allowed — this is a learning tool, not a
    brokerage.
    """
    prices = prices.dropna()
    if len(prices) < 2:
        raise ValueError("Need at least two price points to simulate a path.")
    if amount <= 0:
        raise ValueError("Investment amount must be positive.")

    start_price = float(prices.iloc[0])
    end_price = float(prices.iloc[-1])
    shares = amount / start_price
    path = prices * shares

    start_value = amount
    end_value = float(path.iloc[-1])
    total_return_pct = round((end_value / start_value - 1.0) * 100.0, 4)

    days = (prices.index[-1] - prices.index[0]).days
    if days > 0:
        growth = end_value / start_value
        annualized = (growth ** (_TRADING_DAYS_PER_YEAR / days) - 1.0) * 100.0
        annualized_return_pct: float | None = round(annualized, 4)
    else:
        annualized_return_pct = None

    return Investment(
        shares=round(shares, 6),
        start_price=round(start_price, 4),
        end_price=round(end_price, 4),
        start_value=round(start_value, 2),
        end_value=round(end_value, 2),
        total_return_pct=total_return_pct,
        annualized_return_pct=annualized_return_pct,
        path=path,
        max_drawdown=max_drawdown(path.to_numpy()),
    )
