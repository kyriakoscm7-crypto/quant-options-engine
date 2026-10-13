"""Historical-frequency probability benchmark.

Each prediction uses only outcomes that were fully observable
at the time the forecast was made.
"""

import numpy as np
import pandas as pd


def historical_up_probability(
    close_prices: pd.Series,
    forecast_index: int,
    horizon: int,
    minimum_samples: int = 30,
) -> float:
    """Estimate the historical frequency of positive horizon returns."""

    prices = pd.to_numeric(close_prices, errors="coerce")

    if horizon < 1:
        raise ValueError("Horizon must be positive.")

    if minimum_samples < 1:
        raise ValueError("minimum_samples must be positive.")

    if forecast_index < 0 or forecast_index >= len(prices):
        raise ValueError("Invalid forecast index.")

    if (
        prices.isna().any()
        or not np.isfinite(prices.to_numpy()).all()
        or (prices <= 0).any()
    ):
        raise ValueError("Prices must be finite and positive.")

    # A historical observation starting at index i is eligible
    # only when its outcome at i + horizon is already known.
    eligible_end = forecast_index - horizon

    if eligible_end < 0:
        raise ValueError("Insufficient historical outcomes.")

    past_returns = (
        prices.iloc[horizon : forecast_index + 1].to_numpy()
        / prices.iloc[: eligible_end + 1].to_numpy()
        - 1.0
    )

    if len(past_returns) < minimum_samples:
        raise ValueError("Insufficient historical outcomes.")

    return float(np.mean(past_returns > 0))
