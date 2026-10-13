"""Leakage-conscious aligned predictions for three forecasting models.

Research-only. Final-test prices are excluded from development evaluation.
"""

import numpy as np
import pandas as pd

from app.forecasting.historical_benchmark import historical_up_probability
from app.forecasting.research_splits import (
    assign_research_periods,
    create_research_split,
)
from app.forecasting.uncertainty_aware import uncertainty_aware_forecast
from app.forecasting.walk_forward import walk_forward_predictions


def generate_aligned_predictions(
    close_prices: pd.Series,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    training_days: int = 252,
    step: int = 5,
) -> pd.DataFrame:
    """Return aligned historical predictions from three models.

    Every row represents the same forecast origin, horizon, and
    realized outcome for all three models.

    The reserved final-test period is never passed to the forecasters.
    """

    if not isinstance(close_prices, pd.Series):
        raise ValueError("close_prices must be a pandas Series.")

    if not horizons or any(
        isinstance(h, bool) or not isinstance(h, int) or h < 1
        for h in horizons
    ):
        raise ValueError("Horizons must be positive integers.")

    if (
        isinstance(training_days, bool)
        or not isinstance(training_days, int)
        or training_days < 120
    ):
        raise ValueError("training_days must be at least 120.")

    if (
        isinstance(step, bool)
        or not isinstance(step, int)
        or step < 1
    ):
        raise ValueError("step must be a positive integer.")

    prices = close_prices.to_numpy(dtype=float)

    if (
        len(prices) < 300
        or not np.isfinite(prices).all()
        or np.any(prices <= 0)
    ):
        raise ValueError("Prices must be sufficient, finite, and positive.")

    split = create_research_split(
        total_observations=len(close_prices),
        embargo_days=max(horizons),
    )

    development_prices = close_prices.iloc[:split.validation_end]

    original_predictions = walk_forward_predictions(
        development_prices,
        horizons=horizons,
        training_days=training_days,
        step=step,
    )

    assigned = assign_research_periods(
        original_predictions,
        split,
    )

    assigned = assigned[
        assigned["Research Period"].isin(["Training", "Validation"])
    ]

    records = []

    for row in assigned.to_dict("records"):
        forecast_index = int(row["Forecast Index"])
        horizon = int(row["Horizon"])

        historical_prices = development_prices.iloc[:forecast_index + 1]

        uncertainty_probability = uncertainty_aware_forecast(
            historical_prices,
            horizons=(horizon,),
            lookback=training_days,
            minimum_observations=120,
        )[0].probability_up

        historical_probability = historical_up_probability(
            development_prices,
            forecast_index=forecast_index,
            horizon=horizon,
        )

        records.append(
            {
                "Forecast Index": forecast_index,
                "Horizon": horizon,
                "Research Period": row["Research Period"],
                "Actual Up": int(row["Actual Up"]),
                "Original Probability": float(row["Probability Up"]),
                "Uncertainty Probability": float(
                    uncertainty_probability
                ),
                "Historical Probability": float(
                    historical_probability
                ),
            }
        )

    columns = [
        "Forecast Index",
        "Horizon",
        "Research Period",
        "Actual Up",
        "Original Probability",
        "Uncertainty Probability",
        "Historical Probability",
    ]

    if not records:
        return pd.DataFrame(columns=columns)

    result = pd.DataFrame(records, columns=columns)

    return result.sort_values(
        ["Horizon", "Forecast Index"]
    ).reset_index(drop=True)
