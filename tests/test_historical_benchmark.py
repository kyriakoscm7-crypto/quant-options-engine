"""Tests for the leakage-free historical probability benchmark."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.historical_benchmark import (
    historical_up_probability,
)


def test_rising_prices_produce_probability_one():
    prices = pd.Series(np.linspace(100, 200, 200))

    result = historical_up_probability(
        prices,
        forecast_index=150,
        horizon=5,
    )

    assert result == pytest.approx(1.0)


def test_falling_prices_produce_probability_zero():
    prices = pd.Series(np.linspace(200, 100, 200))

    result = historical_up_probability(
        prices,
        forecast_index=150,
        horizon=5,
    )

    assert result == pytest.approx(0.0)


def test_future_prices_cannot_change_historical_probability():
    prices = pd.Series(np.linspace(100, 200, 200))

    original = historical_up_probability(
        prices,
        forecast_index=120,
        horizon=5,
    )

    modified = prices.copy()
    modified.iloc[121:] *= 3.0

    changed = historical_up_probability(
        modified,
        forecast_index=120,
        horizon=5,
    )

    assert original == pytest.approx(changed)


def test_insufficient_samples_are_rejected():
    prices = pd.Series(np.linspace(100, 200, 100))

    with pytest.raises(ValueError):
        historical_up_probability(
            prices,
            forecast_index=20,
            horizon=10,
            minimum_samples=30,
        )


def test_invalid_horizon_is_rejected():
    prices = pd.Series(np.linspace(100, 200, 100))

    with pytest.raises(ValueError):
        historical_up_probability(
            prices,
            forecast_index=80,
            horizon=0,
        )
