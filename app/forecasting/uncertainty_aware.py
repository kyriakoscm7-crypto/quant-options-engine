"""Research-only uncertainty-aware probability forecasting."""

from dataclasses import dataclass
from math import erf, sqrt

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class UncertaintyAwareForecast:
    horizon_days: int
    probability_up: float
    expected_return_pct: float
    predictive_volatility_pct: float
    observations: int


def uncertainty_aware_forecast(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    lookback: int = 252,
    minimum_observations: int = 120,
) -> list[UncertaintyAwareForecast]:
    """Forecast positive-return probabilities with mean-estimation uncertainty."""

    if not isinstance(close_prices, pd.Series):
        raise ValueError("close_prices must be a pandas Series.")

    prices = close_prices.to_numpy(dtype=float)

    if (
        len(prices) < 2
        or not np.all(np.isfinite(prices))
        or np.any(prices <= 0)
    ):
        raise ValueError("Prices must be finite, positive, and sufficient.")

    if not isinstance(lookback, int) or isinstance(lookback, bool) or lookback < 2:
        raise ValueError("lookback must be an integer of at least 2.")

    if (
        not isinstance(minimum_observations, int)
        or isinstance(minimum_observations, bool)
        or minimum_observations < 2
    ):
        raise ValueError("minimum_observations must be at least 2.")

    if not horizons or any(
        not isinstance(h, int) or isinstance(h, bool) or h <= 0
        for h in horizons
    ):
        raise ValueError("Horizons must be positive integers.")

    returns = np.diff(np.log(prices))[-lookback:]

    n = len(returns)

    if n < minimum_observations:
        raise ValueError("Insufficient historical observations.")

    mean_return = float(np.mean(returns))
    daily_volatility = float(np.std(returns, ddof=1))

    forecasts = []

    for horizon in horizons:
        expected_log_return = mean_return * horizon

        predictive_variance = daily_volatility**2 * (
            horizon + horizon**2 / n
        )

        predictive_std = sqrt(predictive_variance)

        if predictive_std == 0:
            if expected_log_return > 0:
                probability = 1.0
            elif expected_log_return < 0:
                probability = 0.0
            else:
                probability = 0.5
        else:
            z_score = expected_log_return / predictive_std
            probability = 0.5 * (1.0 + erf(z_score / sqrt(2.0)))

        expected_simple_return = (
            np.exp(expected_log_return + predictive_variance / 2.0) - 1.0
        ) * 100.0

        forecasts.append(
            UncertaintyAwareForecast(
                horizon_days=horizon,
                probability_up=float(probability),
                expected_return_pct=float(expected_simple_return),
                predictive_volatility_pct=float(predictive_std * 100.0),
                observations=n,
            )
        )

    return forecasts
