"""
Multi-stock market scanner for Quant Intelligence.

This module:
- Downloads historical stock prices.
- Calculates historical momentum.
- Measures volatility and maximum drawdown.
- Compares performance against SPY.
- Produces structured results for dashboards and research.

Important:
    Historical performance is not a forecast.
    Scanner results are descriptive, not investment recommendations.
"""

from collections.abc import Iterable

import numpy as np
import pandas as pd

from app.market_data.stock_history import (
    calculate_stock_statistics,
    fetch_stock_history,
    validate_ticker,
)

# Approximate number of trading sessions in each lookback window.
ONE_MONTH_TRADING_DAYS = 21
THREE_MONTH_TRADING_DAYS = 63

# Limit the number of symbols in one scan to avoid excessive
# requests to the market-data provider.
MAX_SCAN_TICKERS = 20

DEFAULT_BENCHMARK = "SPY"


def normalize_tickers(
    tickers: str | Iterable[str],
) -> list[str]:
    """
    Validate, uppercase, and deduplicate ticker symbols.

    Accepts:
        "AAPL, MSFT, NVDA"
        ["AAPL", "MSFT", "NVDA"]

    Preserves the original ticker order.
    """

    if isinstance(tickers, str):
        candidates = tickers.split(",")

    else:
        try:
            candidates = list(tickers)

        except TypeError as exc:
            raise ValueError(
                "Tickers must be a comma-separated string "
                "or an iterable of ticker strings."
            ) from exc

    if not candidates:
        raise ValueError(
            "Provide at least one ticker symbol."
        )

    normalized = []
    seen = set()

    for candidate in candidates:
        symbol = validate_ticker(candidate)

        if symbol not in seen:
            normalized.append(symbol)
            seen.add(symbol)

    if len(normalized) > MAX_SCAN_TICKERS:
        raise ValueError(
            f"A scan supports at most {MAX_SCAN_TICKERS} "
            "unique ticker symbols."
        )

    return normalized


def calculate_momentum(
    history: pd.DataFrame,
    trading_days: int,
) -> float | None:
    """
    Calculate historical momentum over a fixed trading-day window.

    Formula:
        (latest_close / close_N_sessions_ago - 1) * 100

    For a 21-session lookback, at least 22 prices are required.

    Returns None when insufficient valid observations exist.
    """

    if not isinstance(history, pd.DataFrame):
        raise ValueError(
            "History must be a pandas DataFrame."
        )

    if "Close" not in history.columns:
        raise ValueError(
            "History must contain a Close column."
        )

    if (
        isinstance(trading_days, bool)
        or not isinstance(trading_days, int)
        or trading_days < 1
    ):
        raise ValueError(
            "Trading days must be a positive integer."
        )

    prices = pd.to_numeric(
        history["Close"],
        errors="coerce",
    )

    prices = prices.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    prices = prices[
        prices > 0
    ]

    if len(prices) <= trading_days:
        return None

    latest_price = float(
        prices.iloc[-1]
    )

    earlier_price = float(
        prices.iloc[-(trading_days + 1)]
    )

    momentum_pct = (
        latest_price / earlier_price - 1.0
    ) * 100.0

    return round(
        momentum_pct,
        4,
    )


