"""Reproducible historical-window sampling for robustness research."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TestWindow:
    __test__ = False

    start: pd.Timestamp
    end: pd.Timestamp


def generate_random_windows(
    trading_dates: pd.DatetimeIndex,
    window_days: int = 252,
    number_of_windows: int = 20,
    seed: int = 42,
) -> list[TestWindow]:
    """Sample reproducible contiguous windows from a trading calendar.

    Windows may overlap and must not be interpreted as independent tests.
    """
    if window_days < 2:
        raise ValueError("window_days must be at least 2.")

    if number_of_windows < 1:
        raise ValueError("number_of_windows must be positive.")

    dates = pd.DatetimeIndex(trading_dates).sort_values().unique()

    if dates.hasnans:
        raise ValueError("Trading dates cannot contain NaT.")

    if len(dates) < window_days:
        raise ValueError("Not enough trading dates for requested window.")

    possible_starts = len(dates) - window_days + 1

    if number_of_windows > possible_starts:
        raise ValueError(
            "Requested more unique windows than available starting dates."
        )

    rng = np.random.default_rng(seed)

    starts = rng.choice(
        possible_starts,
        size=number_of_windows,
        replace=False,
    )

    return [
        TestWindow(
            start=pd.Timestamp(dates[int(i)]),
            end=pd.Timestamp(dates[int(i) + window_days - 1]),
        )
        for i in starts
    ]


def summarize_window_returns(
    portfolio_values: pd.Series,
    benchmark_values: pd.Series,
    windows: list[TestWindow],
) -> pd.DataFrame:
    """Compare compounded strategy and benchmark returns within each window.

    Uses the value at the first window close as the starting reference.
    Consequently, these are close-to-close window returns, not fresh-entry
    backtests with a new initial investment at each window's opening.
    """
    portfolio = pd.to_numeric(
        portfolio_values, errors="raise"
    ).sort_index()

    benchmark = pd.to_numeric(
        benchmark_values, errors="raise"
    ).sort_index()

    if not isinstance(portfolio.index, pd.DatetimeIndex):
        raise ValueError("Portfolio must have a DatetimeIndex.")

    if not isinstance(benchmark.index, pd.DatetimeIndex):
        raise ValueError("Benchmark must have a DatetimeIndex.")

    if portfolio.index.has_duplicates or benchmark.index.has_duplicates:
        raise ValueError("Duplicate valuation dates are not allowed.")

    common_dates = portfolio.index.intersection(benchmark.index)

    portfolio = portfolio.loc[common_dates]
    benchmark = benchmark.loc[common_dates]

    if (
        portfolio.empty
        or portfolio.isna().any()
        or benchmark.isna().any()
        or (portfolio <= 0).any()
        or (benchmark <= 0).any()
    ):
        raise ValueError("Portfolio and benchmark values must be positive.")

    records = []

    for window in windows:
        dates = common_dates[
            (common_dates >= window.start)
            & (common_dates <= window.end)
        ]

        if len(dates) < 2:
            raise ValueError("Window contains fewer than two shared dates.")

        start = dates[0]
        end = dates[-1]

        strategy_return = (
            float(portfolio.loc[end]) / float(portfolio.loc[start]) - 1
        )

        benchmark_return = (
            float(benchmark.loc[end]) / float(benchmark.loc[start]) - 1
        )

        records.append(
            {
                "Start": start,
                "End": end,
                "Trading Days": len(dates),
                "Strategy Return (%)": strategy_return * 100,
                "SPY Return (%)": benchmark_return * 100,
                "Excess Return (pp)": (
                    strategy_return - benchmark_return
                ) * 100,
                "Beat SPY": strategy_return > benchmark_return,
            }
        )

    return pd.DataFrame(records)
