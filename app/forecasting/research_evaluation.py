"""Chronological evaluation of probabilistic stock forecasts.

Research-only diagnostics.

Final-test results must remain untouched during model development.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.forecasting.research_splits import (
    ResearchSplit,
    assign_research_periods,
    create_research_split,
)
from app.forecasting.walk_forward import walk_forward_predictions


@dataclass(frozen=True)
class PeriodEvaluation:
    period: str
    horizon_days: int
    predictions: int
    brier_score: float
    directional_accuracy: float
    average_probability: float
    observed_up_frequency: float


def evaluate_research_periods(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    training_days: int = 252,
    step: int = 5,
    include_final_test: bool = False,
) -> tuple[ResearchSplit, list[PeriodEvaluation]]:
    """Evaluate forecasts within chronological research periods.

    By default, final-test results are excluded from the report.

    Predictions use the existing walk-forward baseline, which
    estimates parameters using historical prices only.
    """

    if not isinstance(include_final_test, bool):
        raise ValueError("include_final_test must be a boolean.")

    split = create_research_split(
        total_observations=len(close_prices),
        embargo_days=max(horizons),
    )

    # During development, do not expose final-test prices
    # to the forecasting engine at all.
    evaluation_prices = (
        close_prices
        if include_final_test
        else close_prices.iloc[: split.validation_end]
    )

    predictions = walk_forward_predictions(
        evaluation_prices,
        horizons=horizons,
        training_days=training_days,
        step=step,
    )

    predictions = assign_research_periods(
        predictions,
        split,
    )

    allowed_periods = ["Training", "Validation"]

    if include_final_test:
        allowed_periods.append("Test")

    predictions = predictions[
        predictions["Research Period"].isin(allowed_periods)
    ]

    results = []

    for (period, horizon), group in predictions.groupby(
        ["Research Period", "Horizon"]
    ):
        probabilities = group["Probability Up"].to_numpy(dtype=float)
        actual = group["Actual Up"].to_numpy(dtype=float)

        results.append(
            PeriodEvaluation(
                period=str(period),
                horizon_days=int(horizon),
                predictions=len(group),
                brier_score=float(
                    np.mean((probabilities - actual) ** 2)
                ),
                directional_accuracy=float(
                    np.mean((probabilities > 0.5) == actual)
                ),
                average_probability=float(probabilities.mean()),
                observed_up_frequency=float(actual.mean()),
            )
        )

    return split, results
