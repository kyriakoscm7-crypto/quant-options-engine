"""Compare regularization candidates using matched validation forecasts."""

import numpy as np
import pandas as pd

from app.forecasting.calibration_diagnostics import analyze_calibration


def analyze_regularization_candidates(
    predictions: pd.DataFrame,
    candidate_columns: tuple[str, ...],
    n_bins: int = 10,
) -> pd.DataFrame:
    """Evaluate candidate probabilities on identical validation observations.

    Training observations are excluded from scoring.
    Reserved test observations are never evaluated.

    Results are descriptive validation diagnostics, not evidence
    of independent out-of-sample predictive skill.
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
        raise ValueError("No validation forecasts available.")

    rows = []

    for horizon, group in validation.groupby("Horizon"):
        actual = group["Actual Up"].to_numpy(dtype=float)

        if not np.isfinite(actual).all():
            raise ValueError("Validation outcomes must be finite.")

        if not np.isin(actual, [0.0, 1.0]).all():
            raise ValueError("Validation outcomes must be binary.")

        models = {
            "Neutral": np.full(len(group), 0.5),
        }

        for candidate in candidate_columns:
            models[candidate] = group[candidate].to_numpy(
                dtype=float
            )

        for model_name, probabilities in models.items():
            report = analyze_calibration(
                actual=actual,
                probabilities=probabilities,
                n_bins=n_bins,
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
                    "Extreme Forecast Rate": (
                        report.extreme_forecast_rate
                    ),
                    "ECE": report.expected_calibration_error,
                    "MCE": report.maximum_calibration_error,
                }
            )

    return pd.DataFrame(rows).sort_values(
        ["Horizon", "Brier", "Model"],
        kind="stable",
    ).reset_index(drop=True)
