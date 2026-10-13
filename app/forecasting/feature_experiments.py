"""Training-only comparisons of forecasting feature configurations."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from app.forecasting.market_features import FEATURE_COLUMNS
from app.forecasting.ml_walk_forward import ml_walk_forward_predictions
from app.forecasting.research_runner import calculate_probability_scores

SIMPLIFIED_FEATURES = (
    "momentum_20d",
    "volatility_60d",
    "trend_50d",
    "trend_200d",
)


@dataclass(frozen=True)
class ExperimentConfiguration:
    name: str
    features: tuple[str, ...]
    regularization_c: float


CONFIGURATIONS = (
    ExperimentConfiguration("A - Original", FEATURE_COLUMNS, 0.1),
    ExperimentConfiguration("B - Regularized", FEATURE_COLUMNS, 0.01),
    ExperimentConfiguration("C - Simplified", SIMPLIFIED_FEATURES, 0.1),
    ExperimentConfiguration("D - Simplified Regularized", SIMPLIFIED_FEATURES, 0.01),
)


def expected_calibration_error(
    actual: np.ndarray,
    probability: np.ndarray,
    bins: int = 10,
) -> float:
    """Calculate weighted absolute calibration error."""

    actual = np.asarray(actual, dtype=float)
    probability = np.asarray(probability, dtype=float)

    if actual.size == 0:
        return float("nan")

    if actual.shape != probability.shape:
        raise ValueError("Actual outcomes and probabilities must match.")

    if bins < 1:
        raise ValueError("bins must be positive.")

    if not np.isfinite(actual).all() or not np.isfinite(probability).all():
        raise ValueError("Inputs must be finite.")

    if not np.isin(actual, [0.0, 1.0]).all():
        raise ValueError("Actual outcomes must be binary.")

    if ((probability < 0) | (probability > 1)).any():
        raise ValueError("Probabilities must be between zero and one.")

    edges = np.linspace(0.0, 1.0, bins + 1)
    assignments = np.minimum(
        np.searchsorted(edges, probability, side="right") - 1,
        bins - 1,
    )

    error = 0.0

    for index in range(bins):
        mask = assignments == index

        if not mask.any():
            continue

        observed = actual[mask].mean()
        predicted = probability[mask].mean()

        error += mask.mean() * abs(observed - predicted)

    return float(error)


def run_feature_experiments(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    training_window: int = 756,
    step: int = 5,
) -> pd.DataFrame:
    """Compare four ML configurations using training predictions only."""

    results = []

    for configuration in CONFIGURATIONS:
        predictions = ml_walk_forward_predictions(
            close_prices,
            horizons=horizons,
            training_window=training_window,
            step=step,
            regularization_c=configuration.regularization_c,
            feature_columns=configuration.features,
            training_only=True,
        )

        # Never score Validation or reserved Test observations.
        predictions = predictions.loc[
            predictions["Research Period"] == "Training"
        ].copy()

        for horizon in horizons:
            subset = predictions.loc[
                predictions["Horizon"] == horizon
            ]

            if subset.empty:
                continue

            actual = subset["Actual Up"].to_numpy(dtype=float)
            probability = subset["ML Probability"].to_numpy(dtype=float)
            historical = subset["Historical Probability"].to_numpy(dtype=float)

            brier, log_loss = calculate_probability_scores(
                actual,
                probability,
            )

            historical_brier, _ = calculate_probability_scores(
                actual,
                historical,
            )

            auc = (
                float(roc_auc_score(actual, probability))
                if np.unique(actual).size == 2
                else float("nan")
            )

            results.append(
                {
                    "Configuration": configuration.name,
                    "Horizon": horizon,
                    "Features": len(configuration.features),
                    "C": configuration.regularization_c,
                    "N": len(subset),
                    "Brier": brier,
                    "Historical Brier": historical_brier,
                    "Brier Improvement": historical_brier - brier,
                    "Log Loss": log_loss,
                    "ROC AUC": auc,
                    "Calibration Error": expected_calibration_error(
                        actual,
                        probability,
                    ),
                }
            )

    return pd.DataFrame(results)
