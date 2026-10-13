"""Integration tests for probability benchmark consistency."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app.forecasting.historical_benchmark import historical_up_probability
from app.forecasting.probability_benchmarks import historical_base_rate
from app.forecasting.research_data import ResearchDataResult
from app.forecasting.research_runner import run_research
from app.forecasting.research_universe import ResearchStock


@pytest.fixture
def prices():
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-01", periods=1200, freq="B")

    returns = rng.normal(0.0003, 0.015, size=1200)
    values = 100 * np.exp(np.cumsum(returns))

    return pd.Series(values, index=dates)


@pytest.mark.parametrize("horizon", [1, 5, 20, 60])
@pytest.mark.parametrize("forecast_index", [300, 600, 1000])
def test_base_rate_matches_existing_historical(
    prices,
    horizon,
    forecast_index,
):
    original = historical_up_probability(
        prices,
        forecast_index=forecast_index,
        horizon=horizon,
        minimum_samples=30,
    )

    new = historical_base_rate(
        prices,
        forecast_index=forecast_index,
        horizon_days=horizon,
        minimum_samples=30,
    )

    assert new.probability_up == pytest.approx(original)


def test_all_models_use_identical_validation_observations(prices):
    stock = ResearchStock("TEST", "Technology")

    data = ResearchDataResult(
        ticker="TEST",
        close=prices,
        status="Valid",
        observations=len(prices),
        start_date=str(prices.index[0].date()),
        end_date=str(prices.index[-1].date()),
        missing_prices=0,
        duplicate_dates=0,
        invalid_prices=0,
        error=None,
    )

    predictions = pd.DataFrame(
        {
            "Forecast Index": [500, 505, 510, 515],
            "Horizon": [5, 5, 5, 5],
            "Research Period": [
                "Training",
                "Validation",
                "Validation",
                "Test",
            ],
            "Actual Up": [1, 1, 0, 1],
            "Historical Probability": [0.5, 0.6, 0.4, 0.5],
            "ML Probability": [0.5, 0.8, 0.2, 0.5],
        }
    )

    with (
        patch(
            "app.forecasting.research_runner.download_research_prices",
            return_value=data,
        ),
        patch(
            "app.forecasting.research_runner.ml_walk_forward_predictions",
            return_value=predictions,
        ),
    ):
        result = run_research((stock,))

    assert set(result.scores["Model"]) == {
        "Neutral",
        "Base Rate",
        "Historical",
        "ML",
        "Ensemble",
    }

    assert len(result.scores) == 5
    assert (result.scores["N"] == 2).all()

    neutral = result.scores.loc[
        result.scores["Model"] == "Neutral"
    ].iloc[0]

    assert neutral["Brier"] == pytest.approx(0.25)
    assert neutral["Log Loss"] == pytest.approx(np.log(2))


def test_future_prices_do_not_change_base_rate(prices):
    original = historical_base_rate(
        prices,
        forecast_index=600,
        horizon_days=20,
    )

    changed_prices = prices.copy()
    changed_prices.iloc[601:] *= 100

    changed = historical_base_rate(
        changed_prices,
        forecast_index=600,
        horizon_days=20,
    )

    assert original == changed
