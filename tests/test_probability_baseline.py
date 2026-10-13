"""Tests for the research-only probabilistic forecasting baseline."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.probability_baseline import forecast_probabilities


def make_prices(daily_log_returns):
    returns = np.asarray(daily_log_returns, dtype=float)
    prices = 100.0 * np.exp(np.r_[0.0, np.cumsum(returns)])
    return pd.Series(prices)


def test_default_forecast_horizons():
    returns = np.tile([0.01, -0.005, 0.008, -0.003], 80)
    forecasts = forecast_probabilities(make_prices(returns))

    assert [f.horizon_days for f in forecasts] == [1, 5, 20, 60]
    assert all(f.observations == 252 for f in forecasts)
    assert all(0 <= f.probability_up <= 1 for f in forecasts)


def test_positive_drift_produces_probability_above_half():
    returns = np.tile([0.012, -0.004], 100)
    forecast = forecast_probabilities(
        make_prices(returns),
        horizons=(5,),
    )[0]

    assert forecast.probability_up > 0.5
    assert forecast.expected_return_pct > 0


def test_negative_drift_produces_probability_below_half():
    returns = np.tile([-0.012, 0.004], 100)
    forecast = forecast_probabilities(
        make_prices(returns),
        horizons=(5,),
    )[0]

    assert forecast.probability_up < 0.5
    assert forecast.expected_return_pct < 0


def test_flat_prices_do_not_create_false_bullish_probability():
    prices = pd.Series(np.full(200, 100.0))
    forecast = forecast_probabilities(
        prices,
        horizons=(1,),
    )[0]

    assert forecast.expected_return_pct == pytest.approx(0.0)
    assert forecast.volatility_pct == pytest.approx(0.0)
    assert forecast.probability_up == 0.0


@pytest.mark.parametrize(
    "prices",
    [
        pd.Series([100.0] * 20),
        pd.Series([100.0] * 150 + [np.nan]),
        pd.Series([100.0] * 150 + [np.inf]),
        pd.Series([100.0] * 150 + [-1.0]),
        pd.Series([100.0] * 150 + [0.0]),
    ],
)
def test_invalid_prices_are_rejected(prices):
    with pytest.raises(ValueError):
        forecast_probabilities(prices)


def test_invalid_horizons_are_rejected():
    prices = pd.Series(np.linspace(100, 120, 200))

    with pytest.raises(ValueError):
        forecast_probabilities(prices, horizons=(0,))

    with pytest.raises(ValueError):
        forecast_probabilities(prices, horizons=(-5,))

    with pytest.raises(ValueError):
        forecast_probabilities(prices, horizons=(True,))


def test_insufficient_observations_rejected():
    prices = pd.Series(np.linspace(100, 120, 100))

    with pytest.raises(ValueError):
        forecast_probabilities(prices)


def test_forecast_uses_only_latest_lookback_returns():
    old_returns = np.full(200, -0.01)
    recent_returns = np.tile([0.012, -0.004], 100)

    prices = make_prices(np.r_[old_returns, recent_returns])

    forecast = forecast_probabilities(
        prices,
        horizons=(5,),
        lookback=200,
    )[0]

    assert forecast.observations == 200
    assert forecast.probability_up > 0.5
