"""Pure technical-analysis math.

No network or DB access — everything takes pandas objects and returns plain
values / dataclasses, so it unit-tests with hand-built fixtures. Prices in are
expected daily and ascending by date.

Convention:
  * **raw close** for prices, affordability, gaps, and daily change (what you'd
    actually pay per share).
  * **adjusted close** for return/volatility math (includes dividends + splits).
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .simulation import max_drawdown

# Approximate trading-day offsets for lookback returns.
_TD_1M = 21
_TD_3M = 63
_TD_1Y = 252


@dataclass(frozen=True)
class StockMetrics:
    ticker: str
    price: float
    prev_close: float
    change_pct: float
    open: float
    gap_pct: float
    ma50: float | None
    ma200: float | None
    above_ma50: bool
    above_ma200: bool
    rsi14: float | None
    rsi_signal: str | None  # 'overbought' | 'oversold' | None
    vol_90d: float | None  # annualized %
    ret_1m: float | None
    ret_3m: float | None
    ret_1y: float | None
    high_52w: float
    low_52w: float
    range_52w_position: float
    avg_dollar_volume_20d: float
    volume: int
    avg_volume_30d: float
    volume_ratio: float
    max_drawdown_1y: float
    is_new_high_52w: bool
    is_new_low_52w: bool
    cross: str | None  # 'golden' | 'death' | None (recent only)
    cross_date: dt.date | None
    spark: list[float] = field(default_factory=list)  # last ~30 closes, oldest→newest


# --------------------------------------------------------------------------- #
# Building blocks
# --------------------------------------------------------------------------- #
def moving_average(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=window).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI. Equivalent to an EWM with alpha = 1/period, adjust=False."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss
    out = 100.0 - 100.0 / (1.0 + rs)
    # All-gains window → avg_loss 0 → rs inf → RSI 100 (fillna handles it).
    out = out.where(avg_loss != 0, 100.0)
    return out


def annualized_volatility(adj_close: pd.Series, window: int = 90) -> float | None:
    rets = adj_close.pct_change().dropna().tail(window)
    if len(rets) < 2:
        return None
    return float(rets.std(ddof=1) * np.sqrt(252) * 100.0)


def total_return_pct(adj_close: pd.Series, trading_days: int) -> float | None:
    if len(adj_close) <= trading_days:
        return None
    past = float(adj_close.iloc[-1 - trading_days])
    if past <= 0:
        return None
    return float((adj_close.iloc[-1] / past - 1.0) * 100.0)


def avg_dollar_volume(close: pd.Series, volume: pd.Series, window: int = 20) -> float:
    dollars = (close * volume).tail(window)
    return float(dollars.mean()) if len(dollars) else 0.0


def detect_cross(
    ma_short: pd.Series, ma_long: pd.Series, lookback: int
) -> tuple[str | None, dt.date | None]:
    """Most recent MA50/MA200 crossover, if it happened within ``lookback`` sessions.

    Golden = short crosses above long (bullish); death = short crosses below.
    """
    diff = (ma_short - ma_long).dropna()
    if len(diff) < 2:
        return None, None
    sign = np.sign(diff.to_numpy())
    changes = np.where(np.diff(sign) != 0)[0]
    if len(changes) == 0:
        return None, None
    last = int(changes[-1]) + 1  # index in diff where the new regime starts
    sessions_since = len(diff) - 1 - last
    if sessions_since > lookback:
        return None, None
    kind = "golden" if sign[last] > 0 else "death"
    idx = diff.index[last]
    return kind, (idx.date() if hasattr(idx, "date") else idx)


def normalized_growth(adj_close: pd.Series, base: float = 100.0) -> pd.Series:
    """Rebase a price path to ``base`` at its first point (for comparison charts)."""
    first = float(adj_close.iloc[0])
    return adj_close / first * base


def correlation_matrix(series_by_ticker: dict[str, pd.Series], window: int = 126) -> dict:
    """Pearson correlation of daily returns over the last ``window`` sessions."""
    frames = {}
    for ticker, s in series_by_ticker.items():
        frames[ticker] = s.pct_change()
    df = pd.DataFrame(frames).dropna().tail(window)
    corr = df.corr()
    labels = list(corr.columns)
    matrix = [[round(float(corr.loc[a, b]), 3) for b in labels] for a in labels]
    return {"labels": labels, "matrix": matrix}


def return_histogram(adj_close: pd.Series, bins: int = 21, clip_pct: float = 8.0) -> dict:
    """Distribution of daily % returns, clipped to ±clip_pct for a readable shape."""
    rets = (adj_close.pct_change().dropna() * 100.0).clip(-clip_pct, clip_pct)
    counts, edges = np.histogram(rets, bins=bins, range=(-clip_pct, clip_pct))
    return {
        "counts": [int(c) for c in counts],
        "edges": [round(float(e), 2) for e in edges],
    }


# --------------------------------------------------------------------------- #
# One-shot per-stock metrics
# --------------------------------------------------------------------------- #
def compute_metrics(ticker: str, df: pd.DataFrame) -> StockMetrics | None:
    """Compute the full metric set for one ticker from its OHLCV history.

    Returns None if there isn't enough data to say anything useful.
    """
    df = df.sort_index()
    close = df["close"]
    adj = df["adj_close"]
    volume = df["volume"]
    if len(close) < 2:
        return None

    price = float(close.iloc[-1])
    prev_close = float(close.iloc[-2])
    change_pct = (price / prev_close - 1.0) * 100.0 if prev_close else 0.0
    open_ = float(df["open"].iloc[-1])
    gap_pct = (open_ / prev_close - 1.0) * 100.0 if prev_close else 0.0

    ma50_s = moving_average(close, 50)
    ma200_s = moving_average(close, 200)
    ma50 = float(ma50_s.iloc[-1]) if not np.isnan(ma50_s.iloc[-1]) else None
    ma200 = float(ma200_s.iloc[-1]) if not np.isnan(ma200_s.iloc[-1]) else None

    rsi_s = rsi(adj, 14)
    rsi14 = float(rsi_s.iloc[-1]) if not np.isnan(rsi_s.iloc[-1]) else None
    rsi_signal = None
    if rsi14 is not None:
        rsi_signal = "overbought" if rsi14 >= 70 else "oversold" if rsi14 <= 30 else None

    window_52w = close.tail(_TD_1Y)
    high_52w = float(window_52w.max())
    low_52w = float(window_52w.min())
    span = high_52w - low_52w
    position = (price - low_52w) / span if span > 0 else 0.5
    position = min(1.0, max(0.0, position))

    volume_today = int(volume.iloc[-1])
    prior_vol = volume.iloc[-31:-1]
    avg_volume_30d = float(prior_vol.mean()) if len(prior_vol) else float(volume.mean())
    volume_ratio = volume_today / avg_volume_30d if avg_volume_30d else 1.0

    dd = max_drawdown(adj.tail(_TD_1Y).to_numpy())
    cross, cross_date = detect_cross(ma50_s, ma200_s, lookback=10)

    return StockMetrics(
        ticker=ticker,
        price=round(price, 2),
        prev_close=round(prev_close, 2),
        change_pct=round(change_pct, 2),
        open=round(open_, 2),
        gap_pct=round(gap_pct, 2),
        ma50=round(ma50, 2) if ma50 is not None else None,
        ma200=round(ma200, 2) if ma200 is not None else None,
        above_ma50=ma50 is not None and price > ma50,
        above_ma200=ma200 is not None and price > ma200,
        rsi14=round(rsi14, 1) if rsi14 is not None else None,
        rsi_signal=rsi_signal,
        vol_90d=(
            round(v, 1) if (v := annualized_volatility(adj, 90)) is not None else None
        ),
        ret_1m=(
            round(r, 2) if (r := total_return_pct(adj, _TD_1M)) is not None else None
        ),
        ret_3m=(
            round(r, 2) if (r := total_return_pct(adj, _TD_3M)) is not None else None
        ),
        ret_1y=(
            round(r, 2) if (r := total_return_pct(adj, _TD_1Y)) is not None else None
        ),
        high_52w=round(high_52w, 2),
        low_52w=round(low_52w, 2),
        range_52w_position=round(position, 4),
        avg_dollar_volume_20d=round(avg_dollar_volume(close, volume, 20), 0),
        volume=volume_today,
        avg_volume_30d=round(avg_volume_30d, 0),
        volume_ratio=round(volume_ratio, 2),
        max_drawdown_1y=dd.drawdown_pct,
        is_new_high_52w=position >= 0.995,
        is_new_low_52w=position <= 0.005,
        cross=cross,
        cross_date=cross_date,
        spark=[round(float(x), 2) for x in close.tail(30)],
    )
