"""Tests for the multi-stock research runner."""

from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app.forecasting.research_data import ResearchDataResult
from app.forecasting.research_runner import (
    calculate_probability_scores,
    run_research,
)
from app.forecasting.research_universe import ResearchStock


def make_valid_data(ticker="TEST"):
    dates = pd.date_range("2020-01-01", periods=1200, freq="B")
    prices = pd.Series(
        np.linspace(100, 200, 1200),
        index=dates,
    )

    return ResearchDataResult(
        ticker=ticker,
        close=prices,
        status="Valid",
        observations=1200,
        start_date="2020-01-01",
        end_date="2024-08-06",
        missing_prices=0,
        duplicate_dates=0,
        invalid_prices=0,
        error=None,
    )


def make_predictions():
    return pd.DataFrame(
        {
            "Forecast Index": [400, 405, 410, 415],
            "Horizon": [5, 5, 5, 5],
            "Research Period": [
                "Training",
                "Validation",
                "Validation",
                "Test",
            ],
            "Actual Up": [1, 1, 0, 1],
            "Historical Probability": [0.1, 0.6, 0.4, 0.1],
            "ML Probability": [0.1, 0.8, 0.2, 0.1],
        }
    )


def test_perfect_predictions_have_zero_brier():
    brier, _ = calculate_probability_scores(
        np.array([1, 0, 1]),
        np.array([1, 0, 1]),
    )

    assert brier == pytest.approx(0.0)


def test_brier_score_calculation():
    brier, _ = calculate_probability_scores(
        np.array([1, 0]),
        np.array([0.8, 0.2]),
    )

    assert brier == pytest.approx(0.04)


def test_log_loss_calculation():
    _, log_loss = calculate_probability_scores(
        np.array([1, 0]),
        np.array([0.8, 0.2]),
    )

    assert log_loss == pytest.approx(-np.log(0.8))


def test_neutral_forecast_scores():
    brier, log_loss = calculate_probability_scores(
        np.array([1, 0]),
        np.array([0.5, 0.5]),
    )

    assert brier == pytest.approx(0.25)
    assert log_loss == pytest.approx(np.log(2))


@pytest.mark.parametrize(
    "bad_probability",
    [-0.1, 1.1, np.nan, np.inf],
)
def test_invalid_probabilities_rejected(bad_probability):
    with pytest.raises(ValueError):
        calculate_probability_scores(
            np.array([1, 0]),
            np.array([bad_probability, 0.5]),
        )


def test_nonbinary_outcomes_rejected():
    with pytest.raises(ValueError):
        calculate_probability_scores(
            np.array([1, 0.5]),
            np.array([0.8, 0.2]),
        )


def test_mismatched_lengths_rejected():
    with pytest.raises(ValueError):
        calculate_probability_scores(
            np.array([1, 0]),
            np.array([0.8]),
        )


def test_empty_inputs_rejected():
    with pytest.raises(ValueError):
        calculate_probability_scores(
            np.array([]),
            np.array([]),
        )


def test_only_validation_rows_are_scored():
    stock = ResearchStock("TEST", "Technology")

    with (
        patch(
            "app.forecasting.research_runner.download_research_prices",
            return_value=make_valid_data(),
        ),
        patch(
            "app.forecasting.research_runner.ml_walk_forward_predictions",
            return_value=make_predictions(),
        ),
    ):
        result = run_research((stock,))

    assert len(result.scores) == 5
    assert set(result.scores["Model"]) == {
        "Neutral",
        "Base Rate",
        "Historical",
        "ML",
        "Ensemble",
    }
    assert (result.scores["N"] == 2).all()

    neutral = result.scores.loc[
        result.scores["Model"] == "Neutral"
    ].iloc[0]

    assert neutral["Brier"] == pytest.approx(0.25)
    assert neutral["Log Loss"] == pytest.approx(np.log(2))

    historical = result.scores.loc[
        result.scores["Model"] == "Historical"
    ].iloc[0]

    assert historical["Brier"] == pytest.approx(0.16)


def test_ensemble_scores_are_correct():
    stock = ResearchStock("TEST", "Technology")

    with (
        patch(
            "app.forecasting.research_runner.download_research_prices",
            return_value=make_valid_data(),
        ),
        patch(
            "app.forecasting.research_runner.ml_walk_forward_predictions",
            return_value=make_predictions(),
        ),
    ):
        result = run_research((stock,), ml_weight=0.25)

    ensemble = result.scores.loc[
        result.scores["Model"] == "Ensemble"
    ].iloc[0]

    assert ensemble["Brier"] == pytest.approx(0.1225)


def test_download_failure_is_recorded():
    stock = ResearchStock("TEST", "Technology")

    failed_data = ResearchDataResult(
        ticker="TEST",
        close=None,
        status="Download failed",
        observations=0,
        start_date=None,
        end_date=None,
        missing_prices=0,
        duplicate_dates=0,
        invalid_prices=0,
        error="Network error",
    )

    with patch(
        "app.forecasting.research_runner.download_research_prices",
        return_value=failed_data,
    ):
        result = run_research((stock,))

    assert result.scores.empty
    assert result.data_quality.iloc[0]["Status"] == "Download failed"


def test_forecast_failure_is_recorded():
    stock = ResearchStock("TEST", "Technology")

    with (
        patch(
            "app.forecasting.research_runner.download_research_prices",
            return_value=make_valid_data(),
        ),
        patch(
            "app.forecasting.research_runner.ml_walk_forward_predictions",
            side_effect=RuntimeError("Model failed"),
        ),
    ):
        result = run_research((stock,))

    assert result.scores.empty
    assert result.data_quality.iloc[0]["Status"] == "Forecast failed"
    assert "Model failed" in result.data_quality.iloc[0]["Error"]


def test_empty_stock_universe_rejected():
    with pytest.raises(ValueError):
        run_research(())


def test_invalid_horizon_rejected():
    with pytest.raises(ValueError):
        run_research(
            (ResearchStock("TEST", "Technology"),),
            horizons=(0,),
        )


def test_invalid_step_rejected():
    with pytest.raises(ValueError):
        run_research(
            (ResearchStock("TEST", "Technology"),),
            step=0,
        )
