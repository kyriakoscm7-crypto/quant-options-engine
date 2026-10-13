"""Tests for aligned three-model historical predictions."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.aligned_predictions import generate_aligned_predictions
from app.forecasting.research_splits import create_research_split
from app.forecasting.walk_forward import walk_forward_predictions


def make_prices(n=1200, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.015, n - 1)
    return pd.Series(100 * np.exp(np.r_[0.0, np.cumsum(returns)]))


def test_predictions_are_generated():
    result = generate_aligned_predictions(
        make_prices(),
        horizons=(1, 5, 20, 60),
    )

    assert not result.empty
    assert set(result["Horizon"]) == {1, 5, 20, 60}


def test_only_development_periods_are_included():
    result = generate_aligned_predictions(
        make_prices(),
        horizons=(5,),
    )

    assert set(result["Research Period"]) == {
        "Training",
        "Validation",
    }


def test_all_model_probabilities_are_valid():
    result = generate_aligned_predictions(
        make_prices(),
        horizons=(1, 5, 20, 60),
    )

    columns = [
        "Original Probability",
        "Uncertainty Probability",
        "Historical Probability",
    ]

    for column in columns:
        assert result[column].notna().all()
        assert result[column].between(0, 1).all()


def test_actual_outcomes_are_binary():
    result = generate_aligned_predictions(
        make_prices(),
        horizons=(5,),
    )

    assert set(result["Actual Up"]).issubset({0, 1})


def test_original_predictions_match_walk_forward():
    prices = make_prices()

    result = generate_aligned_predictions(
        prices,
        horizons=(5,),
    )

    split = create_research_split(
        len(prices),
        embargo_days=5,
    )

    development_prices = prices.iloc[:split.validation_end]

    original = walk_forward_predictions(
        development_prices,
        horizons=(5,),
        training_days=252,
        step=5,
    )

    expected = original.set_index(
        ["Forecast Index", "Horizon"]
    )["Probability Up"]

    actual = result.set_index(
        ["Forecast Index", "Horizon"]
    )["Original Probability"]

    pd.testing.assert_series_equal(
        actual.sort_index(),
        expected.loc[actual.index].sort_index().rename(
            "Original Probability"
        ),
    )


def test_final_test_prices_cannot_change_predictions():
    prices = make_prices()

    original = generate_aligned_predictions(
        prices,
        horizons=(5, 20),
    )

    modified = prices.copy()

    split = create_research_split(
        len(prices),
        embargo_days=20,
    )

    modified.iloc[split.validation_end:] *= 10

    updated = generate_aligned_predictions(
        modified,
        horizons=(5, 20),
    )

    pd.testing.assert_frame_equal(original, updated)


def test_results_are_deterministic():
    prices = make_prices()

    first = generate_aligned_predictions(
        prices,
        horizons=(5,),
    )

    second = generate_aligned_predictions(
        prices,
        horizons=(5,),
    )

    pd.testing.assert_frame_equal(first, second)


def test_predictions_are_sorted():
    result = generate_aligned_predictions(
        make_prices(),
        horizons=(1, 5, 20),
    )

    expected = result.sort_values(
        ["Horizon", "Forecast Index"]
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(result, expected)


def test_no_duplicate_forecast_origins():
    result = generate_aligned_predictions(
        make_prices(),
        horizons=(1, 5, 20, 60),
    )

    assert not result.duplicated(
        ["Forecast Index", "Horizon"]
    ).any()


@pytest.mark.parametrize("bad_horizon", [0, -1, 1.5, True])
def test_invalid_horizons_rejected(bad_horizon):
    with pytest.raises(ValueError):
        generate_aligned_predictions(
            make_prices(),
            horizons=(bad_horizon,),
        )


@pytest.mark.parametrize("bad_value", [0, -5, np.nan, np.inf])
def test_invalid_prices_rejected(bad_value):
    prices = make_prices()
    prices.iloc[100] = bad_value

    with pytest.raises(ValueError):
        generate_aligned_predictions(prices)
