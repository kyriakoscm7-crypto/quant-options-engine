"""Compare model probabilities with a leakage-free historical benchmark."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.forecasting.historical_benchmark import historical_up_probability
from app.forecasting.walk_forward import walk_forward_predictions


@dataclass(frozen=True)
class ModelComparison:
    horizon_days: int
    predictions: int
    model_brier_score: float
    benchmark_brier_score: float
    brier_improvement: float
    model_directional_accuracy: float
    benchmark_directional_accuracy: float


def compare_model_to_benchmark(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    training_days: int = 252,
    step: int = 5,
) -> list[ModelComparison]:
    """Evaluate model and benchmark on identical historical outcomes."""

    predictions = walk_forward_predictions(
        close_prices,
        horizons=horizons,
        training_days=training_days,
        step=step,
    )

    rows = []

    for row in predictions.to_dict("records"):
        forecast_index = int(row["Forecast Index"])
        horizon = int(row["Horizon"])
        model_probability = float(row["Probability Up"])
        actual_up = int(row["Actual Up"])

        benchmark_probability = historical_up_probability(
            close_prices,
            forecast_index=forecast_index,
            horizon=horizon,
        )

        rows.append(
            {
                "Horizon": horizon,
                "Model Probability": model_probability,
                "Benchmark Probability": benchmark_probability,
                "Actual Up": actual_up,
            }
        )

    comparison = pd.DataFrame(rows)
    results = []

    for horizon, group in comparison.groupby("Horizon"):
        model_p = group["Model Probability"].to_numpy(dtype=float)
        benchmark_p = group["Benchmark Probability"].to_numpy(dtype=float)
        actual = group["Actual Up"].to_numpy(dtype=float)

        model_brier = float(np.mean((model_p - actual) ** 2))
        benchmark_brier = float(
            np.mean((benchmark_p - actual) ** 2)
        )

        results.append(
            ModelComparison(
                horizon_days=int(horizon),
                predictions=len(group),
                model_brier_score=model_brier,
                benchmark_brier_score=benchmark_brier,
                brier_improvement=benchmark_brier - model_brier,
                model_directional_accuracy=float(
                    np.mean((model_p > 0.5) == actual)
                ),
                benchmark_directional_accuracy=float(
                    np.mean((benchmark_p > 0.5) == actual)
                ),
            )
        )

    return results
