"""Statistical reliability report for aligned probability forecasts.

Research-only. Evaluates validation predictions, never final-test results.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.forecasting.statistical_reliability import (
    block_bootstrap_brier_improvement,
)


@dataclass(frozen=True)
class ReliabilityComparison:
    horizon_days: int
    challenger: str
    observations: int
    historical_brier: float
    challenger_brier: float
    historical_advantage: float
    confidence_lower: float | None
    confidence_upper: float | None
    block_length: int | None
    evidence_status: str


def build_reliability_report(
    predictions: pd.DataFrame,
    step_days: int = 5,
    bootstrap_samples: int = 2000,
    random_seed: int = 42,
) -> list[ReliabilityComparison]:
    """Compare the historical benchmark with two alternative models.

    Positive advantage means the historical benchmark has lower
    Brier loss than the challenger.

    Confidence intervals are approximate and do not adjust for
    multiple comparisons or changing market regimes.
    """

    required = {
        "Forecast Index",
        "Horizon",
        "Research Period",
        "Actual Up",
        "Original Probability",
        "Uncertainty Probability",
        "Historical Probability",
    }

    if not required.issubset(predictions.columns):
        raise ValueError("Missing required prediction columns.")

    if (
        isinstance(step_days, bool)
        or not isinstance(step_days, int)
        or step_days < 1
    ):
        raise ValueError("step_days must be a positive integer.")

    if (
        isinstance(bootstrap_samples, bool)
        or not isinstance(bootstrap_samples, int)
        or bootstrap_samples < 100
    ):
        raise ValueError("bootstrap_samples must be at least 100.")

    if not isinstance(random_seed, int) or isinstance(random_seed, bool):
        raise ValueError("random_seed must be an integer.")

    validation = predictions[
        predictions["Research Period"] == "Validation"
    ].copy()

    if validation.empty:
        return []

    results = []

    challengers = {
        "Original": "Original Probability",
        "Uncertainty-aware": "Uncertainty Probability",
    }

    for horizon, group in validation.groupby("Horizon"):
        group = group.sort_values("Forecast Index")

        actual = group["Actual Up"].to_numpy(dtype=float)
        historical = group["Historical Probability"].to_numpy(dtype=float)

        for challenger_name, column in challengers.items():
            challenger = group[column].to_numpy(dtype=float)

            if (
                not np.isfinite(actual).all()
                or not np.isfinite(historical).all()
                or not np.isfinite(challenger).all()
                or not np.isin(actual, [0, 1]).all()
                or np.any((historical < 0) | (historical > 1))
                or np.any((challenger < 0) | (challenger > 1))
            ):
                raise ValueError("Invalid probabilities or outcomes.")

            historical_brier = float(
                np.mean((historical - actual) ** 2)
            )

            challenger_brier = float(
                np.mean((challenger - actual) ** 2)
            )

            advantage = challenger_brier - historical_brier

            try:
                reliability = block_bootstrap_brier_improvement(
                    model_probabilities=historical,
                    benchmark_probabilities=challenger,
                    actual_outcomes=actual,
                    horizon_days=int(horizon),
                    step_days=step_days,
                    bootstrap_samples=bootstrap_samples,
                    random_seed=random_seed,
                )

            except ValueError as exc:
                if (
                    len(group) >= 30
                    and len(group) >= 3 * int(
                        np.ceil(int(horizon) / step_days)
                    )
                ):
                    raise RuntimeError(
                        "Bootstrap failed despite sufficient observations."
                    ) from exc

                lower = None
                upper = None
                block_length = None
                status = "Insufficient evidence"

            else:
                lower = reliability.confidence_lower
                upper = reliability.confidence_upper
                block_length = reliability.block_length

                if lower > 0:
                    status = "Historical advantage supported"
                elif upper < 0:
                    status = "Challenger advantage supported"
                else:
                    status = "Inconclusive"

            results.append(
                ReliabilityComparison(
                    horizon_days=int(horizon),
                    challenger=challenger_name,
                    observations=len(group),
                    historical_brier=historical_brier,
                    challenger_brier=challenger_brier,
                    historical_advantage=advantage,
                    confidence_lower=lower,
                    confidence_upper=upper,
                    block_length=block_length,
                    evidence_status=status,
                )
            )

    return results
