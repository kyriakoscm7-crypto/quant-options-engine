"""Leakage-safe reference probabilities for forecasting research."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BenchmarkForecast:
    """Reference forecast and information available at prediction time."""

    probability_up: float
    observations: int
    forecast_index: int
    horizon_days: int
    latest_training_origin: int | None


def neutral_probability() -> float:
    """Return the constant 50% probability benchmark."""

    return 0.5


def historical_base_rate(
    close_prices: pd.Series,
    forecast_index: int,
    horizon_days: int,
    minimum_samples: int = 30,
    lookback_days: int | None = None,
) -> BenchmarkForecast:
    """Estimate upward-move frequency using matured historical outcomes.

    For a forecast made at index t with horizon h, only labels whose
    origin i satisfies i + h <= t are eligible.

    The forecast therefore never uses prices after index t.

    A rolling lookback, when provided, limits eligible outcome origins
    to the most recent lookback_days origins.

    This benchmark uses a simple empirical frequency without
    smoothing or probability calibration.
    """

    if not isinstance(close_prices, pd.Series):
        raise ValueError("close_prices must be a pandas Series.")

    if isinstance(forecast_index, (bool, np.bool_)) or not isinstance(
        forecast_index, (int, np.integer)
    ):
        raise ValueError("forecast_index must be an integer.")

    if isinstance(horizon_days, (bool, np.bool_)) or not isinstance(
        horizon_days, (int, np.integer)
    ):
        raise ValueError("horizon_days must be an integer.")

    if isinstance(minimum_samples, (bool, np.bool_)) or not isinstance(
        minimum_samples, (int, np.integer)
    ):
        raise ValueError("minimum_samples must be an integer.")

    if horizon_days < 1:
        raise ValueError("horizon_days must be positive.")

    if minimum_samples < 1:
        raise ValueError("minimum_samples must be positive.")

    if forecast_index < 0 or forecast_index >= len(close_prices):
        raise ValueError("forecast_index is outside the price series.")

    if lookback_days is not None:
        if isinstance(lookback_days, (bool, np.bool_)) or not isinstance(
            lookback_days, (int, np.integer)
        ):
            raise ValueError("lookback_days must be an integer or None.")

        if lookback_days < 1:
            raise ValueError("lookback_days must be positive.")

    history = close_prices.iloc[: forecast_index + 1]

    if not isinstance(history.index, pd.DatetimeIndex):
        raise ValueError("Prices must use a DatetimeIndex.")

    if history.index.has_duplicates:
        raise ValueError("Duplicate dates are not permitted.")

    if not history.index.is_monotonic_increasing:
        raise ValueError("Dates must be chronological.")

    prices = pd.to_numeric(history, errors="coerce").to_numpy(dtype=float)

    if not np.isfinite(prices).all() or np.any(prices <= 0):
        raise ValueError("Historical prices must be finite and positive.")

    latest_origin = forecast_index - horizon_days

    if latest_origin < 0:
        raise ValueError("Insufficient matured historical outcomes.")

    earliest_origin = 0

    if lookback_days is not None:
        earliest_origin = max(
            0,
            latest_origin - lookback_days + 1,
        )

    origins = np.arange(
        earliest_origin,
        latest_origin + 1,
        dtype=int,
    )

    if len(origins) < minimum_samples:
        raise ValueError(
            "Insufficient matured historical outcomes: "
            f"{len(origins)} available, "
            f"{minimum_samples} required."
        )

    outcomes = (
        prices[origins + horizon_days] > prices[origins]
    )

    probability = float(np.mean(outcomes))

    return BenchmarkForecast(
        probability_up=probability,
        observations=len(outcomes),
        forecast_index=int(forecast_index),
        horizon_days=int(horizon_days),
        latest_training_origin=int(origins[-1]),
    )
