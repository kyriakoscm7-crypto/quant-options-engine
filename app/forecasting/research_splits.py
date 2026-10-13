"""Chronological research splits for forecasting experiments.

Separates model development, validation, and final evaluation.

Forward-return labels must mature within their assigned period
to prevent leakage across research boundaries.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ResearchSplit:
    training_end: int
    validation_start: int
    validation_end: int
    test_start: int
    total_observations: int
    embargo_days: int


def create_research_split(
    total_observations: int,
    training_fraction: float = 0.60,
    validation_fraction: float = 0.20,
    embargo_days: int = 60,
) -> ResearchSplit:
    """Create chronological train/validation/test boundaries.

    Indices refer to positions in the original price series.

    The embargo separates eligible forecast origins between
    research periods. Label maturity must still be checked
    separately for each forecast horizon.
    """

    if (
        isinstance(total_observations, bool)
        or not isinstance(total_observations, int)
        or total_observations < 300
    ):
        raise ValueError("At least 300 observations are required.")

    if not 0 < training_fraction < 1:
        raise ValueError("training_fraction must be between 0 and 1.")

    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1.")

    if training_fraction + validation_fraction >= 1:
        raise ValueError("Training and validation fractions must sum to less than 1.")

    if (
        isinstance(embargo_days, bool)
        or not isinstance(embargo_days, int)
        or embargo_days < 0
    ):
        raise ValueError("embargo_days must be a nonnegative integer.")

    training_end = int(total_observations * training_fraction)
    validation_end = int(
        total_observations * (
            training_fraction + validation_fraction
        )
    )

    validation_start = training_end + embargo_days
    test_start = validation_end + embargo_days

    if validation_start >= validation_end:
        raise ValueError("Embargo leaves no validation observations.")

    if test_start >= total_observations:
        raise ValueError("Embargo leaves no test observations.")

    return ResearchSplit(
        training_end=training_end,
        validation_start=validation_start,
        validation_end=validation_end,
        test_start=test_start,
        total_observations=total_observations,
        embargo_days=embargo_days,
    )


def assign_research_periods(
    predictions: pd.DataFrame,
    split: ResearchSplit,
) -> pd.DataFrame:
    """Assign eligible historical predictions to research periods.

    Forecast Index is the prediction origin.
    Horizon is the number of future trading sessions required.

    A forecast is assigned only when its realized outcome
    falls within the same research period as its origin.
    """

    required = {"Forecast Index", "Horizon"}

    if not required.issubset(predictions.columns):
        raise ValueError("Missing required prediction columns.")

    result = predictions.copy()

    origin = result["Forecast Index"]
    horizon = result["Horizon"]
    maturity = origin + horizon

    training = (
        (origin >= 0)
        & (origin < split.training_end)
        & (maturity < split.training_end)
    )

    validation = (
        (origin >= split.validation_start)
        & (origin < split.validation_end)
        & (maturity < split.validation_end)
    )

    test = (
        (origin >= split.test_start)
        & (origin < split.total_observations)
        & (maturity < split.total_observations)
    )

    result["Research Period"] = "Excluded"

    result.loc[training, "Research Period"] = "Training"
    result.loc[validation, "Research Period"] = "Validation"
    result.loc[test, "Research Period"] = "Test"

    return result
