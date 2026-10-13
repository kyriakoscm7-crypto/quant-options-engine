"""Probability calibration and discrimination diagnostics."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


@dataclass(frozen=True)
class CalibrationReport:
    """Summary of probability forecast quality."""

    observations: int
    brier_score: float
    log_loss: float
    expected_calibration_error: float
    maximum_calibration_error: float
    mean_probability: float
    observed_up_rate: float
    probability_std: float
    extreme_forecast_rate: float
    roc_auc: float | None
    bins: pd.DataFrame


def analyze_calibration(
    actual: np.ndarray,
    probabilities: np.ndarray,
    n_bins: int = 10,
    extreme_threshold: float = 0.8,
) -> CalibrationReport:
    """Evaluate probability accuracy, calibration, and discrimination.

    Bins use fixed equal-width probability intervals.

    Expected Calibration Error is a descriptive bin-based metric.
    Its value depends on bin choice and sample size.

    ROC AUC is undefined when only one outcome class is present.
    """

    actual = np.asarray(actual, dtype=float)
    probabilities = np.asarray(probabilities, dtype=float)

    if actual.ndim != 1 or probabilities.ndim != 1:
        raise ValueError("Inputs must be one-dimensional.")

    if len(actual) == 0 or len(actual) != len(probabilities):
        raise ValueError("Inputs must be nonempty and equal length.")

    if not np.isfinite(actual).all():
        raise ValueError("Actual outcomes must be finite.")

    if not np.isin(actual, [0.0, 1.0]).all():
        raise ValueError("Actual outcomes must be binary.")

    if not np.isfinite(probabilities).all():
        raise ValueError("Probabilities must be finite.")

    if np.any((probabilities < 0) | (probabilities > 1)):
        raise ValueError("Probabilities must be between zero and one.")

    if isinstance(n_bins, (bool, np.bool_)) or not isinstance(
        n_bins, (int, np.integer)
    ):
        raise ValueError("n_bins must be an integer.")

    if n_bins < 2:
        raise ValueError("n_bins must be at least 2.")

    if not np.isfinite(extreme_threshold):
        raise ValueError("extreme_threshold must be finite.")

    if not 0.5 < extreme_threshold <= 1.0:
        raise ValueError(
            "extreme_threshold must be greater than 0.5 and at most 1."
        )

    brier = float(np.mean((probabilities - actual) ** 2))

    safe = np.clip(probabilities, 1e-12, 1 - 1e-12)

    log_loss = float(
        -np.mean(
            actual * np.log(safe)
            + (1 - actual) * np.log1p(-safe)
        )
    )

    edges = np.linspace(0.0, 1.0, n_bins + 1)

    bin_indices = np.minimum(
        np.searchsorted(edges, probabilities, side="right") - 1,
        n_bins - 1,
    )

    bin_rows = []
    ece = 0.0
    mce = 0.0

    for bin_index in range(n_bins):
        mask = bin_indices == bin_index
        count = int(np.sum(mask))

        lower = float(edges[bin_index])
        upper = float(edges[bin_index + 1])

        if count == 0:
            mean_predicted = np.nan
            observed_frequency = np.nan
            calibration_gap = np.nan
        else:
            mean_predicted = float(np.mean(probabilities[mask]))
            observed_frequency = float(np.mean(actual[mask]))
            calibration_gap = abs(
                mean_predicted - observed_frequency
            )

            ece += (count / len(actual)) * calibration_gap
            mce = max(mce, calibration_gap)

        bin_rows.append(
            {
                "Bin Lower": lower,
                "Bin Upper": upper,
                "Count": count,
                "Mean Predicted": mean_predicted,
                "Observed Frequency": observed_frequency,
                "Calibration Gap": calibration_gap,
            }
        )

    extreme_rate = float(
        np.mean(
            (probabilities >= extreme_threshold)
            | (probabilities <= 1 - extreme_threshold)
        )
    )

    if len(np.unique(actual)) < 2:
        auc = None
    else:
        auc = float(roc_auc_score(actual, probabilities))

    return CalibrationReport(
        observations=len(actual),
        brier_score=brier,
        log_loss=log_loss,
        expected_calibration_error=float(ece),
        maximum_calibration_error=float(mce),
        mean_probability=float(np.mean(probabilities)),
        observed_up_rate=float(np.mean(actual)),
        probability_std=float(np.std(probabilities)),
        extreme_forecast_rate=extreme_rate,
        roc_auc=auc,
        bins=pd.DataFrame(bin_rows),
    )
