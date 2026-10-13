"""
Automated tests for historical stock-market data and analytics.

Tests cover:
- Ticker validation.
- Historical returns.
- Annualized volatility.
- Maximum drawdown.
- Normalized performance.
- Yahoo Finance data cleaning.
- Invalid data and provider failures.

Yahoo Finance is mocked so these tests run without internet access.
"""

import math
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from app.market_data.stock_history import (
    TRADING_DAYS_PER_YEAR,
    calculate_normalized_performance,
    calculate_stock_statistics,
    fetch_stock_history,
    validate_ticker,
)

# ============================================================
# TEST DATA HELPERS
# ============================================================

def make_price_history(prices):
    """
    Create a small deterministic historical-price dataset.

    Fixed prices allow exact calculations to be checked
    without downloading real market data.
    """

    dates = pd.date_range(
        "2026-01-05",
        periods=len(prices),
        freq="B",
        tz="UTC",
    )

    return pd.DataFrame(
        {
            "Date": dates,
            "Close": prices,
        }
    )


def make_yahoo_history():
    """
    Create a simulated Yahoo Finance response.

    Includes one invalid observation to verify cleaning.
    """

    dates = pd.date_range(
        "2026-01-05",
        periods=4,
        freq="B",
        tz="America/New_York",
    )

    return pd.DataFrame(
        {
            "Open": [100.0, 102.0, -1.0, 104.0],
            "High": [105.0, 106.0, 110.0, 108.0],
            "Low": [99.0, 101.0, 98.0, 103.0],
            "Close": [103.0, 105.0, 107.0, 106.0],
            "Volume": [1000, 1200, 1300, 1400],
        },
        index=dates,
    )


# ============================================================
# TICKER VALIDATION TESTS
# ============================================================

# TEST 1:
# Lowercase tickers should be converted to uppercase.
def test_validate_ticker_uppercase():

    assert validate_ticker("aapl") == "AAPL"


# TEST 2:
# Leading and trailing whitespace should be removed.
def test_validate_ticker_whitespace():

    assert validate_ticker(" spy ") == "SPY"


# TEST 3:
# Tickers containing supported punctuation should work.
def test_validate_ticker_hyphen():

    assert validate_ticker("brk-b") == "BRK-B"


# TEST 4:
# Empty ticker symbols must be rejected.
def test_validate_ticker_empty():

    with pytest.raises(ValueError):

        validate_ticker("")


# TEST 5:
# Unsupported characters must be rejected.
def test_validate_ticker_invalid_characters():

    with pytest.raises(ValueError):

        validate_ticker("AAPL!")


# TEST 6:
# Non-string ticker inputs must be rejected.
def test_validate_ticker_non_string():

    with pytest.raises(ValueError):

        validate_ticker(None)


# ============================================================
# HISTORICAL STATISTICS TESTS
# ============================================================

# TEST 7:
# Verify total return using a known price sequence.
def test_total_return():

    history = make_price_history(
        [100.0, 110.0, 120.0]
    )

    statistics = calculate_stock_statistics(history)

    assert statistics["total_return_pct"] == 20.0


# TEST 8:
# Verify the latest closing price.
def test_latest_close():

    history = make_price_history(
        [100.0, 105.0, 110.0]
    )

    statistics = calculate_stock_statistics(history)

    assert statistics["latest_close"] == 110.0


# TEST 9:
# Verify the previous closing price.
def test_previous_close():

    history = make_price_history(
        [100.0, 105.0, 110.0]
    )

    statistics = calculate_stock_statistics(history)

    assert statistics["previous_close"] == 105.0


# TEST 10:
# Verify the percentage change from the previous close.
def test_latest_daily_change():

    history = make_price_history(
        [100.0, 110.0]
    )

    statistics = calculate_stock_statistics(history)

    assert statistics["latest_change_pct"] == 10.0


# TEST 11:
# Verify annualized volatility using sample standard deviation.
def test_annualized_volatility():

    history = make_price_history(
        [100.0, 110.0, 99.0, 108.9]
    )

    statistics = calculate_stock_statistics(history)

    daily_returns = np.array(
        [0.10, -0.10, 0.10]
    )

    expected = (
        np.std(daily_returns, ddof=1)
        * math.sqrt(TRADING_DAYS_PER_YEAR)
        * 100.0
    )

    assert statistics[
        "annualized_volatility_pct"
    ] == pytest.approx(
        expected,
        abs=0.0001,
    )


# TEST 12:
# Verify maximum drawdown from a known historical peak.
def test_maximum_drawdown():

    history = make_price_history(
        [100.0, 120.0, 90.0, 110.0]
    )

    statistics = calculate_stock_statistics(history)

    # Peak = 120, trough = 90.
    # Drawdown = (90 / 120 - 1) * 100 = -25%.

    assert statistics["maximum_drawdown_pct"] == -25.0


