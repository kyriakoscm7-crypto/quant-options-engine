"""Regression tests for future-data leakage in historical forecasts."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.probability_benchmarks import historical_base_rate


@pytest.fixture
def prices():
    rng = np.random.default_rng(2026)

    returns = rng.normal(0.0005, 0.01, 1200)

    return pd.Series(
        100 * np.exp(np.cumsum(returns)),
        index=pd.bdate_range("2020-01-01", periods=1200),
    )


@pytest.mark.parametrize("horizon", [1, 5, 20, 60])
def test_future_prices_cannot_change_historical_probability(
    prices,
    horizon,
):
    forecast_index = 800

    original = historical_base_rate(
        close_prices=prices,
        forecast_index=forecast_index,
        horizon_days=horizon,
    )

    modified = prices.copy()

    modified.iloc[forecast_index + 1 :] *= 100

    changed = historical_base_rate(
        close_prices=modified,
        forecast_index=forecast_index,
        horizon_days=horizon,
    )

    assert changed.probability_up == pytest.approx(
        original.probability_up
    )

    assert changed.observations == original.observations

    assert (
        changed.latest_training_origin
        <= forecast_index - horizon
    )


@pytest.mark.parametrize("horizon", [1, 5, 20, 60])
def test_latest_training_outcome_is_matured(prices, horizon):
    forecast_index = 800

    result = historical_base_rate(
        close_prices=prices,
        forecast_index=forecast_index,
        horizon_days=horizon,
    )

    assert (
        result.latest_training_origin + horizon
        <= forecast_index
    )


def test_original_prices_are_not_modified(prices):
    original = prices.copy(deep=True)

    historical_base_rate(
        close_prices=prices,
        forecast_index=800,
        horizon_days=20,
    )

    pd.testing.assert_series_equal(prices, original)
