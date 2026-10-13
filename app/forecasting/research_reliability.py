"""Statistical reliability analysis for multi-stock validation forecasts."""

import numpy as np
import pandas as pd

from app.forecasting.statistical_reliability import (
    block_bootstrap_brier_improvement,
)

COLUMNS = [
    "Stock",
    "Horizon",
    "Model",
    "Benchmark",
    "N",
    "Brier Improvement",
    "CI Lower",
    "CI Upper",
    "Evidence",
]


def analyze_research_reliability(
    predictions: pd.DataFrame,
    step_days: int = 5,
    bootstrap_samples: int = 2000,
    random_seed: int = 42,
) -> pd.DataFrame:
    """Compare validation forecasts using moving-block bootstrap intervals."""

    required = {
        "Stock",
        "Forecast Index",
        "Horizon",
        "Research Period",
        "Actual Up",
        "Historical Probability",
        "ML Probability",
        "Ensemble Probability",
    }

    missing = required - set(predictions.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if predictions["Research Period"].eq("Test").any():
        raise ValueError("Reserved test observations are not allowed.")

    validation = predictions.loc[
        predictions["Research Period"].eq("Validation")
    ].copy()

    rows = []

    for (stock, horizon), group in validation.groupby(
        ["Stock", "Horizon"]
    ):
        group = group.sort_values("Forecast Index")

        actual = group["Actual Up"].to_numpy(dtype=float)

        benchmark = group["Historical Probability"].to_numpy(
            dtype=float
        )

        models = {
            "ML": group["ML Probability"].to_numpy(dtype=float),
            "Ensemble": group["Ensemble Probability"].to_numpy(
                dtype=float
            ),
        }

        for model_name, probabilities in models.items():
            try:
                report = block_bootstrap_brier_improvement(
                    model_probabilities=probabilities,
                    benchmark_probabilities=benchmark,
                    actual_outcomes=actual,
                    horizon_days=int(horizon),
                    step_days=step_days,
                    bootstrap_samples=bootstrap_samples,
                    random_seed=random_seed,
                )

                if report.confidence_lower > 0:
                    evidence = "Model advantage"
                elif report.confidence_upper < 0:
                    evidence = "Benchmark advantage"
                else:
                    evidence = "Inconclusive"

                rows.append(
                    {
                        "Stock": stock,
                        "Horizon": int(horizon),
                        "Model": model_name,
                        "Benchmark": "Historical",
                        "N": report.observations,
                        "Brier Improvement": report.brier_improvement,
                        "CI Lower": report.confidence_lower,
                        "CI Upper": report.confidence_upper,
                        "Evidence": evidence,
                    }
                )

            except ValueError as exc:
                if (
                    "At least 30 observations" not in str(exc)
                    and "Insufficient observations for three bootstrap blocks"
                    not in str(exc)
                ):
                    raise

                rows.append(
                    {
                        "Stock": stock,
                        "Horizon": int(horizon),
                        "Model": model_name,
                        "Benchmark": "Historical",
                        "N": len(group),
                        "Brier Improvement": float(
                            np.mean(
                                (benchmark - actual) ** 2
                                - (probabilities - actual) ** 2
                            )
                        ),
                        "CI Lower": np.nan,
                        "CI Upper": np.nan,
                        "Evidence": "Insufficient evidence",
                    }
                )

    return pd.DataFrame(rows, columns=COLUMNS).sort_values(
        ["Stock", "Horizon", "Model"]
    ).reset_index(drop=True)
