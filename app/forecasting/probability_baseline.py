"""Research-only probabilistic forecasting baseline.

Estimates directional probabilities using a fitted normal distribution
of historical daily log returns. Predictions are NOT calibrated or
validated trading signals.
"""

from dataclasses import dataclass
from math import erf, sqrt

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ProbabilityForecast:
    horizon_days: int
    probability_up: float
    expected_return_pct: float
    volatility_pct: float
    observations: int


def forecast_probabilities(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    lookback: int = 252,
    minimum_observations: int = 120,
) -> list[ProbabilityForecast]:
    """Estimate return probabilities from historical daily closes.

    Assumes independent, normally distributed daily log returns.
    The assumption is a baseline, not a claim about real markets.
    """
    if lookback < minimum_observations or minimum_observations < 2:
        raise ValueError("Invalid lookback or minimum observations.")

    if not horizons or any(
        not isinstance(h, int) or isinstance(h, bool) or h <= 0
        for h in horizons
    ):
        raise ValueError("Horizons must be positive integers.")

    prices = pd.to_numeric(close_prices, errors="coerce")

    if prices.isna().any() or not np.isfinite(prices.to_numpy()).all():
        raise ValueError("Prices must be finite.")

    if (prices <= 0).any():
        raise ValueError("Prices must be positive.")

    if len(prices) < minimum_observations + 1:
        raise ValueError("Insufficient price history.")

    returns = np.log(prices / prices.shift(1)).dropna().iloc[-lookback:]

    if len(returns) < minimum_observations:
        raise ValueError("Insufficient return observations.")

    mean_daily = float(returns.mean())
    std_daily = float(returns.std(ddof=1))

    if not np.isfinite(mean_daily) or not np.isfinite(std_daily):
        raise ValueError("Invalid return statistics.")

    forecasts = []

    for horizon in horizons:
        mean_h = mean_daily * horizon
        std_h = std_daily * sqrt(horizon)

        if std_h == 0:
            probability_up = 1.0 if mean_h > 0 else 0.0
        else:
            z = mean_h / std_h
            probability_up = 0.5 * (1.0 + erf(z / sqrt(2.0)))

        expected_return = (
            np.exp(mean_h + 0.5 * std_h**2) - 1.0
        ) * 100.0

        forecasts.append(
            ProbabilityForecast(
                horizon_days=horizon,
                probability_up=float(probability_up),
                expected_return_pct=float(expected_return),
                volatility_pct=float(std_h * 100.0),
                observations=len(returns),
            )
        )

    return forecasts
