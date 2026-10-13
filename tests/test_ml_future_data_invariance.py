"""Ensure ML forecasts cannot access future market prices."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.logistic_forecast import logistic_probability_forecast


@pytest.fixture(scope="module")
def prices():
    rng = np.random.default_rng(2026)

    returns = rng.normal(0.0005, 0.012, 1300)

    return pd.Series(
        100 * np.exp(np.cumsum(returns)),
        index=pd.bdate_range("2020-01-01", periods=1300),
    )


@pytest.mark.parametrize("horizon", [1, 5, 20, 60])
def test_future_prices_cannot_change_ml_probability(prices, horizon):
    forecast_index = 1000

    original = logistic_probability_forecast(
        close_prices=prices,
        forecast_index=forecast_index,
        horizon_days=horizon,
        training_window=756,
        regularization_c=0.1,
    )

    modified = prices.copy()

    modified.iloc[forecast_index + 1 :] *= 100

    changed = logistic_probability_forecast(
        close_prices=modified,
        forecast_index=forecast_index,
        horizon_days=horizon,
        training_window=756,
        regularization_c=0.1,
    )

    assert changed.probability_up == pytest.approx(
        original.probability_up,
        abs=1e-12,
    )


@pytest.mark.parametrize("horizon", [1, 5, 20, 60])
def test_ml_probability_is_valid(prices, horizon):
    result = logistic_probability_forecast(
        close_prices=prices,
        forecast_index=1000,
        horizon_days=horizon,
        training_window=756,
        regularization_c=0.1,
    )

    assert np.isfinite(result.probability_up)
    assert 0.0 <= result.probability_up <= 1.0


def test_ml_forecast_does_not_modify_input(prices):
    original = prices.copy(deep=True)

    logistic_probability_forecast(
        close_prices=prices,
        forecast_index=1000,
        horizon_days=5,
        training_window=756,
        regularization_c=0.1,
    )

    pd.testing.assert_series_equal(prices, original)
