"""Probability calibration analysis for historical forecasts.

Research-only diagnostics. Calibration estimates from overlapping
forecast windows must not be treated as independent observations.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CalibrationBin:
    lower_bound: float
    upper_bound: float
    predictions: int
    average_probability: float
    observed_frequency: float
    calibration_error: float


@dataclass(frozen=True)
class CalibrationSummary:
    predictions: int
    brier_score: float
    expected_calibration_error: float
    maximum_calibration_error: float
    average_predicted_probability: float
    observed_up_frequency: float


def analyze_calibration(
    predictions: pd.DataFrame,
    bins: int = 10,
) -> tuple[CalibrationSummary, list[CalibrationBin]]:
    """Compare predicted probabilities with observed binary outcomes.

    Required columns:
        Probability Up: forecast probability between 0 and 1.
        Actual Up: realized outcome, either 0 or 1.

    Results describe the supplied evaluation sample only.
    """

    required = {"Probability Up", "Actual Up"}

    if not isinstance(predictions, pd.DataFrame):
        raise TypeError("predictions must be a pandas DataFrame.")

    if not required.issubset(predictions.columns):
        raise ValueError("Missing required prediction columns.")

    if predictions.empty:
        raise ValueError("Cannot analyze an empty prediction sample.")

    if isinstance(bins, bool) or not isinstance(bins, int) or bins < 2:
        raise ValueError("bins must be an integer of at least 2.")

    probabilities = pd.to_numeric(
        predictions["Probability Up"],
        errors="coerce",
    ).to_numpy(dtype=float)

    actual = pd.to_numeric(
        predictions["Actual Up"],
        errors="coerce",
    ).to_numpy(dtype=float)

    if not np.isfinite(probabilities).all():
        raise ValueError("Probabilities must be finite.")

    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Probabilities must be between 0 and 1.")

    if not np.isfinite(actual).all() or not np.isin(actual, [0, 1]).all():
        raise ValueError("Actual outcomes must be 0 or 1.")

    edges = np.linspace(0.0, 1.0, bins + 1)

    bin_indices = np.minimum(
        np.searchsorted(edges, probabilities, side="right") - 1,
        bins - 1,
    )

    calibration_bins = []

    weighted_error = 0.0
    maximum_error = 0.0

    for index in range(bins):
        mask = bin_indices == index
        count = int(mask.sum())

        if count == 0:
            continue

        average_probability = float(probabilities[mask].mean())
        observed_frequency = float(actual[mask].mean())

        error = abs(average_probability - observed_frequency)

        weighted_error += count * error
        maximum_error = max(maximum_error, error)

        calibration_bins.append(
            CalibrationBin(
                lower_bound=float(edges[index]),
                upper_bound=float(edges[index + 1]),
                predictions=count,
                average_probability=average_probability,
                observed_frequency=observed_frequency,
                calibration_error=error,
            )
        )

    summary = CalibrationSummary(
        predictions=len(probabilities),
        brier_score=float(np.mean((probabilities - actual) ** 2)),
        expected_calibration_error=weighted_error / len(probabilities),
        maximum_calibration_error=maximum_error,
        average_predicted_probability=float(probabilities.mean()),
        observed_up_frequency=float(actual.mean()),
    )

    return summary, calibration_bins
