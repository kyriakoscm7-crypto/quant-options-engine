"""Statistical reliability analysis for probabilistic forecasts.

Uses a circular moving-block bootstrap to preserve some of the
serial dependence caused by overlapping forecast horizons.

Research-only diagnostics. Bootstrap confidence intervals are
approximate and do not establish future predictive performance.
"""

from dataclasses import dataclass
from math import ceil

import numpy as np


@dataclass(frozen=True)
class ReliabilityResult:
    observations: int
    block_length: int
    brier_improvement: float
    confidence_lower: float
    confidence_upper: float
    bootstrap_samples: int
    statistically_distinguishable_from_zero: bool


def block_bootstrap_brier_improvement(
    model_probabilities,
    benchmark_probabilities,
    actual_outcomes,
    horizon_days: int,
    step_days: int = 5,
    bootstrap_samples: int = 2000,
    confidence_level: float = 0.95,
    random_seed: int = 42,
) -> ReliabilityResult:
    """Estimate uncertainty in model-versus-benchmark Brier improvement.

    Positive improvement means the model has a lower Brier Score.

    Observations must be ordered chronologically and sampled at
    regular step_days intervals.

    The block length is at least ceil(horizon_days / step_days),
    to approximately preserve overlapping-outcome dependence.
    """

    model = np.asarray(model_probabilities, dtype=float)
    benchmark = np.asarray(benchmark_probabilities, dtype=float)
    actual = np.asarray(actual_outcomes, dtype=float)

    if (
        model.ndim != 1
        or benchmark.ndim != 1
        or actual.ndim != 1
    ):
        raise ValueError("Inputs must be one-dimensional.")

    if not (len(model) == len(benchmark) == len(actual)):
        raise ValueError("Input arrays must have equal lengths.")

    if len(model) < 30:
        raise ValueError("At least 30 observations are required.")

    if (
        not np.isfinite(model).all()
        or not np.isfinite(benchmark).all()
        or not np.isfinite(actual).all()
    ):
        raise ValueError("Inputs must contain only finite values.")

    if (
        ((model < 0) | (model > 1)).any()
        or ((benchmark < 0) | (benchmark > 1)).any()
    ):
        raise ValueError("Probabilities must be between 0 and 1.")

    if not np.isin(actual, [0, 1]).all():
        raise ValueError("Outcomes must be binary.")

    if (
        isinstance(horizon_days, bool)
        or not isinstance(horizon_days, int)
        or horizon_days < 1
    ):
        raise ValueError("horizon_days must be a positive integer.")

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

    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1.")

    n = len(actual)

    block_length = max(
        1,
        ceil(horizon_days / step_days),
    )

    if n < 3 * block_length:
        raise ValueError(
            "Insufficient observations for three bootstrap blocks."
        )

    model_losses = (model - actual) ** 2
    benchmark_losses = (benchmark - actual) ** 2

    improvement_series = benchmark_losses - model_losses

    observed_improvement = float(improvement_series.mean())

    rng = np.random.default_rng(random_seed)

    bootstrap_improvements = np.empty(
        bootstrap_samples,
        dtype=float,
    )

    blocks_needed = ceil(n / block_length)

    for sample in range(bootstrap_samples):
        starts = rng.integers(
            0,
            n,
            size=blocks_needed,
        )

        indices = np.concatenate(
            [
                (start + np.arange(block_length)) % n
                for start in starts
            ]
        )[:n]

        bootstrap_improvements[sample] = float(
            improvement_series[indices].mean()
        )

    alpha = 1.0 - confidence_level

    lower, upper = np.quantile(
        bootstrap_improvements,
        [alpha / 2, 1 - alpha / 2],
    )

    return ReliabilityResult(
        observations=n,
        block_length=block_length,
        brier_improvement=observed_improvement,
        confidence_lower=float(lower),
        confidence_upper=float(upper),
        bootstrap_samples=bootstrap_samples,
        statistically_distinguishable_from_zero=bool(
            lower > 0 or upper < 0
        ),
    )
