"""Tests for historical benchmark comparisons."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.regularization_benchmarks import (
    compare_regularization_benchmarks,
)


@pytest.fixture
def prices():
    rng = np.random.default_rng(42)
    returns = rng.normal(0.0005, 0.01, 500)
    return pd.Series(
        100 * np.exp(np.cumsum(returns)),
        index=pd.bdate_range("2020-01-01", periods=500),
    )


@pytest.fixture
def predictions():
    indices = np.arange(200, 400, 5)
    actual = (indices % 15 == 0).astype(int)

    return pd.DataFrame(
        {
            "Forecast Index": indices,
            "Horizon": 5,
            "Research Period": np.where(
                indices < 300,
                "Training",
                "Validation",
            ),
            "Actual Up": actual,
            "ML C=0.001": np.full(len(indices), 0.5),
            "ML C=0.1": np.full(len(indices), 0.6),
        }
    )


def evaluate(prices, predictions):
    return compare_regularization_benchmarks(
        close_prices=prices,
        predictions=predictions,
        candidate_columns=("ML C=0.001", "ML C=0.1"),
        minimum_samples=30,
    )


def test_expected_models_present(prices, predictions):
    result = evaluate(prices, predictions)

    assert set(result["Model"]) == {
        "Neutral",
        "Historical Base Rate",
        "ML C=0.001",
        "ML C=0.1",
    }


def test_only_validation_observations_scored(prices, predictions):
    result = evaluate(prices, predictions)

    assert result["N"].eq(20).all()


def test_all_models_use_identical_sample_counts(prices, predictions):
    result = evaluate(prices, predictions)

    assert result["N"].nunique() == 1


def test_neutral_brier_is_quarter(prices, predictions):
    result = evaluate(prices, predictions)

    neutral = result.loc[result["Model"].eq("Neutral")]

    assert neutral.iloc[0]["Brier"] == pytest.approx(0.25)


def test_neutral_probability_has_zero_variation(prices, predictions):
    result = evaluate(prices, predictions)

    neutral = result.loc[result["Model"].eq("Neutral")]

    assert neutral.iloc[0]["Probability Std"] == pytest.approx(0)


def test_future_prices_do_not_change_historical_benchmark(
    prices,
    predictions,
):
    original = evaluate(prices, predictions)

    modified_prices = prices.copy()

    modified_prices.iloc[400:] *= 100

    changed = evaluate(modified_prices, predictions)

    historical_original = original.loc[
        original["Model"].eq("Historical Base Rate")
    ].reset_index(drop=True)

    historical_changed = changed.loc[
        changed["Model"].eq("Historical Base Rate")
    ].reset_index(drop=True)

    pd.testing.assert_frame_equal(
        historical_original,
        historical_changed,
    )


def test_training_outcomes_do_not_affect_validation_scores(
    prices,
    predictions,
):
    original = evaluate(prices, predictions)

    modified = predictions.copy()
    training = modified["Research Period"].eq("Training")

    modified.loc[training, "Actual Up"] = (
        1 - modified.loc[training, "Actual Up"]
    )

    changed = evaluate(prices, modified)

    pd.testing.assert_frame_equal(original, changed)


def test_reserved_test_rows_rejected(prices, predictions):
    modified = predictions.copy()
    modified.loc[0, "Research Period"] = "Test"

    with pytest.raises(ValueError, match="Reserved test"):
        evaluate(prices, modified)


def test_unknown_research_period_rejected(prices, predictions):
    modified = predictions.copy()
    modified.loc[0, "Research Period"] = "Unknown"

    with pytest.raises(ValueError, match="Unknown"):
        evaluate(prices, modified)


def test_duplicate_forecast_keys_rejected(prices, predictions):
    modified = pd.concat(
        [predictions, predictions.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate"):
        evaluate(prices, modified)


def test_missing_candidate_rejected(prices, predictions):
    with pytest.raises(ValueError, match="Missing columns"):
        compare_regularization_benchmarks(
            close_prices=prices,
            predictions=predictions,
            candidate_columns=("Missing",),
        )


def test_empty_candidate_list_rejected(prices, predictions):
    with pytest.raises(ValueError, match="At least one"):
        compare_regularization_benchmarks(
            close_prices=prices,
            predictions=predictions,
            candidate_columns=(),
        )


def test_duplicate_candidate_names_rejected(prices, predictions):
    with pytest.raises(ValueError, match="unique"):
        compare_regularization_benchmarks(
            close_prices=prices,
            predictions=predictions,
            candidate_columns=("ML C=0.1", "ML C=0.1"),
        )


def test_no_validation_rows_rejected(prices, predictions):
    modified = predictions.copy()
    modified["Research Period"] = "Training"

    with pytest.raises(ValueError, match="No validation"):
        evaluate(prices, modified)


@pytest.mark.parametrize(
    "invalid",
    [2, -1, float("nan"), float("inf")],
)
def test_invalid_validation_outcomes_rejected(
    prices,
    predictions,
    invalid,
):
    modified = predictions.copy()
    modified["Actual Up"] = modified["Actual Up"].astype(float)
    modified.loc[
        modified["Research Period"].eq("Validation"),
        "Actual Up",
    ] = invalid

    with pytest.raises(ValueError):
        evaluate(prices, modified)


@pytest.mark.parametrize(
    "invalid",
    [-0.1, 1.1, float("nan"), float("inf")],
)
def test_invalid_candidate_probabilities_rejected(
    prices,
    predictions,
    invalid,
):
    modified = predictions.copy()

    modified.loc[
        modified["Research Period"].eq("Validation"),
        "ML C=0.1",
    ] = invalid

    with pytest.raises(ValueError):
        evaluate(prices, modified)


def test_input_predictions_not_modified(prices, predictions):
    original = predictions.copy(deep=True)

    evaluate(prices, predictions)

    pd.testing.assert_frame_equal(predictions, original)


def test_input_prices_not_modified(prices, predictions):
    original = prices.copy(deep=True)

    evaluate(prices, predictions)

    pd.testing.assert_series_equal(prices, original)


def test_summary_scores_are_finite(prices, predictions):
    result = evaluate(prices, predictions)

    assert np.isfinite(
        result[["Brier", "Log Loss", "ECE"]].to_numpy()
    ).all()


def test_results_sorted_by_horizon_and_brier(prices, predictions):
    result = evaluate(prices, predictions)

    assert result["Brier"].is_monotonic_increasing
