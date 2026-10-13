"""Leakage-aware walk-forward evaluation of probability forecasts.

Research-only evaluation. This module does not generate trading advice.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.forecasting.probability_baseline import forecast_probabilities


@dataclass(frozen=True)
class BacktestMetrics:
    horizon_days: int
    predictions: int
    directional_accuracy: float
    brier_score: float
    baseline_brier_score: float
    average_predicted_probability: float
    actual_up_frequency: float


def walk_forward_predictions(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    training_days: int = 252,
    step: int = 1,
) -> pd.DataFrame:
    """Generate historical predictions using only information available then."""

    if training_days < 120:
        raise ValueError("training_days must be at least 120.")

    if not isinstance(step, int) or isinstance(step, bool) or step < 1:
        raise ValueError("step must be a positive integer.")

    if not horizons or any(
        not isinstance(h, int) or isinstance(h, bool) or h < 1
        for h in horizons
    ):
        raise ValueError("Horizons must be positive integers.")

    prices = pd.to_numeric(close_prices, errors="coerce")

    if (
        prices.isna().any()
        or not np.isfinite(prices.to_numpy()).all()
        or (prices <= 0).any()
    ):
        raise ValueError("Close prices must be finite and positive.")

    max_horizon = max(horizons)

    if len(prices) < training_days + max_horizon + 1:
        raise ValueError("Insufficient history for the requested backtest.")

    rows = []

    for index in range(
        training_days,
        len(prices) - min(horizons),
        step,
    ):
        history = prices.iloc[: index + 1]

        eligible_horizons = tuple(
            horizon
            for horizon in horizons
            if index + horizon < len(prices)
        )

        forecasts = forecast_probabilities(
            history,
            horizons=eligible_horizons,
            lookback=training_days,
            minimum_observations=120,
        )

        current_price = float(prices.iloc[index])

        for forecast in forecasts:
            future_price = float(
                prices.iloc[index + forecast.horizon_days]
            )

            realized_return = (
                future_price / current_price - 1.0
            ) * 100.0

            rows.append(
                {
                    "Forecast Index": index,
                    "Horizon": forecast.horizon_days,
                    "Probability Up": forecast.probability_up,
                    "Actual Up": int(realized_return > 0),
                    "Realized Return (%)": realized_return,
                }
            )

    return pd.DataFrame(rows)


def evaluate_predictions(predictions: pd.DataFrame) -> list[BacktestMetrics]:
    """Evaluate directional predictions and probability calibration."""

    required = {
        "Horizon",
        "Probability Up",
        "Actual Up",
    }

    if not required.issubset(predictions.columns):
        raise ValueError("Missing required prediction columns.")

    metrics = []

    for horizon, group in predictions.groupby("Horizon"):
        probabilities = group["Probability Up"].to_numpy(dtype=float)
        actual = group["Actual Up"].to_numpy(dtype=float)

        if len(probabilities) == 0:
            continue

        if (
            not np.isfinite(probabilities).all()
            or not np.isfinite(actual).all()
            or ((probabilities < 0) | (probabilities > 1)).any()
            or not np.isin(actual, [0, 1]).all()
        ):
            raise ValueError("Invalid prediction values.")

        predicted_up = probabilities > 0.5

        directional_accuracy = float(
            np.mean(predicted_up == actual)
        )

        brier_score = float(
            np.mean((probabilities - actual) ** 2)
        )

        base_rate = float(np.mean(actual))

        baseline_brier_score = float(
            np.mean((base_rate - actual) ** 2)
        )

        metrics.append(
            BacktestMetrics(
                horizon_days=int(horizon),
                predictions=len(group),
                directional_accuracy=directional_accuracy,
                brier_score=brier_score,
                baseline_brier_score=baseline_brier_score,
                average_predicted_probability=float(
                    np.mean(probabilities)
                ),
                actual_up_frequency=base_rate,
            )
        )

    return metrics