# TEST 13:
# A continuously rising stock should have zero drawdown.
def test_zero_drawdown():

    history = make_price_history(
        [100.0, 110.0, 120.0]
    )

    statistics = calculate_stock_statistics(history)

    assert statistics["maximum_drawdown_pct"] == 0.0


# TEST 14:
# A single observation cannot produce a daily return
# or meaningful volatility.
def test_single_observation():

    history = make_price_history(
        [100.0]
    )

    statistics = calculate_stock_statistics(history)

    assert statistics["latest_close"] == 100.0

    assert statistics["previous_close"] is None

    assert statistics["latest_change_pct"] is None

    assert statistics["annualized_volatility_pct"] is None

    assert statistics["total_return_pct"] == 0.0


# TEST 15:
# The statistics engine must count valid observations.
def test_trading_days():

    history = make_price_history(
        [100.0, 110.0, 120.0]
    )

    statistics = calculate_stock_statistics(history)

    assert statistics["trading_days"] == 3


# TEST 16:
# Missing closing-price columns must be rejected.
def test_missing_close_column():

    history = pd.DataFrame(
        {"Open": [100.0, 110.0]}
    )

    with pytest.raises(ValueError):

        calculate_stock_statistics(history)


# TEST 17:
# Empty historical datasets must be rejected.
def test_empty_statistics():

    history = pd.DataFrame(
        {"Close": []}
    )

    with pytest.raises(ValueError):

        calculate_stock_statistics(history)


# ============================================================
# NORMALIZED PERFORMANCE TESTS
# ============================================================

# TEST 18:
# Normalized performance must start at 100.
def test_normalized_start():

    history = make_price_history(
        [50.0, 60.0, 75.0]
    )

    result = calculate_normalized_performance(history)

    assert result["Normalized"].iloc[0] == 100.0


# TEST 19:
# A 50% increase should produce normalized value 150.
def test_normalized_growth():

    history = make_price_history(
        [50.0, 60.0, 75.0]
    )

    result = calculate_normalized_performance(history)

    assert result["Normalized"].iloc[-1] == 150.0


# TEST 20:
# Missing required columns must be rejected.
def test_normalized_missing_columns():

    history = pd.DataFrame(
        {"Close": [100.0, 110.0]}
    )

    with pytest.raises(ValueError):

        calculate_normalized_performance(history)


# ============================================================
# YAHOO FINANCE DATA TESTS
# ============================================================

# TEST 21:
# Verify downloaded market data is cleaned and structured.
@patch("app.market_data.stock_history.yf.Ticker")
def test_fetch_stock_history_success(mock_ticker):

    mock_instance = MagicMock()

    mock_instance.history.return_value = (
        make_yahoo_history()
    )

    mock_ticker.return_value = mock_instance

    result = fetch_stock_history(
        "aapl",
        "1mo",
    )

    # One observation has a negative opening price.
    assert len(result) == 3

    assert result["Ticker"].unique().tolist() == [
        "AAPL"
    ]

    assert list(result.columns) == [
        "Date",
        "Ticker",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    assert str(result["Date"].dt.tz) == "UTC"

    mock_instance.history.assert_called_once_with(
        period="1mo",
        interval="1d",
        auto_adjust=True,
        actions=False,
    )


# TEST 22:
# Unsupported historical periods must be rejected.
def test_fetch_invalid_period():

    with pytest.raises(ValueError):

        fetch_stock_history(
            "AAPL",
            "invalid-period",
        )


# TEST 23:
# Empty Yahoo Finance responses must produce a clear error.
@patch("app.market_data.stock_history.yf.Ticker")
def test_fetch_empty_history(mock_ticker):

    mock_instance = MagicMock()

    mock_instance.history.return_value = (
        pd.DataFrame()
    )

    mock_ticker.return_value = mock_instance

    with pytest.raises(RuntimeError):

        fetch_stock_history(
            "AAPL",
            "1mo",
        )


# TEST 24:
# Network/provider failures must produce a clear error.
@patch("app.market_data.stock_history.yf.Ticker")
def test_fetch_provider_failure(mock_ticker):

    mock_instance = MagicMock()

    mock_instance.history.side_effect = (
        ConnectionError("Simulated network failure")
    )

    mock_ticker.return_value = mock_instance

    with pytest.raises(RuntimeError):

        fetch_stock_history(
            "AAPL",
            "1mo",
        )


# TEST 25:
# Yahoo Finance responses missing price columns
# must be rejected.
@patch("app.market_data.stock_history.yf.Ticker")
def test_fetch_missing_columns(mock_ticker):

    mock_instance = MagicMock()

    mock_instance.history.return_value = (
        pd.DataFrame(
            {
                "Close": [100.0, 110.0],
            }
        )
    )

    mock_ticker.return_value = mock_instance

    with pytest.raises(RuntimeError):

        fetch_stock_history(
            "AAPL",
            "1mo",
        )