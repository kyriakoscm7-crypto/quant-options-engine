"""Leakage-aware market features for quantitative forecasting.

All features use prices available at or before the prediction date.
No future returns are used in feature construction.
"""

import numpy as np
import pandas as pd

FEATURE_COLUMNS = (
    "momentum_5d",
    "momentum_20d",
    "momentum_60d",
    "reversal_1d",
    "volatility_20d",
    "volatility_60d",
    "volatility_ratio",
    "trend_50d",
    "trend_200d",
)


def build_market_features(close_prices: pd.Series) -> pd.DataFrame:
    """Build historical price-based features without future leakage."""

    if not isinstance(close_prices, pd.Series):
        raise ValueError("close_prices must be a pandas Series.")

    if len(close_prices) < 201:
        raise ValueError("At least 201 closing prices are required.")

    try:
        close = close_prices.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Closing prices must be numeric.") from exc

    if not np.isfinite(close.to_numpy()).all():
        raise ValueError("Closing prices must be finite.")

    if (close <= 0).any():
        raise ValueError("Closing prices must be positive.")

    if close.index.has_duplicates:
        raise ValueError("Closing price index must not contain duplicates.")

    log_prices = np.log(close)
    returns = log_prices.diff()

    features = pd.DataFrame(index=close.index)

    features["momentum_5d"] = log_prices.diff(5)
    features["momentum_20d"] = log_prices.diff(20)
    features["momentum_60d"] = log_prices.diff(60)

    features["reversal_1d"] = -returns

    features["volatility_20d"] = returns.rolling(
        20,
        min_periods=20,
    ).std()

    features["volatility_60d"] = returns.rolling(
        60,
        min_periods=60,
    ).std()

    features["volatility_ratio"] = (
        features["volatility_20d"]
        / features["volatility_60d"].replace(0, np.nan)
    )

    moving_average_50 = close.rolling(
        50,
        min_periods=50,
    ).mean()

    moving_average_200 = close.rolling(
        200,
        min_periods=200,
    ).mean()

    features["trend_50d"] = close / moving_average_50 - 1.0
    features["trend_200d"] = close / moving_average_200 - 1.0

    return features.replace([np.inf, -np.inf], np.nan)


def build_forward_labels(
    close_prices: pd.Series,
    horizon_days: int,
) -> pd.Series:
    """Create future direction labels for historical model training.

    Labels at date t are only known after t + horizon_days.
    Walk-forward training must exclude labels that have not matured.
    """

    if (
        isinstance(horizon_days, bool)
        or not isinstance(horizon_days, int)
        or horizon_days < 1
    ):
        raise ValueError("horizon_days must be a positive integer.")

    if not isinstance(close_prices, pd.Series):
        raise ValueError("close_prices must be a pandas Series.")

    if close_prices.empty:
        raise ValueError("close_prices must not be empty.")

    try:
        close = close_prices.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("Closing prices must be numeric.") from exc

    if not np.isfinite(close.to_numpy()).all() or (close <= 0).any():
        raise ValueError("Closing prices must be positive and finite.")

    forward_return = close.shift(-horizon_days) / close - 1.0

    labels = (forward_return > 0).astype(float)

    labels[forward_return.isna()] = np.nan

    return labels.rename("actual_up")
