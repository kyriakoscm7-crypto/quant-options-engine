"""Conservative probability ensemble for forecasting research.

Combines a historical probability benchmark with an ML probability.
Fixed weights are research configurations, not optimized parameters.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class EnsembleForecast:
    historical_probability: float
    ml_probability: float
    ml_weight: float
    probability_up: float


def shrinkage_probability(
    historical_probability: float,
    ml_probability: float,
    ml_weight: float = 0.25,
) -> EnsembleForecast:
    """Blend historical and ML probabilities using a fixed weight."""

    values = (
        historical_probability,
        ml_probability,
        ml_weight,
    )

    if any(
        isinstance(value, (bool, np.bool_))
        or not isinstance(value, (int, float, np.number))
        for value in values
    ):
        raise ValueError("Probabilities and weight must be numeric.")

    if not all(np.isfinite(value) for value in values):
        raise ValueError("Probabilities and weight must be finite.")

    if not all(0 <= value <= 1 for value in values):
        raise ValueError("Probabilities and weight must be between 0 and 1.")

    probability = (
        (1.0 - ml_weight) * historical_probability
        + ml_weight * ml_probability
    )

    return EnsembleForecast(
        historical_probability=float(historical_probability),
        ml_probability=float(ml_probability),
        ml_weight=float(ml_weight),
        probability_up=float(probability),
    )


def add_ensemble_predictions(
    predictions: pd.DataFrame,
    ml_weight: float = 0.25,
) -> pd.DataFrame:
    """Add ensemble probabilities to aligned ML/benchmark predictions."""

    required = {
        "ML Probability",
        "Historical Probability",
    }

    if not isinstance(predictions, pd.DataFrame):
        raise ValueError("predictions must be a DataFrame.")

    if not required.issubset(predictions.columns):
        raise ValueError("Missing required probability columns.")

    shrinkage_probability(0.5, 0.5, ml_weight)

    result = predictions.copy()

    for column in required:
        values = result[column].to_numpy()

        if not pd.api.types.is_numeric_dtype(result[column]):
            raise ValueError(f"{column} must be numeric.")

        if (
            not np.isfinite(values).all()
            or np.any(values < 0)
            or np.any(values > 1)
        ):
            raise ValueError(f"{column} contains invalid probabilities.")

    result["Ensemble Probability"] = (
        (1.0 - ml_weight) * result["Historical Probability"]
        + ml_weight * result["ML Probability"]
    )

    return result
