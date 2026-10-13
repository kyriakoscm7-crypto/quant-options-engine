"""Historical market data acquisition and quality validation."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass(frozen=True)
class ResearchDataResult:
    ticker: str
    close: pd.Series | None
    status: str
    observations: int
    start_date: str | None
    end_date: str | None
    missing_prices: int
    duplicate_dates: int
    invalid_prices: int
    error: str | None


def validate_close_prices(
    ticker: str,
    close: pd.Series,
    minimum_observations: int = 1000,
) -> ResearchDataResult:
    """Validate adjusted daily closing prices without filling missing data."""

    if minimum_observations < 1:
        raise ValueError("minimum_observations must be positive.")

    if not isinstance(close, pd.Series):
        raise ValueError("close must be a pandas Series.")

    prices = close.copy()

    duplicate_dates = int(prices.index.duplicated().sum())
    missing_prices = int(prices.isna().sum())

    numeric = pd.to_numeric(prices, errors="coerce")
    values = numeric.to_numpy(dtype=float)

    invalid_prices = int(
        np.sum(~np.isfinite(values) & ~pd.isna(prices).to_numpy())
        + np.sum(np.isfinite(values) & (values <= 0))
    )

    if duplicate_dates:
        status = "Rejected: duplicate dates"
    elif missing_prices:
        status = "Rejected: missing prices"
    elif invalid_prices:
        status = "Rejected: invalid prices"
    elif not isinstance(prices.index, pd.DatetimeIndex):
        status = "Rejected: invalid date index"
    elif not prices.index.is_monotonic_increasing:
        status = "Rejected: dates not chronological"
    elif len(prices) < minimum_observations:
        status = "Rejected: insufficient history"
    else:
        status = "Valid"

    start_date = (
        str(prices.index.min().date())
        if len(prices) and isinstance(prices.index, pd.DatetimeIndex)
        else None
    )

    end_date = (
        str(prices.index.max().date())
        if len(prices) and isinstance(prices.index, pd.DatetimeIndex)
        else None
    )

    return ResearchDataResult(
        ticker=ticker,
        close=prices if status == "Valid" else None,
        status=status,
        observations=len(prices),
        start_date=start_date,
        end_date=end_date,
        missing_prices=missing_prices,
        duplicate_dates=duplicate_dates,
        invalid_prices=invalid_prices,
        error=None,
    )


def download_research_prices(
    ticker: str,
    years: int = 15,
    minimum_observations: int = 1000,
) -> ResearchDataResult:
    """Download and validate adjusted daily closing prices."""

    if years < 1:
        raise ValueError("years must be positive.")

    if not ticker or not isinstance(ticker, str):
        raise ValueError("ticker must be a nonempty string.")

    try:
        data = yf.download(
            ticker,
            period=f"{years}y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if data.empty:
            raise ValueError("No historical data returned.")

        close = data["Close"]

        if isinstance(close, pd.DataFrame):
            if close.shape[1] != 1:
                raise ValueError("Expected exactly one closing-price column.")
            close = close.iloc[:, 0]

        result = validate_close_prices(
            ticker=ticker,
            close=close,
            minimum_observations=minimum_observations,
        )

        return result

    except Exception as exc:
        return ResearchDataResult(
            ticker=ticker,
            close=None,
            status="Download failed",
            observations=0,
            start_date=None,
            end_date=None,
            missing_prices=0,
            duplicate_dates=0,
            invalid_prices=0,
            error=f"{type(exc).__name__}: {exc}",
        )
