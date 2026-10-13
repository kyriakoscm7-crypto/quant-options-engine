"""Leakage-safe chronological selection of probability forecasting candidates."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SelectionResult:
    """Selection outcome and its historical evidence."""

    selected_candidate: str
    selected_brier: float
    observations: int
    evaluation_index: int
    latest_training_index: int
    horizon_days: int
    candidate_scores: pd.DataFrame


def select_probability_candidate(
    predictions: pd.DataFrame,
    evaluation_index: int,
    horizon_days: int,
    candidate_columns: tuple[str, ...],
    minimum_observations: int = 30,
    embargo_days: int = 0,
) -> SelectionResult:
    """Select the lowest-Brier candidate using matured earlier outcomes.

    A training forecast is eligible only when:

        forecast_index + horizon_days + embargo_days < evaluation_index

    The strict inequality is intentionally conservative.

    All candidates use identical historical observations.
    Candidate names are sorted to make ties deterministic.

    This selector assumes candidate probabilities were themselves
    generated without future information.
    """

    def require_integer(name, value, minimum):
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value, (int, np.integer)
        ):
            raise ValueError(f"{name} must be an integer.")

        if value < minimum:
            raise ValueError(f"{name} must be at least {minimum}.")

    require_integer("evaluation_index", evaluation_index, 0)
    require_integer("horizon_days", horizon_days, 1)
    require_integer("minimum_observations", minimum_observations, 1)
    require_integer("embargo_days", embargo_days, 0)

    if not candidate_columns:
        raise ValueError("At least one candidate is required.")

    if len(set(candidate_columns)) != len(candidate_columns):
        raise ValueError("Candidate names must be unique.")

    required = {"Forecast Index", "Horizon", "Actual Up"}
    required.update(candidate_columns)

    missing = required - set(predictions.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if not predictions["Forecast Index"].notna().all():
        raise ValueError("Forecast indices must be present.")

    if not predictions["Horizon"].notna().all():
        raise ValueError("Horizons must be present.")

    history = predictions.loc[
        (predictions["Horizon"] == horizon_days)
        & (
            predictions["Forecast Index"]
            + horizon_days
            + embargo_days
            < evaluation_index
        )
    ].copy()

    if len(history) < minimum_observations:
        raise ValueError(
            "Insufficient matured historical observations: "
            f"{len(history)} < {minimum_observations}"
        )

    history = history.sort_values("Forecast Index")

    forecast_indices = history["Forecast Index"].to_numpy(dtype=float)
    actual = history["Actual Up"].to_numpy(dtype=float)

    if not np.isfinite(forecast_indices).all():
        raise ValueError("Forecast indices must be finite.")

    if not np.isfinite(actual).all():
        raise ValueError("Actual outcomes must be finite.")

    if not np.isin(actual, [0.0, 1.0]).all():
        raise ValueError("Actual outcomes must be binary.")

    if history["Forecast Index"].duplicated().any():
        raise ValueError("Duplicate forecast indices are not allowed.")

    rows = []

    for candidate in sorted(candidate_columns):
        probability = history[candidate].to_numpy(dtype=float)

        if not np.isfinite(probability).all():
            raise ValueError(
                f"Candidate {candidate} contains invalid probabilities."
            )

        if np.any((probability < 0) | (probability > 1)):
            raise ValueError(
                f"Candidate {candidate} has probabilities outside [0, 1]."
            )

        brier = float(np.mean((probability - actual) ** 2))

        rows.append(
            {
                "Candidate": candidate,
                "Brier": brier,
                "N": len(history),
            }
        )

    scores = pd.DataFrame(rows).sort_values(
        ["Brier", "Candidate"],
        kind="stable",
    ).reset_index(drop=True)

    winner = scores.iloc[0]

    return SelectionResult(
        selected_candidate=str(winner["Candidate"]),
        selected_brier=float(winner["Brier"]),
        observations=len(history),
        evaluation_index=int(evaluation_index),
        latest_training_index=int(history["Forecast Index"].max()),
        horizon_days=int(horizon_days),
        candidate_scores=scores,
    )
