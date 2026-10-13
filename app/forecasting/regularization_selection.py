"""Chronological regularization selection using training forecasts only."""

import numpy as np
import pandas as pd

from app.forecasting.chronological_selection import (
    select_probability_candidate,
)


def evaluate_regularization_selection(
    predictions: pd.DataFrame,
    candidate_columns: tuple[str, ...],
    baseline_column: str = "ML C=0.1",
    minimum_observations: int = 30,
    embargo_days: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Select regularization on matured training rows; score validation rows.

    Selection uses only rows labeled Training.
    Validation outcomes are used exclusively for subsequent evaluation.
    No reserved Test rows may enter this function.
    """

    required = {
        "Forecast Index",
        "Horizon",
        "Research Period",
        "Actual Up",
        *candidate_columns,
        baseline_column,
    }

    missing = required - set(predictions.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if not candidate_columns:
        raise ValueError("At least one candidate is required.")

    if baseline_column not in candidate_columns:
        raise ValueError("Baseline must be among candidate columns.")

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

    training = predictions.loc[
        predictions["Research Period"].eq("Training")
    ].copy()

    validation = predictions.loc[
        predictions["Research Period"].eq("Validation")
    ].copy()

    if validation.empty:
        raise ValueError("No validation forecasts available.")

    rows = []

    for horizon, group in validation.groupby("Horizon"):
        historical = training.loc[
            training["Horizon"].eq(horizon)
        ].copy()

        for _, observation in group.sort_values(
            "Forecast Index"
        ).iterrows():
            evaluation_index = int(observation["Forecast Index"])

            try:
                selection = select_probability_candidate(
                    predictions=historical,
                    evaluation_index=evaluation_index,
                    horizon_days=int(horizon),
                    candidate_columns=candidate_columns,
                    minimum_observations=minimum_observations,
                    embargo_days=embargo_days,
                )
            except ValueError as exc:
                if "Insufficient matured historical observations" in str(exc):
                    continue
                raise

            selected = selection.selected_candidate

            rows.append(
                {
                    "Forecast Index": evaluation_index,
                    "Horizon": int(horizon),
                    "Actual Up": float(observation["Actual Up"]),
                    "Selected Candidate": selected,
                    "Selected Probability": float(observation[selected]),
                    "Baseline Probability": float(
                        observation[baseline_column]
                    ),
                    "Neutral Probability": 0.5,
                    "Selection Observations": selection.observations,
                    "Latest Selection Index": (
                        selection.latest_training_index
                    ),
                }
            )

    if not rows:
        raise ValueError("No eligible validation forecasts.")

    results = pd.DataFrame(rows).sort_values(
        ["Horizon", "Forecast Index"]
    ).reset_index(drop=True)

    actual = results["Actual Up"].to_numpy(dtype=float)

    if not np.isfinite(actual).all() or not np.isin(
        actual, [0.0, 1.0]
    ).all():
        raise ValueError("Invalid validation outcomes.")

    summary_rows = []

    for horizon, group in results.groupby("Horizon"):
        actual = group["Actual Up"].to_numpy(dtype=float)

        for model, column in [
            ("Chronological Selection", "Selected Probability"),
            ("Fixed C=0.1", "Baseline Probability"),
            ("Neutral", "Neutral Probability"),
        ]:
            probability = group[column].to_numpy(dtype=float)

            if not np.isfinite(probability).all():
                raise ValueError("Invalid validation probabilities.")

            if ((probability < 0) | (probability > 1)).any():
                raise ValueError("Probabilities outside [0, 1].")

            clipped = np.clip(probability, 1e-15, 1 - 1e-15)

            brier = float(np.mean((probability - actual) ** 2))

            log_loss = float(
                -np.mean(
                    actual * np.log(clipped)
                    + (1 - actual) * np.log(1 - clipped)
                )
            )

            summary_rows.append(
                {
                    "Horizon": int(horizon),
                    "Model": model,
                    "N": len(group),
                    "Brier": brier,
                    "Log Loss": log_loss,
                }
            )

    summary = pd.DataFrame(summary_rows)

    return results, summary
