"""Tests for calibration research integration."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.calibration_research import analyze_research_predictions
from app.forecasting.probability_benchmarks import historical_base_rate


@pytest.fixture
def prices():
    rng = np.random.default_rng(42)
    dates = pd.date_range("2015-01-01", periods=1200, freq="B")
    returns = rng.normal(0.0003, 0.015, 1200)

    return pd.Series(
        100 * np.exp(np.cumsum(returns)),
        index=dates,
    )


@pytest.fixture
def predictions():
    return pd.DataFrame(
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


def test_all_five_models_present(prices, predictions):
    result = analyze_research_predictions(prices, predictions)

    assert set(result["Model"]) == {
        "Neutral",
        "Base Rate",
        "Historical",
        "ML",
        "Ensemble",
    }


def test_only_validation_observations_used(prices, predictions):
    result = analyze_research_predictions(prices, predictions)

    assert (result["N"] == 2).all()


def test_neutral_brier_score(prices, predictions):
    result = analyze_research_predictions(prices, predictions)

    neutral = result.loc[result["Model"] == "Neutral"].iloc[0]

    assert neutral["Brier"] == pytest.approx(0.25)
    assert neutral["Log Loss"] == pytest.approx(np.log(2))


def test_historical_brier_score(prices, predictions):
    result = analyze_research_predictions(prices, predictions)

    historical = result.loc[
        result["Model"] == "Historical"
    ].iloc[0]

    assert historical["Brier"] == pytest.approx(0.16)


def test_ml_brier_score(prices, predictions):
    result = analyze_research_predictions(prices, predictions)

    ml = result.loc[result["Model"] == "ML"].iloc[0]

    assert ml["Brier"] == pytest.approx(0.04)


def test_ensemble_brier_score(prices, predictions):
    result = analyze_research_predictions(prices, predictions)

    ensemble = result.loc[
        result["Model"] == "Ensemble"
    ].iloc[0]

    assert ensemble["Brier"] == pytest.approx(0.1225)


def test_base_rate_matches_independent_calculation(prices, predictions):
    result = analyze_research_predictions(prices, predictions)

    base_rate = result.loc[
        result["Model"] == "Base Rate"
    ].iloc[0]

    probabilities = np.array(
        [
            historical_base_rate(
                prices,
                forecast_index=index,
                horizon_days=5,
            ).probability_up
            for index in [505, 510]
        ]
    )

    expected = np.mean(
        (probabilities - np.array([1, 0])) ** 2
    )

    assert base_rate["Brier"] == pytest.approx(expected)


def test_training_predictions_do_not_affect_results(prices, predictions):
    original = analyze_research_predictions(prices, predictions)

    modified = predictions.copy()
    modified.loc[0, "ML Probability"] = 0.99
    modified.loc[0, "Actual Up"] = 0

    changed = analyze_research_predictions(prices, modified)

    pd.testing.assert_frame_equal(original, changed)


def test_test_predictions_do_not_affect_results(prices, predictions):
    original = analyze_research_predictions(prices, predictions)

    modified = predictions.copy()
    modified.loc[3, "ML Probability"] = 0.01
    modified.loc[3, "Actual Up"] = 0

    changed = analyze_research_predictions(prices, modified)

    pd.testing.assert_frame_equal(original, changed)


def test_future_prices_do_not_affect_results(prices, predictions):
    original = analyze_research_predictions(prices, predictions)

    modified_prices = prices.copy()
    modified_prices.iloc[511:] *= 10

    changed = analyze_research_predictions(
        modified_prices,
        predictions,
    )

    pd.testing.assert_frame_equal(original, changed)


def test_missing_columns_rejected(prices, predictions):
    invalid = predictions.drop(columns=["ML Probability"])

    with pytest.raises(ValueError, match="Missing prediction columns"):
        analyze_research_predictions(prices, invalid)


@pytest.mark.parametrize("weight", [-0.1, 1.1])
def test_invalid_ensemble_weights_rejected(prices, predictions, weight):
    with pytest.raises(ValueError):
        analyze_research_predictions(
            prices,
            predictions,
            ml_weight=weight,
        )


def test_different_ensemble_weights_change_scores(prices, predictions):
    first = analyze_research_predictions(
        prices,
        predictions,
        ml_weight=0.0,
    )

    second = analyze_research_predictions(
        prices,
        predictions,
        ml_weight=1.0,
    )

    first_ensemble = first.loc[
        first["Model"] == "Ensemble", "Brier"
    ].iloc[0]

    second_ensemble = second.loc[
        second["Model"] == "Ensemble", "Brier"
    ].iloc[0]

    assert first_ensemble != second_ensemble


def test_roc_auc_values_are_valid(prices, predictions):
    result = analyze_research_predictions(prices, predictions)

    assert result["ROC AUC"].between(0, 1).all()


def test_input_predictions_are_not_modified(prices, predictions):
    original = predictions.copy(deep=True)

    analyze_research_predictions(prices, predictions)

    pd.testing.assert_frame_equal(predictions, original)
