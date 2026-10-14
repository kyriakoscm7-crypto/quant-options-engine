"""
Quant Intelligence — Historical Risk Analytics

Calculates consistent trailing-one-year risk metrics from
daily closing prices.

All annualized statistics use 252 trading days per year.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def _daily_close(history: pd.DataFrame) -> pd.Series:
    """Extract clean daily closing prices indexed by trading date."""

    if history is None or history.empty:
        return pd.Series(dtype=float)

    frame = history.copy()

    if "Date" in frame.columns:
        dates = pd.to_datetime(
            frame["Date"], utc=True, errors="coerce"
        )
    else:
        dates = pd.to_datetime(
            frame.index, utc=True, errors="coerce"
        )

    if "Close" not in frame.columns:
        raise ValueError("Price history must contain Close.")

    closes = pd.to_numeric(
        frame["Close"], errors="coerce"
    )

    series = pd.Series(
        closes.to_numpy(),
        index=pd.DatetimeIndex(dates).normalize(),
        dtype=float,
    )

    series = series.replace(
        [np.inf, -np.inf], np.nan
    ).dropna()

    series = series[series > 0]

    # Use the last observation for each trading date.
    series = series.groupby(level=0).last()

    return series.sort_index()


def calculate_risk_metrics(
    stock_history: pd.DataFrame,
    benchmark_history: pd.DataFrame,
    risk_free_rate: float = 0.0,
) -> dict:
    """
    Calculate historical risk using daily stock and benchmark data.

    risk_free_rate is an annual decimal rate (0.04 means 4%).
    """

    if not math.isfinite(risk_free_rate) or risk_free_rate <= -1:
        raise ValueError("Invalid annual risk-free rate.")

    stock = _daily_close(stock_history).tail(253)
    benchmark = _daily_close(benchmark_history).tail(253)

    if len(stock) < 30:
        raise ValueError(
            "At least 30 daily stock prices are required."
        )

    stock_returns = stock.pct_change().dropna()

    volatility = None
    sharpe = None
    beta = None
    correlation = None

    if len(stock_returns) >= 20:
        daily_std = float(stock_returns.std(ddof=1))

        if daily_std > 0 and math.isfinite(daily_std):
            volatility = (
                daily_std * math.sqrt(TRADING_DAYS) * 100
            )

            daily_rf = (
                (1 + risk_free_rate) ** (1 / TRADING_DAYS)
                - 1
            )

            sharpe = (
                float(stock_returns.mean()) - daily_rf
            ) / daily_std * math.sqrt(TRADING_DAYS)

    running_peak = stock.cummax()
    drawdowns = stock / running_peak - 1

    maximum_drawdown = float(drawdowns.min() * 100)

    # Align stock and benchmark by actual trading dates.
    aligned_prices = pd.concat(
        [
            stock.rename("stock"),
            benchmark.rename("benchmark"),
        ],
        axis=1,
        join="inner",
    ).dropna()

    # Calculate returns AFTER aligning dates.
    # This avoids comparing returns over mismatched intervals.
    aligned_returns = aligned_prices.pct_change().dropna()

    if len(aligned_returns) >= 20:
        benchmark_variance = float(
            aligned_returns["benchmark"].var(ddof=1)
        )

        stock_variance = float(
            aligned_returns["stock"].var(ddof=1)
        )

        if benchmark_variance > 0:
            covariance = float(
                aligned_returns["stock"].cov(
                    aligned_returns["benchmark"]
                )
            )

            beta = covariance / benchmark_variance

        if stock_variance > 0 and benchmark_variance > 0:
            correlation = float(
                aligned_returns["stock"].corr(
                    aligned_returns["benchmark"]
                )
            )

    return {
        "annualized_volatility_pct": volatility,
        "maximum_drawdown_pct": maximum_drawdown,
        "sharpe_ratio": sharpe,
        "beta_vs_spy": beta,
        "correlation_vs_spy": correlation,
        "daily_observations": len(stock),
        "benchmark_overlap_days": len(aligned_prices),
        "risk_free_rate": risk_free_rate,
        "risk_window": "Trailing 252 trading-day returns",
    }
