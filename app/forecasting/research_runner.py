"""Multi-stock forecasting research and validation engine."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.forecasting.ml_walk_forward import ml_walk_forward_predictions
from app.forecasting.probability_benchmarks import (
    historical_base_rate,
    neutral_probability,
)
from app.forecasting.research_data import download_research_prices
from app.forecasting.research_universe import ResearchStock
from app.forecasting.shrinkage_ensemble import add_ensemble_predictions


@dataclass(frozen=True)
class ResearchRunResult:
    scores: pd.DataFrame
    data_quality: pd.DataFrame


def calculate_probability_scores(
    actual: np.ndarray,
    probability: np.ndarray,
) -> tuple[float, float]:
    """Calculate Brier Score and binary log loss."""

    actual = np.asarray(actual, dtype=float)
    probability = np.asarray(probability, dtype=float)

    if actual.ndim != 1 or probability.ndim != 1:
        raise ValueError("Inputs must be one-dimensional.")

    if len(actual) == 0 or len(actual) != len(probability):
        raise ValueError("Inputs must be nonempty and equal length.")

    if not np.isfinite(actual).all():
        raise ValueError("Actual outcomes must be finite.")

    if not np.isin(actual, [0.0, 1.0]).all():
        raise ValueError("Actual outcomes must be binary.")

    if not np.isfinite(probability).all():
        raise ValueError("Probabilities must be finite.")

    if np.any((probability < 0) | (probability > 1)):
        raise ValueError("Probabilities must be between zero and one.")

    brier = float(np.mean((probability - actual) ** 2))

    safe = np.clip(probability, 1e-12, 1 - 1e-12)

    log_loss = float(
        -np.mean(
            actual * np.log(safe)
            + (1 - actual) * np.log1p(-safe)
        )
    )

    return brier, log_loss


def run_research(
    stocks: tuple[ResearchStock, ...],
    years: int = 15,
    horizons: tuple[int, ...] = (1, 5, 20, 60),
    step: int = 5,
    ml_weight: float = 0.25,
) -> ResearchRunResult:
    """Evaluate forecasting models on validation observations only."""

    if not stocks:
        raise ValueError("At least one research stock is required.")

    if not horizons or any(h <= 0 for h in horizons):
        raise ValueError("Horizons must contain positive integers.")

    if step < 1:
        raise ValueError("Step must be positive.")

    score_rows = []
    quality_rows = []

    for stock in stocks:
        print(f"Evaluating {stock.ticker} ({stock.sector})...", flush=True)

        data = download_research_prices(
            ticker=stock.ticker,
            years=years,
            minimum_observations=1000,
        )

        quality = {
            "Stock": stock.ticker,
            "Sector": stock.sector,
            "Status": data.status,
            "Observations": data.observations,
            "Start": data.start_date,
            "End": data.end_date,
            "Missing Prices": data.missing_prices,
            "Duplicate Dates": data.duplicate_dates,
            "Invalid Prices": data.invalid_prices,
            "Error": data.error,
        }

        if data.close is None:
            quality_rows.append(quality)
            continue

        try:
            predictions = ml_walk_forward_predictions(
                data.close,
                horizons=horizons,
                training_window=756,
                step=step,
                regularization_c=0.1,
            )

            predictions = add_ensemble_predictions(
                predictions,
                ml_weight=ml_weight,
            )

            validation = predictions.loc[
                predictions["Research Period"] == "Validation"
            ]

            if validation.empty:
                raise ValueError("No validation predictions produced.")

            stock_score_rows = []

            for horizon, group in validation.groupby("Horizon"):
                actual = group["Actual Up"].to_numpy(dtype=float)

                neutral = np.full(
                    len(group),
                    neutral_probability(),
                    dtype=float,
                )

                base_rate = np.array(
                    [
                        historical_base_rate(
                            close_prices=data.close,
                            forecast_index=int(forecast_index),
                            horizon_days=int(horizon),
                            minimum_samples=30,
                        ).probability_up
                        for forecast_index in group["Forecast Index"]
                    ],
                    dtype=float,
                )

                probabilities = {
                    "Neutral": neutral,
                    "Base Rate": base_rate,
                    "Historical": group[
                        "Historical Probability"
                    ].to_numpy(dtype=float),
                    "ML": group[
                        "ML Probability"
                    ].to_numpy(dtype=float),
                    "Ensemble": group[
                        "Ensemble Probability"
                    ].to_numpy(dtype=float),
                }

                for model, probability in probabilities.items():
                    brier, log_loss = calculate_probability_scores(
                        actual,
                        probability,
                    )

                    stock_score_rows.append(
                        {
                            "Stock": stock.ticker,
                            "Sector": stock.sector,
                            "Horizon": int(horizon),
                            "Model": model,
                            "N": len(group),
                            "Brier": brier,
                            "Log Loss": log_loss,
                        }
                    )

            score_rows.extend(stock_score_rows)

            quality_rows.append(quality)

        except Exception as exc:
            quality["Status"] = "Forecast failed"
            quality["Error"] = f"{type(exc).__name__}: {exc}"
            quality_rows.append(quality)

    return ResearchRunResult(
        scores=pd.DataFrame(
            score_rows,
            columns=[
                "Stock",
                "Sector",
                "Horizon",
                "Model",
                "N",
                "Brier",
                "Log Loss",
            ],
        ),
        data_quality=pd.DataFrame(
            quality_rows,
            columns=[
                "Stock",
                "Sector",
                "Status",
                "Observations",
                "Start",
                "End",
                "Missing Prices",
                "Duplicate Dates",
                "Invalid Prices",
                "Error",
            ],
        ),
    )
