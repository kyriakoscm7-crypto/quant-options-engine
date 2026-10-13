"""Compare regularization candidates against historical benchmarks."""

import numpy as np
import pandas as pd

from app.forecasting.calibration_diagnostics import analyze_calibration
from app.forecasting.probability_benchmarks import historical_base_rate


def compare_regularization_benchmarks(
    close_prices: pd.Series,
    predictions: pd.DataFrame,
    candidate_columns: tuple[str, ...],
    minimum_samples: int = 30,
) -> pd.DataFrame:
    """Score matched validation forecasts without using reserved test data.

    Historical probabilities are recomputed at each forecast origin
    using only previously matured outcomes.
    """

    if not candidate_columns:
        raise ValueError("At least one candidate is required.")

    if len(set(candidate_columns)) != len(candidate_columns):
        raise ValueError("Candidate names must be unique.")

    required = {
        "Forecast Index",
        "Horizon",
        "Research Period",
        "Actual Up",
        *candidate_columns,
    }

    missing = required - set(predictions.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if predictions["Research Period"].eq("Test").any():
        raise ValueError("Reserved test observations are not allowed.")

    if not predictions["Research Period"].isin(
        ["Training", "Validation"]
    ).all():
        raise ValueError("Unknown research period detected.")

    if predictions.duplicated(
        subset=["Forecast Index", "Horizon"]
    ).any():
        raise ValueError("Duplicate forecast keys detected.")

    validation = predictions.loc[
        predictions["Research Period"].eq("Validation")
    ].copy()

    if validation.empty:
        raise ValueError("No validation observations available.")

    rows = []

    for horizon, group in validation.groupby("Horizon"):
        group = group.sort_values("Forecast Index")

        actual = group["Actual Up"].to_numpy(dtype=float)

        if not np.isfinite(actual).all():
            raise ValueError("Outcomes must be finite.")

        if not np.isin(actual, [0.0, 1.0]).all():
            raise ValueError("Outcomes must be binary.")

        historical_probabilities = []

        for forecast_index in group["Forecast Index"]:
            benchmark = historical_base_rate(
                close_prices=close_prices,
                forecast_index=int(forecast_index),
                horizon_days=int(horizon),
                minimum_samples=minimum_samples,
            )

            historical_probabilities.append(
                benchmark.probability_up
            )

        models = {
            "Neutral": np.full(len(group), 0.5),
            "Historical Base Rate": np.asarray(
                historical_probabilities,
                dtype=float,
            ),
        }

        for candidate in candidate_columns:
            models[candidate] = group[candidate].to_numpy(
                dtype=float
            )

        for model_name, probabilities in models.items():
            report = analyze_calibration(
                actual=actual,
                probabilities=probabilities,
            )

            rows.append(
                {
                    "Horizon": int(horizon),
                    "Model": model_name,
                    "N": report.observations,
                    "Brier": report.brier_score,
                    "Log Loss": report.log_loss,
                    "ROC AUC": report.roc_auc,
                    "Mean Probability": report.mean_probability,
                    "Actual Up Rate": report.observed_up_rate,
                    "Probability Std": report.probability_std,
                    "ECE": report.expected_calibration_error,
                }
            )

    return pd.DataFrame(rows).sort_values(
        ["Horizon", "Brier", "Model"],
        kind="stable",
    ).reset_index(drop=True)
