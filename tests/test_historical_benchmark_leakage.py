"""Verify that historical benchmark forecasts cannot see future prices."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.historical_benchmark import historical_up_probability


def make_prices(n=1000, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.015, n - 1)

    return pd.Series(
        100 * np.exp(np.r_[0.0, np.cumsum(returns)])
    )


@pytest.mark.parametrize("horizon", [1, 5, 20, 60])
def test_future_prices_cannot_change_forecast(horizon):
    prices = make_prices()

    forecast_index = 700

    original = historical_up_probability(
        prices,
        forecast_index=forecast_index,
        horizon=horizon,
    )

    modified = prices.copy()

    modified.iloc[forecast_index + 1:] *= 10

    updated = historical_up_probability(
        modified,
        forecast_index=forecast_index,
        horizon=horizon,
    )

    assert original == pytest.approx(updated)


@pytest.mark.parametrize("horizon", [1, 5, 20, 60])
def test_benchmark_uses_only_matured_outcomes(horizon):
    prices = make_prices()

    forecast_index = 700

    actual = historical_up_probability(
        prices,
        forecast_index=forecast_index,
        horizon=horizon,
    )

    historical_returns = (
        prices.iloc[horizon:forecast_index + 1].to_numpy()
        / prices.iloc[:forecast_index - horizon + 1].to_numpy()
        - 1.0
    )

    expected = float(np.mean(historical_returns > 0))

    assert actual == pytest.approx(expected)


@pytest.mark.parametrize("horizon", [1, 5, 20, 60])
def test_unmatured_outcomes_cannot_change_forecast(horizon):
    prices = make_prices()

    forecast_index = 700

    original = historical_up_probability(
        prices,
        forecast_index=forecast_index,
        horizon=horizon,
    )

    modified = prices.copy()

    modified.iloc[forecast_index + 1:] = (
        modified.iloc[forecast_index + 1:] * 100
    )

    updated = historical_up_probability(
        modified,
        forecast_index=forecast_index,
        horizon=horizon,
    )

    assert original == pytest.approx(updated)


def test_insufficient_matured_outcomes_are_rejected():
    prices = make_prices()

    with pytest.raises(ValueError):
        historical_up_probability(
            prices,
            forecast_index=50,
            horizon=60,
            minimum_samples=30,
        )