def calculate_relative_performance(
    stock_history: pd.DataFrame,
    benchmark_history: pd.DataFrame,
) -> float | None:
    """
    Calculate stock performance relative to a benchmark.

    Both assets are compared using their first and last
    shared trading dates.

    Formula:
        stock_return_pct - benchmark_return_pct

    Returns None when fewer than two common dates exist.

    This is historical excess return in percentage points,
    not statistical alpha or a future-return forecast.
    """

    required_columns = {
        "Date",
        "Close",
    }

    for history in (
        stock_history,
        benchmark_history,
    ):
        if not isinstance(history, pd.DataFrame):
            raise ValueError(
                "History must be a pandas DataFrame."
            )

        if not required_columns.issubset(
            history.columns
        ):
            raise ValueError(
                "History must contain Date and Close columns."
            )

    stock = stock_history[
        ["Date", "Close"]
    ].copy()

    benchmark = benchmark_history[
        ["Date", "Close"]
    ].copy()

    stock["Date"] = pd.to_datetime(
        stock["Date"],
        utc=True,
        errors="coerce",
    ).dt.date

    benchmark["Date"] = pd.to_datetime(
        benchmark["Date"],
        utc=True,
        errors="coerce",
    ).dt.date

    for frame in (
        stock,
        benchmark,
    ):
        frame["Close"] = pd.to_numeric(
            frame["Close"],
            errors="coerce",
        )

        frame.replace(
            [np.inf, -np.inf],
            np.nan,
            inplace=True,
        )

        frame.dropna(
            subset=["Date", "Close"],
            inplace=True,
        )

        frame.drop(
            frame[
                frame["Close"] <= 0
            ].index,
            inplace=True,
        )

        frame.sort_values(
            "Date",
            inplace=True,
        )

        frame.drop_duplicates(
            subset=["Date"],
            keep="last",
            inplace=True,
        )

    stock = stock.rename(
        columns={"Close": "Stock"}
    )

    benchmark = benchmark.rename(
        columns={"Close": "Benchmark"}
    )

    aligned = pd.merge(
        stock,
        benchmark,
        on="Date",
        how="inner",
    )

    aligned = aligned.sort_values(
        "Date"
    ).reset_index(drop=True)

    if len(aligned) < 2:
        return None

    stock_return_pct = (
        aligned["Stock"].iloc[-1]
        / aligned["Stock"].iloc[0]
        - 1.0
    ) * 100.0

    benchmark_return_pct = (
        aligned["Benchmark"].iloc[-1]
        / aligned["Benchmark"].iloc[0]
        - 1.0
    ) * 100.0

    return round(
        float(
            stock_return_pct
            - benchmark_return_pct
        ),
        4,
    )


def scan_market(
    tickers: str | Iterable[str],
    period: str = "1y",
    benchmark: str = DEFAULT_BENCHMARK,
) -> pd.DataFrame:
    """
    Scan multiple stocks and calculate historical metrics.

    Each ticker is processed independently.

    If one ticker fails, its row contains an error message
    while the remaining tickers continue processing.

    Benchmark data is downloaded once per scan.

    Returns:
        A pandas DataFrame with one row per requested ticker.

    Notes:
        - Momentum uses trading-session counts, not calendar months.
        - Volatility is annualized historical daily-return volatility.
        - Relative performance uses common benchmark dates.
        - Missing metrics are represented by None.
    """

    symbols = normalize_tickers(
        tickers
    )

    benchmark_symbol = validate_ticker(
        benchmark
    )

    # Download benchmark data only once.
    benchmark_history = None
    benchmark_error = None

    try:
        benchmark_history = fetch_stock_history(
            benchmark_symbol,
            period,
        )

    except (ValueError, RuntimeError) as exc:
        benchmark_error = str(exc)

    results = []

    for symbol in symbols:
        row = {
            "Ticker": symbol,
            "Latest Close": None,
            "Total Return (%)": None,
            "1M Momentum (%)": None,
            "3M Momentum (%)": None,
            "Annualized Volatility (%)": None,
            "Maximum Drawdown (%)": None,
            "Relative to SPY (%)": None,
            "Trading Days": None,
            "Status": "OK",
        }

        try:
            # Reuse benchmark history if the benchmark itself
            # appears in the requested stock list.
            if (
                symbol == benchmark_symbol
                and benchmark_history is not None
            ):
                history = benchmark_history

            else:
                history = fetch_stock_history(
                    symbol,
                    period,
                )

            statistics = calculate_stock_statistics(
                history
            )

            row["Latest Close"] = statistics[
                "latest_close"
            ]

            row["Total Return (%)"] = statistics[
                "total_return_pct"
            ]

            row["1M Momentum (%)"] = calculate_momentum(
                history,
                ONE_MONTH_TRADING_DAYS,
            )

            row["3M Momentum (%)"] = calculate_momentum(
                history,
                THREE_MONTH_TRADING_DAYS,
            )

            row["Annualized Volatility (%)"] = statistics[
                "annualized_volatility_pct"
            ]

            row["Maximum Drawdown (%)"] = statistics[
                "maximum_drawdown_pct"
            ]

            row["Trading Days"] = statistics[
                "trading_days"
            ]

            if benchmark_history is not None:
                row["Relative to SPY (%)"] = (
                    calculate_relative_performance(
                        history,
                        benchmark_history,
                    )
                )

            else:
                row["Status"] = (
                    "OK (benchmark unavailable: "
                    f"{benchmark_error})"
                )

        except (ValueError, RuntimeError) as exc:
            row["Status"] = (
                f"ERROR: {exc}"
            )

        results.append(
            row
        )

    return pd.DataFrame(
        results
    )