"""Tests for leakage-aware logistic regression forecasting."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.logistic_forecast import logistic_probability_forecast


def make_prices(n=1100, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.015, n - 1)
    return pd.Series(100 * np.exp(np.r_[0.0, np.cumsum(returns)]))


def forecast(prices=None, **kwargs):
    if prices is None:
        prices = make_prices()

    return logistic_probability_forecast(
        prices,
        forecast_index=800,
        horizon_days=20,
        **kwargs,
    )


def test_probability_is_valid():
    result = forecast()

    assert 0 <= result.probability_up <= 1


def test_forecast_metadata():
    result = forecast()

    assert result.horizon_days == 20
    assert result.forecast_index == 800
    assert result.training_samples >= 120


def test_training_labels_are_matured():
    result = forecast()

    assert result.training_end_index + result.horizon_days <= (
        result.forecast_index
    )


def test_training_window_is_respected():
    result = forecast(training_window=300)

    assert result.training_samples <= 300
    assert result.training_end_index <= 780
    assert result.training_start_index >= 481


def test_future_prices_cannot_change_prediction():
    prices = make_prices()

    original = forecast(prices)

    modified = prices.copy()
    modified.iloc[801:] *= 10

    updated = forecast(modified)

    assert original == updated


def test_future_data_can_be_omitted():
    prices = make_prices()

    full = forecast(prices)

    truncated = forecast(prices.iloc[:801])

    assert full == truncated


def test_forecast_is_deterministic():
    first = forecast()
    second = forecast()

    assert first == second


def test_different_horizons_respect_maturity():
    prices = make_prices()

    for horizon in (1, 5, 20, 60):
        result = logistic_probability_forecast(
            prices,
            forecast_index=800,
            horizon_days=horizon,
        )

        assert result.training_end_index + horizon <= 800
        assert 0 <= result.probability_up <= 1


def test_training_samples_match_reported_boundaries():
    result = forecast(training_window=300)

    assert result.training_samples > 0
    assert result.training_start_index <= result.training_end_index


def test_insufficient_training_data_is_rejected():
    with pytest.raises(ValueError):
        logistic_probability_forecast(
            make_prices(n=350),
            forecast_index=250,
            horizon_days=60,
        )


def test_single_class_training_is_rejected():
    prices = pd.Series(
        100 * np.exp(np.arange(1100) * 0.001)
    )

    with pytest.raises(ValueError, match="only one class"):
        forecast(prices)


@pytest.mark.parametrize(
    "bad_horizon",
    [0, -1, True, 1.5],
)
def test_invalid_horizon_is_rejected(bad_horizon):
    with pytest.raises(ValueError):
        logistic_probability_forecast(
            make_prices(),
            forecast_index=800,
            horizon_days=bad_horizon,
        )


@pytest.mark.parametrize(
    "bad_index",
    [-1, 1100, True, 1.5],
)
def test_invalid_forecast_index_is_rejected(bad_index):
    with pytest.raises(ValueError):
        logistic_probability_forecast(
            make_prices(),
            forecast_index=bad_index,
        )


@pytest.mark.parametrize(
    "bad_c",
    [0, -1, np.nan, np.inf, True],
)
def test_invalid_regularization_is_rejected(bad_c):
    with pytest.raises(ValueError):
        forecast(regularization_c=bad_c)


@pytest.mark.parametrize(
    "bad_window",
    [0, -1, True],
)
def test_invalid_training_window_is_rejected(bad_window):
    with pytest.raises(ValueError):
        forecast(training_window=bad_window)


def test_invalid_prices_are_rejected():
    prices = make_prices()
    prices.iloc[500] = np.nan

    with pytest.raises(ValueError):
        forecast(prices)
