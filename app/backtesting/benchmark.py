"""Benchmark portfolio simulation for historical strategy comparisons."""

from __future__ import annotations

import pandas as pd


def simulate_buy_and_hold(
    benchmark: pd.DataFrame,
    execution_date: pd.Timestamp,
    end_date: pd.Timestamp,
    initial_capital: float = 10_000.0,
    transaction_cost: float = 0.001,
) -> pd.Series:
    """Buy at the execution-session open and mark to subsequent closes."""

    if initial_capital <= 0:
        raise ValueError("Initial capital must be positive.")

    if not 0 <= transaction_cost < 1:
        raise ValueError("Transaction cost must be between 0 and 1.")

    if not {"Open", "Close"}.issubset(benchmark.columns):
        raise ValueError("Benchmark must contain Open and Close columns.")

    benchmark = benchmark.sort_index()

    execution_date = pd.Timestamp(execution_date)
    end_date = pd.Timestamp(end_date)

    if execution_date not in benchmark.index:
        raise ValueError("Execution date is missing from benchmark.")

    if end_date < execution_date:
        raise ValueError("End date cannot precede execution date.")

    purchase_price = float(benchmark.loc[execution_date, "Open"])

    if purchase_price <= 0:
        raise ValueError("Benchmark opening price must be positive.")

    shares = initial_capital / (
        purchase_price * (1.0 + transaction_cost)
    )

    prices = benchmark.loc[
        (benchmark.index >= execution_date)
        & (benchmark.index <= end_date),
        "Close",
    ].astype(float)

    if prices.empty:
        raise ValueError("No benchmark observations in evaluation period.")

    if prices.isna().any() or (prices <= 0).any():
        raise ValueError("Benchmark closing prices must be positive.")

    values = shares * prices
    values.name = "Benchmark Value"

    return values
