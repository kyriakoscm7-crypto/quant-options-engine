"""Tests for chronological machine-learning walk-forward predictions."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.ml_walk_forward import ml_walk_forward_predictions
from app.forecasting.research_splits import create_research_split


def make_prices(n=850, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.015, n - 1)
    return pd.Series(100 * np.exp(np.r_[0.0, np.cumsum(returns)]))


def run_forecast(prices=None, horizons=(5,)):
    if prices is None:
        prices = make_prices()

    return ml_walk_forward_predictions(
        prices,
        horizons=horizons,
        training_window=300,
        step=20,
    )


def test_predictions_are_generated():
    result = run_forecast()

    assert not result.empty
    assert set(result["Horizon"]) == {5}


def test_probabilities_are_valid():
    result = run_forecast()

    assert result["ML Probability"].between(0, 1).all()
    assert result["Historical Probability"].between(0, 1).all()


def test_actual_outcomes_are_correct():
    prices = make_prices()
    result = run_forecast(prices)

    for row in result.itertuples(index=False):
        origin = int(row[0])
        horizon = int(row[1])
        actual = int(row[3])

        expected = int(
            prices.iloc[origin + horizon] > prices.iloc[origin]
        )

        assert actual == expected


def test_only_development_periods_are_included():
    result = run_forecast()

    assert set(result["Research Period"]).issubset(
        {"Training", "Validation"}
    )


def test_final_test_prices_cannot_change_predictions():
    prices = make_prices()

    original = run_forecast(prices)

    split = create_research_split(
        len(prices),
        embargo_days=5,
    )

    modified = prices.copy()
    modified.iloc[split.validation_end:] *= 10

    updated = run_forecast(modified)

    pd.testing.assert_frame_equal(original, updated)


def test_predictions_are_deterministic():
    first = run_forecast()
    second = run_forecast()

    pd.testing.assert_frame_equal(first, second)


def test_no_duplicate_prediction_origins():
    result = run_forecast(horizons=(1, 5, 20))

    assert not result.duplicated(
        ["Forecast Index", "Horizon"]
    ).any()


def test_predictions_are_sorted():
    result = run_forecast(horizons=(1, 5, 20))

    expected = result.sort_values(
        ["Horizon", "Forecast Index"]
    ).reset_index(drop=True)

    pd.testing.assert_frame_equal(result, expected)


def test_invalid_prices_are_rejected():
    prices = make_prices()
    prices.iloc[100] = np.nan

    with pytest.raises(ValueError):
        run_forecast(prices)


@pytest.mark.parametrize("bad_horizon", [0, -1, True, 1.5])
def test_invalid_horizons_are_rejected(bad_horizon):
    with pytest.raises(ValueError):
        run_forecast(horizons=(bad_horizon,))


@pytest.mark.parametrize("bad_step", [0, -1, True])
def test_invalid_steps_are_rejected(bad_step):
    with pytest.raises(ValueError):
        ml_walk_forward_predictions(
            make_prices(),
            horizons=(5,),
            step=bad_step,
        )


def test_insufficient_history_is_rejected():
    with pytest.raises(ValueError):
        run_forecast(make_prices(n=300))
