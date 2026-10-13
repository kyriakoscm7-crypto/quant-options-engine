"""Generate strictly matched walk-forward regularization candidates."""

import numpy as np
import pandas as pd

from app.forecasting.ml_walk_forward import ml_walk_forward_predictions

DEFAULT_REGULARIZATION_VALUES = (0.001, 0.01, 0.1, 1.0)

MATCH_COLUMNS = (
    "Forecast Index",
    "Horizon",
    "Research Period",
    "Actual Up",
    "Historical Probability",
)


def generate_regularization_candidates(
    close_prices: pd.Series,
    regularization_values: tuple[float, ...] = DEFAULT_REGULARIZATION_VALUES,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    training_window: int = 756,
    step: int = 5,
) -> pd.DataFrame:
    """Generate candidates on identical historical forecast observations.

    All forecasts are produced by the existing walk-forward engine.
    The reserved final-test period remains excluded.
    """

    if not regularization_values:
        raise ValueError("At least one regularization value is required.")

    values = []

    for value in regularization_values:
        if isinstance(value, (bool, np.bool_)):
            raise ValueError("Regularization values must be positive.")

        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Regularization values must be numeric."
            ) from exc

        if not np.isfinite(numeric) or numeric <= 0:
            raise ValueError(
                "Regularization values must be positive and finite."
            )

        values.append(numeric)

    if len(set(values)) != len(values):
        raise ValueError("Regularization values must be unique.")

    combined = None

    for value in values:
        predictions = ml_walk_forward_predictions(
            close_prices=close_prices,
            horizons=horizons,
            training_window=training_window,
            step=step,
            regularization_c=value,
        )

        if predictions.empty:
            raise ValueError(
                f"No predictions generated for regularization C={value}."
            )

        if predictions.duplicated(
            subset=["Forecast Index", "Horizon"]
        ).any():
            raise ValueError("Duplicate forecast keys detected.")

        if predictions["Research Period"].isin(["Test"]).any():
            raise ValueError("Reserved test predictions are not allowed.")

        candidate_name = f"ML C={value:g}"

        candidate = predictions[
            list(MATCH_COLUMNS) + ["ML Probability"]
        ].copy()

        candidate = candidate.rename(
            columns={"ML Probability": candidate_name}
        )

        if combined is None:
            combined = candidate

        else:
            combined = combined.merge(
                candidate,
                on=list(MATCH_COLUMNS),
                how="outer",
                validate="one_to_one",
                indicator=True,
            )

            if not combined["_merge"].eq("both").all():
                raise ValueError(
                    "Regularization candidates have mismatched "
                    "forecast dates, horizons, periods, or outcomes."
                )

            combined = combined.drop(columns="_merge")

    if combined is None:
        raise ValueError("No candidates generated.")

    candidate_columns = [
        f"ML C={value:g}" for value in values
    ]

    if combined[candidate_columns].isna().any().any():
        raise ValueError("Candidate probabilities contain missing values.")

    probabilities = combined[candidate_columns].to_numpy(dtype=float)

    if not np.isfinite(probabilities).all():
        raise ValueError("Candidate probabilities must be finite.")

    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Candidate probabilities must be within [0, 1].")

    return combined.sort_values(
        ["Horizon", "Forecast Index"]
    ).reset_index(drop=True)
