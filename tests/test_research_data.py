"""Tests for historical research data validation."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.research_data import validate_close_prices


@pytest.fixture
def valid_prices():
    dates = pd.date_range("2020-01-01", periods=1200, freq="B")
    return pd.Series(
        np.linspace(100, 200, 1200),
        index=dates,
    )


def test_valid_prices_accepted(valid_prices):
    result = validate_close_prices("TEST", valid_prices)

    assert result.status == "Valid"
    assert result.observations == 1200
    assert result.close is not None


def test_missing_price_rejected(valid_prices):
    prices = valid_prices.copy()
    prices.iloc[100] = np.nan

    result = validate_close_prices("TEST", prices)

    assert result.status == "Rejected: missing prices"
    assert result.missing_prices == 1
    assert result.close is None


def test_negative_price_rejected(valid_prices):
    prices = valid_prices.copy()
    prices.iloc[100] = -5.0

    result = validate_close_prices("TEST", prices)

    assert result.status == "Rejected: invalid prices"
    assert result.invalid_prices == 1


def test_zero_price_rejected(valid_prices):
    prices = valid_prices.copy()
    prices.iloc[100] = 0.0

    result = validate_close_prices("TEST", prices)

    assert result.status == "Rejected: invalid prices"


def test_infinite_price_rejected(valid_prices):
    prices = valid_prices.copy()
    prices.iloc[100] = np.inf

    result = validate_close_prices("TEST", prices)

    assert result.status == "Rejected: invalid prices"


def test_duplicate_dates_rejected(valid_prices):
    prices = valid_prices.copy()
    dates = list(prices.index)
    dates[100] = dates[99]
    prices.index = pd.DatetimeIndex(dates)

    result = validate_close_prices("TEST", prices)

    assert result.status == "Rejected: duplicate dates"
    assert result.duplicate_dates == 1


def test_unsorted_dates_rejected(valid_prices):
    prices = valid_prices.iloc[::-1]

    result = validate_close_prices("TEST", prices)

    assert result.status == "Rejected: dates not chronological"


def test_insufficient_history_rejected(valid_prices):
    prices = valid_prices.iloc[:100]

    result = validate_close_prices("TEST", prices)

    assert result.status == "Rejected: insufficient history"


def test_custom_minimum_history(valid_prices):
    result = validate_close_prices(
        "TEST",
        valid_prices,
        minimum_observations=1500,
    )

    assert result.status == "Rejected: insufficient history"


def test_invalid_minimum_rejected(valid_prices):
    with pytest.raises(ValueError):
        validate_close_prices(
            "TEST",
            valid_prices,
            minimum_observations=0,
        )


def test_non_series_input_rejected():
    with pytest.raises(ValueError):
        validate_close_prices(
            "TEST",
            [100, 101, 102],
        )


def test_original_prices_not_modified(valid_prices):
    original = valid_prices.copy(deep=True)

    validate_close_prices("TEST", valid_prices)

    pd.testing.assert_series_equal(valid_prices, original)


def test_valid_date_range(valid_prices):
    result = validate_close_prices("TEST", valid_prices)

    assert result.start_date == "2020-01-01"
    assert result.end_date == "2024-08-06"


def test_empty_series_rejected():
    prices = pd.Series(
        dtype=float,
        index=pd.DatetimeIndex([]),
    )

    result = validate_close_prices("TEST", prices)

    assert result.status == "Rejected: insufficient history"
    assert result.observations == 0
