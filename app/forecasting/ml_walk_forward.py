"""Chronological walk-forward comparison of ML and historical forecasts."""

import numpy as np
import pandas as pd

from app.forecasting.historical_benchmark import historical_up_probability
from app.forecasting.logistic_forecast import logistic_probability_forecast
from app.forecasting.market_features import FEATURE_COLUMNS
from app.forecasting.research_splits import (
    assign_research_periods,
    create_research_split,
)

COLUMNS = [
    "Forecast Index",
    "Horizon",
    "Research Period",
    "Actual Up",
    "ML Probability",
    "Historical Probability",
]


def ml_walk_forward_predictions(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    training_window: int = 756,
    step: int = 5,
    regularization_c: float = 0.1,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
) -> pd.DataFrame:
    """Generate matched ML and benchmark predictions.

    Only training and validation periods are evaluated.
    The reserved final-test period is excluded.
    """

    if not isinstance(close_prices, pd.Series):
        raise ValueError("close_prices must be a pandas Series.")

    if not horizons or any(
        isinstance(h, bool) or not isinstance(h, int) or h < 1
        for h in horizons
    ):
        raise ValueError("horizons must contain positive integers.")

    if isinstance(step, bool) or not isinstance(step, int) or step < 1:
        raise ValueError("step must be a positive integer.")

    if (
        isinstance(training_window, bool)
        or not isinstance(training_window, int)
        or training_window < 1
    ):
        raise ValueError("training_window must be a positive integer.")

    if len(close_prices) < 500:
        raise ValueError("At least 500 closing prices are required.")

    prices = close_prices.astype(float)

    if not np.isfinite(prices.to_numpy()).all() or (prices <= 0).any():
        raise ValueError("Closing prices must be positive and finite.")

    split = create_research_split(
        len(prices),
        embargo_days=max(horizons),
    )

    development = prices.iloc[:split.validation_end]

    rows = []

    for horizon in horizons:
        for forecast_index in range(
            320 + horizon,
            len(development) - horizon,
            step,
        ):
            try:
                ml = logistic_probability_forecast(
                    development,
                    forecast_index=forecast_index,
                    horizon_days=horizon,
                    training_window=training_window,
                    regularization_c=regularization_c,
                    feature_columns=feature_columns,
                )

                historical = historical_up_probability(
                    development,
                    forecast_index=forecast_index,
                    horizon=horizon,
                )

            except ValueError as exc:
                if (
                    "Insufficient matured" in str(exc)
                    or "only one class" in str(exc)
                ):
                    continue

                raise

            actual_return = (
                development.iloc[forecast_index + horizon]
                / development.iloc[forecast_index]
                - 1.0
            )

            rows.append(
                {
                    "Forecast Index": forecast_index,
                    "Horizon": horizon,
                    "Actual Up": int(actual_return > 0),
                    "ML Probability": ml.probability_up,
                    "Historical Probability": float(historical),
                }
            )

    if not rows:
        return pd.DataFrame(columns=COLUMNS)

    predictions = pd.DataFrame(rows)

    predictions = assign_research_periods(
        predictions,
        split,
    )

    predictions = predictions[
        predictions["Research Period"].isin(
            ["Training", "Validation"]
        )
    ]

    return predictions[COLUMNS].sort_values(
        ["Horizon", "Forecast Index"]
    ).reset_index(drop=True)
