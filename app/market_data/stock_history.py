"""
Historical stock-market data and basic quantitative analytics.

This module retrieves historical daily stock prices using yfinance
and calculates descriptive statistics for research dashboards.

Important:
    Historical statistics describe past market behavior.
    They are not forecasts or investment recommendations.
"""

import math
import re

import numpy as np
import pandas as pd
import yfinance as yf

# Supported historical periods.
SUPPORTED_PERIODS = {
    "1mo",
    "3mo",
    "6mo",
    "1y",
    "2y",
    "5y",
    "10y",
    "max",
}

# Approximate number of U.S. equity trading days per year.
TRADING_DAYS_PER_YEAR = 252


def validate_ticker(ticker: str) -> str:
    """
    Validate and normalize a stock ticker symbol.

    Examples:
        "aapl" -> "AAPL"
        " spy " -> "SPY"
        "BRK-B" -> "BRK-B"

    Rejects empty or unsupported ticker formats.
    """

    if not isinstance(ticker, str):
        raise ValueError("Ticker must be a string.")

    normalized = ticker.strip().upper()

    if not re.fullmatch(r"[A-Z0-9^][A-Z0-9.^=-]{0,19}", normalized):
        raise ValueError(
            "Invalid ticker symbol. Use a valid stock or ETF ticker."
        )

    return normalized


def fetch_stock_history(
    ticker: str,
    period: str = "1y",
) -> pd.DataFrame:
    """
    Download daily historical stock prices.

    Prices are adjusted for corporate actions using yfinance's
    auto_adjust=True option.

    Returns a DataFrame with:
        Date
        Open
        High
        Low
        Close
        Volume

    Notes:
        - Close is adjusted for corporate actions.
        - The latest row may represent an incomplete trading day.
        - Data availability depends on Yahoo Finance.
        - Adjusted historical prices are not necessarily executable
          market prices.
    """

    symbol = validate_ticker(ticker)

    if period not in SUPPORTED_PERIODS:
        raise ValueError(
            f"Unsupported period: {period}. "
            f"Choose from {sorted(SUPPORTED_PERIODS)}."
        )

    try:
        history = yf.Ticker(symbol).history(
            period=period,
            interval="1d",
            auto_adjust=True,
            actions=False,
        )

    except Exception as exc:
        raise RuntimeError(
            f"Unable to retrieve historical data for {symbol}."
        ) from exc

    if history.empty:
        raise RuntimeError(
            f"No historical stock data available for {symbol}."
        )

    required_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    if not all(column in history.columns for column in required_columns):
        raise RuntimeError(
            "Market data is missing required price columns."
        )

    cleaned = history[required_columns].copy()

    cleaned = cleaned.replace(
        [np.inf, -np.inf],
        np.nan,
    )

    cleaned = cleaned.dropna(
        subset=["Open", "High", "Low", "Close"],
    )

    cleaned = cleaned[
        (cleaned["Open"] > 0)
        & (cleaned["High"] > 0)
        & (cleaned["Low"] > 0)
        & (cleaned["Close"] > 0)
    ]

    if cleaned.empty:
        raise RuntimeError(
            "No valid historical price observations were found."
        )

    cleaned = cleaned.sort_index()

    cleaned = cleaned.reset_index()

    # Yahoo Finance normally labels the index "Date".
    # Normalize the first column regardless of its original name.
    cleaned = cleaned.rename(
        columns={cleaned.columns[0]: "Date"}
    )

    cleaned["Date"] = pd.to_datetime(
        cleaned["Date"],
        utc=True,
    )

    cleaned["Volume"] = pd.to_numeric(
        cleaned["Volume"],
        errors="coerce",
    ).fillna(0)

    cleaned["Ticker"] = symbol

    return cleaned[
        [
            "Date",
            "Ticker",
            "Open",
            "High",
            "Low",
            "Close",
            "Volume",
        ]
    ].reset_index(drop=True)


def calculate_stock_statistics(
    history: pd.DataFrame,
) -> dict:
    """
    Calculate descriptive statistics from historical prices.

    Returns:
        latest_close
        previous_close
        latest_change_pct
        total_return_pct
        annualized_volatility_pct
        maximum_drawdown_pct
        trading_days

    Important:
        Returns and volatility are historical observations,
        not predictions of future performance.
    """

    if not isinstance(history, pd.DataFrame):
        raise ValueError("History must be a pandas DataFrame.")

    if "Close" not in history.columns:
        raise ValueError("History must contain a Close column.")

    prices = pd.to_numeric(
        history["Close"],
        errors="coerce",
    )

    prices = prices.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    prices = prices[prices > 0]

    if prices.empty:
        raise ValueError(
            "History must contain at least one valid closing price."
        )

    latest_close = float(prices.iloc[-1])

    previous_close = (
        float(prices.iloc[-2])
        if len(prices) >= 2
        else None
    )

    latest_change_pct = (
        (latest_close / previous_close - 1.0) * 100.0
        if previous_close is not None
        else None
    )

    first_close = float(prices.iloc[0])

    total_return_pct = (
        latest_close / first_close - 1.0
    ) * 100.0

    daily_returns = prices.pct_change().dropna()

    annualized_volatility_pct = (
        float(
            daily_returns.std(ddof=1)
            * math.sqrt(TRADING_DAYS_PER_YEAR)
            * 100.0
        )
        if len(daily_returns) >= 2
        else None
    )

    running_peak = prices.cummax()

    drawdowns = (
        prices / running_peak - 1.0
    ) * 100.0

    maximum_drawdown_pct = float(
        drawdowns.min()
    )

    return {
        "latest_close": round(latest_close, 4),
        "previous_close": (
            round(previous_close, 4)
            if previous_close is not None
            else None
        ),
        "latest_change_pct": (
            round(latest_change_pct, 4)
            if latest_change_pct is not None
            else None
        ),
        "total_return_pct": round(
            total_return_pct, 4
        ),
        "annualized_volatility_pct": (
            round(annualized_volatility_pct, 4)
            if annualized_volatility_pct is not None
            else None
        ),
        "maximum_drawdown_pct": round(
            maximum_drawdown_pct, 4
        ),
        "trading_days": int(len(prices)),
    }


def calculate_normalized_performance(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """
    Normalize a stock's historical closing prices to 100.

    This allows multiple assets to be compared on the same chart.

    Example:
        First observation: 100
        Final observation: 115

    Represents a 15% increase in adjusted closing prices.
    """

    if not {"Date", "Close"}.issubset(history.columns):
        raise ValueError(
            "History must contain Date and Close columns."
        )

    result = history[
        ["Date", "Close"]
    ].copy()

    result["Close"] = pd.to_numeric(
        result["Close"],
        errors="coerce",
    )

    result = result.replace(
        [np.inf, -np.inf],
        np.nan,
    ).dropna()

    result = result[
        result["Close"] > 0
    ]

    if result.empty:
        raise ValueError(
            "No valid closing prices available."
        )

    initial_price = float(
        result["Close"].iloc[0]
    )

    result["Normalized"] = (
        result["Close"]
        / initial_price
        * 100.0
    )

    return result[
        ["Date", "Normalized"]
    ].reset_index(drop=True)