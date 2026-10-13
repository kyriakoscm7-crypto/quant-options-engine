"""Tests for leakage-safe probability benchmarks."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.probability_benchmarks import (
    historical_base_rate,
    neutral_probability,
)


@pytest.fixture
def prices():
    dates = pd.date_range("2020-01-01", periods=300, freq="B")

    values = 100 * np.exp(
        np.cumsum(
            0.002 + 0.015 * np.sin(np.arange(300) * 0.17)
        )
    )

    return pd.Series(values, index=dates)


def test_neutral_probability():
    assert neutral_probability() == 0.5


def test_strictly_increasing_prices():
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    values = np.arange(100, 400, dtype=float)
    series = pd.Series(values, index=dates)

    result = historical_base_rate(series, 250, 20)

    assert result.probability_up == 1.0
    assert result.observations == 231
    assert result.latest_training_origin == 230


def test_strictly_decreasing_prices():
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    values = np.arange(400, 100, -1, dtype=float)
    series = pd.Series(values, index=dates)

    result = historical_base_rate(series, 250, 20)

    assert result.probability_up == 0.0


def test_only_matured_outcomes_are_used(prices):
    forecast_index = 200
    horizon = 20

    result = historical_base_rate(
        prices,
        forecast_index,
        horizon,
    )

    assert result.latest_training_origin == 180
    assert result.observations == 181


def test_future_prices_cannot_change_past_forecast(prices):
    original = historical_base_rate(
        prices,
        forecast_index=200,
        horizon_days=20,
    )

    modified = prices.copy()

    modified.iloc[201:] *= 1000

    changed = historical_base_rate(
        modified,
        forecast_index=200,
        horizon_days=20,
    )

    assert changed == original


def test_immature_outcomes_are_excluded(prices):
    original = historical_base_rate(
        prices,
        forecast_index=200,
        horizon_days=20,
    )

    modified = prices.copy()

    modified.iloc[201:220] *= 0.001

    changed = historical_base_rate(
        modified,
        forecast_index=200,
        horizon_days=20,
    )

    assert changed.probability_up == original.probability_up


def test_rolling_lookback_sample_count(prices):
    result = historical_base_rate(
        prices,
        forecast_index=200,
        horizon_days=20,
        lookback_days=50,
    )

    assert result.observations == 50
    assert result.latest_training_origin == 180


def test_rolling_lookback_matches_manual_calculation(prices):
    forecast_index = 200
    horizon = 20
    lookback = 50

    result = historical_base_rate(
        prices,
        forecast_index,
        horizon,
        lookback_days=lookback,
    )

    values = prices.to_numpy()

    origins = np.arange(131, 181)

    expected = np.mean(
        values[origins + horizon] > values[origins]
    )

    assert result.probability_up == pytest.approx(expected)


def test_full_history_matches_manual_calculation(prices):
    result = historical_base_rate(
        prices,
        forecast_index=200,
        horizon_days=5,
    )

    values = prices.to_numpy()

    origins = np.arange(196)

    expected = np.mean(
        values[origins + 5] > values[origins]
    )

    assert result.probability_up == pytest.approx(expected)


def test_insufficient_matured_history_rejected(prices):
    with pytest.raises(ValueError):
        historical_base_rate(
            prices,
            forecast_index=20,
            horizon_days=20,
            minimum_samples=30,
        )


def test_invalid_forecast_index_rejected(prices):
    with pytest.raises(ValueError):
        historical_base_rate(
            prices,
            forecast_index=300,
            horizon_days=5,
        )


def test_invalid_horizon_rejected(prices):
    with pytest.raises(ValueError):
        historical_base_rate(
            prices,
            forecast_index=200,
            horizon_days=0,
        )


@pytest.mark.parametrize(
    "bad_lookback",
    [0, -1, 1.5, True],
)
def test_invalid_lookback_rejected(prices, bad_lookback):
    with pytest.raises(ValueError):
        historical_base_rate(
            prices,
            forecast_index=200,
            horizon_days=5,
            lookback_days=bad_lookback,
        )


def test_missing_price_rejected(prices):
    modified = prices.copy()
    modified.iloc[100] = np.nan

    with pytest.raises(ValueError):
        historical_base_rate(
            modified,
            forecast_index=200,
            horizon_days=5,
        )


def test_negative_price_rejected(prices):
    modified = prices.copy()
    modified.iloc[100] = -1.0

    with pytest.raises(ValueError):
        historical_base_rate(
            modified,
            forecast_index=200,
            horizon_days=5,
        )


def test_original_prices_unchanged(prices):
    original = prices.copy(deep=True)

    historical_base_rate(
        prices,
        forecast_index=200,
        horizon_days=20,
    )

    pd.testing.assert_series_equal(prices, original)


def test_forecast_is_deterministic(prices):
    first = historical_base_rate(prices, 200, 20)
    second = historical_base_rate(prices, 200, 20)

    assert first == second


def test_future_invalid_prices_are_not_accessed(prices):
    modified = prices.copy()
    modified.iloc[250:] = np.nan

    result = historical_base_rate(
        modified,
        forecast_index=200,
        horizon_days=20,
    )

    assert 0 <= result.probability_up <= 1
