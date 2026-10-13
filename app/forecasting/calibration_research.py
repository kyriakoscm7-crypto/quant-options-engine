"""Calibration analysis for matched walk-forward validation predictions."""

import numpy as np
import pandas as pd

from app.forecasting.calibration_diagnostics import analyze_calibration
from app.forecasting.probability_benchmarks import (
    historical_base_rate,
    neutral_probability,
)


def analyze_research_predictions(
    close_prices: pd.Series,
    predictions: pd.DataFrame,
    ml_weight: float = 0.25,
    n_bins: int = 10,
) -> pd.DataFrame:
    """Analyze calibration using validation forecasts only.

    All models are evaluated on identical forecast origins and outcomes.
    Training and reserved test observations are excluded.

    Historical and Base Rate are equivalent implementations, not
    independent forecasting models.
    """

    required = {
        "Forecast Index",
        "Horizon",
        "Research Period",
        "Actual Up",
        "Historical Probability",
        "ML Probability",
    }

    missing = required - set(predictions.columns)

    if missing:
        raise ValueError(f"Missing prediction columns: {sorted(missing)}")

    if not 0 <= ml_weight <= 1:
        raise ValueError("ml_weight must be between 0 and 1.")

    validation = predictions.loc[
        predictions["Research Period"] == "Validation"
    ].copy()

    rows = []

    for horizon, group in validation.groupby("Horizon"):
        actual = group["Actual Up"].to_numpy(dtype=float)

        historical = group[
            "Historical Probability"
        ].to_numpy(dtype=float)

        ml = group["ML Probability"].to_numpy(dtype=float)

        base_rate = np.array(
            [
                historical_base_rate(
                    close_prices=close_prices,
                    forecast_index=int(index),
                    horizon_days=int(horizon),
                    minimum_samples=30,
                ).probability_up
                for index in group["Forecast Index"]
            ],
            dtype=float,
        )

        ensemble = (
            (1 - ml_weight) * historical
            + ml_weight * ml
        )

        models = {
            "Neutral": np.full(len(group), neutral_probability()),
            "Base Rate": base_rate,
            "Historical": historical,
            "ML": ml,
            "Ensemble": ensemble,
        }

        for model, probabilities in models.items():
            report = analyze_calibration(
                actual=actual,
                probabilities=probabilities,
                n_bins=n_bins,
            )

            rows.append(
                {
                    "Horizon": int(horizon),
                    "Model": model,
                    "N": report.observations,
                    "Brier": report.brier_score,
                    "Log Loss": report.log_loss,
                    "ECE": report.expected_calibration_error,
                    "MCE": report.maximum_calibration_error,
                    "Mean Probability": report.mean_probability,
                    "Actual Up Rate": report.observed_up_rate,
                    "Probability Std": report.probability_std,
                    "Extreme Forecast Rate": report.extreme_forecast_rate,
                    "ROC AUC": report.roc_auc,
                }
            )

    return pd.DataFrame(rows)
