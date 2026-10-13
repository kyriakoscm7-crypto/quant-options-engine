"""Chronological comparison of three probability forecasting models."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.forecasting.historical_benchmark import historical_up_probability
from app.forecasting.research_splits import (
    assign_research_periods,
    create_research_split,
)
from app.forecasting.uncertainty_aware import uncertainty_aware_forecast
from app.forecasting.walk_forward import walk_forward_predictions


@dataclass(frozen=True)
class ModelComparisonResult:
    period: str
    horizon_days: int
    predictions: int
    original_brier: float
    uncertainty_aware_brier: float
    historical_brier: float
    improvement_vs_original: float
    improvement_vs_historical: float


def compare_three_models(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    training_days: int = 252,
    step: int = 5,
) -> list[ModelComparisonResult]:
    """Compare models without exposing final-test prices."""

    if not isinstance(close_prices, pd.Series):
        raise ValueError("close_prices must be a pandas Series.")

    if not horizons or any(
        not isinstance(h, int) or isinstance(h, bool) or h <= 0
        for h in horizons
    ):
        raise ValueError("Horizons must contain positive integers.")

    if (
        not isinstance(training_days, int)
        or isinstance(training_days, bool)
        or training_days < 120
    ):
        raise ValueError("training_days must be at least 120.")

    if (
        not isinstance(step, int)
        or isinstance(step, bool)
        or step < 1
    ):
        raise ValueError("step must be a positive integer.")

    prices = close_prices.to_numpy(dtype=float)

    if (
        len(prices) < 300
        or not np.all(np.isfinite(prices))
        or np.any(prices <= 0)
    ):
        raise ValueError("Price history must be sufficient, finite, and positive.")

    split = create_research_split(
        total_observations=len(close_prices),
        embargo_days=max(horizons),
    )

    development_prices = close_prices.iloc[:split.validation_end]

    original_predictions = walk_forward_predictions(
        development_prices,
        horizons=horizons,
        training_days=training_days,
        step=step,
    )

    predictions = assign_research_periods(
        original_predictions,
        split,
    )

    predictions = predictions[
        predictions["Research Period"].isin(["Training", "Validation"])
    ]

    records = []

    for row in predictions.to_dict("records"):
        forecast_index = int(row["Forecast Index"])
        horizon = int(row["Horizon"])

        historical_prices = development_prices.iloc[:forecast_index + 1]

        uncertainty = uncertainty_aware_forecast(
            historical_prices,
            horizons=(horizon,),
            lookback=training_days,
            minimum_observations=120,
        )[0]

        historical_probability = historical_up_probability(
            development_prices,
            forecast_index=forecast_index,
            horizon=horizon,
        )

        records.append(
            {
                "Period": row["Research Period"],
                "Horizon": horizon,
                "Actual": float(row["Actual Up"]),
                "Original": float(row["Probability Up"]),
                "Uncertainty": uncertainty.probability_up,
                "Historical": float(historical_probability),
            }
        )

    if not records:
        return []

    comparison = pd.DataFrame(records)

    results = []

    for (period, horizon), group in comparison.groupby(
        ["Period", "Horizon"]
    ):
        actual = group["Actual"].to_numpy(dtype=float)

        original = group["Original"].to_numpy(dtype=float)
        uncertainty = group["Uncertainty"].to_numpy(dtype=float)
        historical = group["Historical"].to_numpy(dtype=float)

        original_brier = float(np.mean((original - actual) ** 2))
        uncertainty_brier = float(np.mean((uncertainty - actual) ** 2))
        historical_brier = float(np.mean((historical - actual) ** 2))

        results.append(
            ModelComparisonResult(
                period=str(period),
                horizon_days=int(horizon),
                predictions=len(group),
                original_brier=original_brier,
                uncertainty_aware_brier=uncertainty_brier,
                historical_brier=historical_brier,
                improvement_vs_original=original_brier - uncertainty_brier,
                improvement_vs_historical=historical_brier - uncertainty_brier,
            )
        )

    return results
