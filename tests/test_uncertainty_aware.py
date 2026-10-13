"""Tests for uncertainty-aware probability forecasting."""

from math import erf, sqrt

import numpy as np
import pandas as pd
import pytest

from app.forecasting.uncertainty_aware import uncertainty_aware_forecast


def make_prices(n=300, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.015, n - 1)
    return pd.Series(100 * np.exp(np.r_[0, np.cumsum(returns)]))


def test_default_horizons():
    results = uncertainty_aware_forecast(make_prices())

    assert [r.horizon_days for r in results] == [1, 5, 20, 60]


def test_probabilities_are_valid():
    results = uncertainty_aware_forecast(make_prices())

    for result in results:
        assert 0 <= result.probability_up <= 1
        assert np.isfinite(result.expected_return_pct)
        assert np.isfinite(result.predictive_volatility_pct)


def test_uncertainty_increases_predictive_variance():
    prices = make_prices()
    result = uncertainty_aware_forecast(prices, horizons=(60,))[0]

    returns = np.diff(np.log(prices.to_numpy()))[-252:]
    sigma = np.std(returns, ddof=1)

    original_std = sigma * sqrt(60)

    assert result.predictive_volatility_pct / 100 > original_std


def test_probability_matches_mathematical_formula():
    prices = make_prices()

    result = uncertainty_aware_forecast(
        prices,
        horizons=(20,),
    )[0]

    returns = np.diff(np.log(prices.to_numpy()))[-252:]

    mu = np.mean(returns)
    sigma = np.std(returns, ddof=1)
    n = len(returns)

    predictive_std = sigma * sqrt(20 + 20**2 / n)

    expected_probability = 0.5 * (
        1 + erf((20 * mu / predictive_std) / sqrt(2))
    )

    assert result.probability_up == pytest.approx(expected_probability)


def test_rising_prices():
    prices = pd.Series(np.linspace(100, 200, 300))

    result = uncertainty_aware_forecast(prices, horizons=(20,))[0]

    assert result.probability_up > 0.5


def test_falling_prices():
    prices = pd.Series(np.linspace(200, 100, 300))

    result = uncertainty_aware_forecast(prices, horizons=(20,))[0]

    assert result.probability_up < 0.5


def test_constant_prices_are_neutral():
    prices = pd.Series(np.full(300, 100.0))

    result = uncertainty_aware_forecast(prices, horizons=(20,))[0]

    assert result.probability_up == 0.5
    assert result.predictive_volatility_pct == 0.0


def test_lookback_limits_observations():
    result = uncertainty_aware_forecast(
        make_prices(500),
        horizons=(5,),
        lookback=150,
    )[0]

    assert result.observations == 150


@pytest.mark.parametrize("bad_value", [0.0, -5.0, np.nan, np.inf])
def test_invalid_prices_rejected(bad_value):
    prices = make_prices()
    prices.iloc[10] = bad_value

    with pytest.raises(ValueError):
        uncertainty_aware_forecast(prices)


@pytest.mark.parametrize("bad_horizon", [0, -1, 1.5, True])
def test_invalid_horizons_rejected(bad_horizon):
    with pytest.raises(ValueError):
        uncertainty_aware_forecast(
            make_prices(),
            horizons=(bad_horizon,),
        )


def test_insufficient_history_rejected():
    with pytest.raises(ValueError):
        uncertainty_aware_forecast(make_prices(50))


def test_invalid_lookback_rejected():
    with pytest.raises(ValueError):
        uncertainty_aware_forecast(make_prices(), lookback=1)


def test_invalid_minimum_observations_rejected():
    with pytest.raises(ValueError):
        uncertainty_aware_forecast(
            make_prices(),
            minimum_observations=1,
        )


def test_deterministic_results():
    prices = make_prices()

    first = uncertainty_aware_forecast(prices)
    second = uncertainty_aware_forecast(prices)

    assert first == second
