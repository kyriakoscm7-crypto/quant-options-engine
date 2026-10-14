"""Evaluate whether historical ranking scores predict future returns."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = {
    "date",
    "ticker",
    "score",
    "future_return",
}


def evaluate_prediction_accuracy(
    predictions: pd.DataFrame,
    top_fraction: float = 0.2,
) -> dict:
    """Evaluate historical cross-sectional ranking accuracy.

    Each row must represent a historical prediction and its
    subsequently observed return.

    Returns are expressed as decimals:
        0.10 means +10%.
       -0.05 means -5%.
    """

    missing = REQUIRED_COLUMNS - set(predictions.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    if not 0 < top_fraction <= 0.5:
        raise ValueError(
            "top_fraction must be greater than 0 and at most 0.5."
        )

    data = predictions.copy()

    data["score"] = pd.to_numeric(
        data["score"],
        errors="coerce",
    )

    data["future_return"] = pd.to_numeric(
        data["future_return"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["date", "ticker", "score", "future_return"]
    )

    if data.empty:
        raise ValueError("No valid predictions available.")

    correlations = []
    spreads = []
    hit_rates = []
    evaluated_dates = 0

    for _, group in data.groupby("date"):
        group = group.sort_values(
            ["score", "ticker"],
            ascending=[False, True],
        )

        if len(group) < 5:
            continue

        count = max(
            1,
            int(len(group) * top_fraction),
        )

        top = group.head(count)
        bottom = group.tail(count)

        correlation = group["score"].corr(
            group["future_return"],
            method="spearman",
        )

        if pd.notna(correlation):
            correlations.append(float(correlation))

        top_return = float(top["future_return"].mean())
        bottom_return = float(bottom["future_return"].mean())
        universe_return = float(group["future_return"].mean())

        spreads.append(top_return - bottom_return)

        hit_rates.append(
            float(top_return > universe_return)
        )

        evaluated_dates += 1

    if not evaluated_dates:
        raise ValueError(
            "Insufficient cross-sectional predictions."
        )

    return {
        "prediction_rows": len(data),
        "evaluation_dates": evaluated_dates,
        "mean_spearman_correlation": (
            sum(correlations) / len(correlations)
            if correlations
            else float("nan")
        ),
        "mean_top_bottom_spread": (
            sum(spreads) / len(spreads)
        ),
        "top_group_hit_rate": (
            sum(hit_rates) / len(hit_rates)
        ),
    }
