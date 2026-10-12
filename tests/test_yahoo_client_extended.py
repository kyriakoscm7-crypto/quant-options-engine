"""
Extended tests for the Yahoo Finance option-chain client.

These tests use mocked Yahoo Finance data instead of making
real network requests.

This allows us to test market-data processing reliably,
even when Yahoo Finance is unavailable.
"""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from app.market_data.yahoo_client import (
    calculate_observation_age_hours,
    fetch_option_chain,
    is_valid_option_quote,
    normalize_timestamp,
)

# ============================================================
# TEST HELPERS
# ============================================================


def make_expiration(days_from_today=30):
    """
    Create an expiration date relative to the current date.

    Using a future date prevents tests from becoming outdated.
    """

    return (
        datetime.now(UTC).date() + timedelta(days=days_from_today)
    ).isoformat()


def make_mock_ticker(
    stock_price=500.0,
    expirations=None,
    calls=None,
):
    """
    Create a fake Yahoo Finance ticker.

    It provides the same attributes and methods that our
    application uses, without connecting to Yahoo Finance.
    """

    if expirations is None:
        expirations = [make_expiration(30)]

    if calls is None:
        calls = pd.DataFrame(
            [
                {
                    "strike": 500.0,
                    "bid": 19.0,
                    "ask": 21.0,
                    "lastTradeDate": pd.Timestamp.now(tz="UTC"),
                }
            ]
        )

    history = pd.DataFrame(
        {"Close": [stock_price]},
        index=pd.DatetimeIndex(
            [pd.Timestamp.now(tz="UTC")]
        ),
    )

    class MockTicker:
        def __init__(self):
            self.options = expirations
            self.requested_expiration = None

        def history(self, period):
            assert period == "5d"
            return history

        def option_chain(self, expiration):
            self.requested_expiration = expiration
            return SimpleNamespace(calls=calls)

    return MockTicker()


# ============================================================
# OPTION QUOTE VALIDATION TESTS
# ============================================================


@pytest.mark.parametrize(
    "strike,bid,ask",
    [
        (0, 10, 11),
        (-100, 10, 11),
        (100, 0, 11),
        (100, -1, 11),
        (100, 10, 0),
        (100, 10, -1),
        (100, 12, 10),
        (float("nan"), 10, 11),
        (100, float("nan"), 11),
        (100, 10, float("nan")),
        (float("inf"), 10, 11),
        (100, float("inf"), 11),
        (100, 10, float("inf")),
        (None, 10, 11),
        (100, None, 11),
        (100, 10, None),
        ("invalid", 10, 11),
    ],
)
def test_invalid_option_quotes_are_rejected(strike, bid, ask):
    """
    Verify that invalid quotes are rejected safely.
    """

    assert not is_valid_option_quote(
        strike=strike,
        bid=bid,
        ask=ask,
    )


def test_valid_option_quote_is_accepted():
    """
    A normal bid/ask quote should pass validation.
    """

    assert is_valid_option_quote(
        strike=500,
        bid=19,
        ask=21,
    )


def test_excessively_wide_spread_is_rejected():
    """
    Quotes with excessive spreads should be rejected.
    """

    assert not is_valid_option_quote(
        strike=500,
        bid=10,
        ask=20,
        maximum_relative_spread=0.30,
    )


def test_negative_maximum_spread_is_rejected():
    """
    A negative spread threshold is invalid.
    """

    assert not is_valid_option_quote(
        strike=500,
        bid=19,
        ask=21,
        maximum_relative_spread=-0.1,
    )


def test_zero_spread_is_accepted():
    """
    Equal positive bid and ask prices are permitted.
    """

    assert is_valid_option_quote(
        strike=500,
        bid=20,
        ask=20,
    )


# ============================================================
# TIMESTAMP TESTS
# ============================================================


def test_normalize_timestamp_converts_to_utc():
    """
    Timezone-aware timestamps should be converted to UTC.
    """

    result = normalize_timestamp(
        pd.Timestamp("2026-01-01 10:00:00-05:00")
    )

    assert result == "2026-01-01T15:00:00+00:00"


@pytest.mark.parametrize(
    "timestamp",
    [
        None,
        "not-a-date",
        pd.NaT,
        pd.Timestamp("2026-01-01 10:00:00"),
    ],
)
def test_normalize_timestamp_rejects_invalid_values(timestamp):
    """
    Invalid and timezone-naive timestamps should return None.
    """

    assert normalize_timestamp(timestamp) is None


def test_observation_age_is_calculated_correctly():
    """
    Observation age should be returned in hours.
    """

    observation = pd.Timestamp(
        "2026-01-01T10:00:00+00:00"
    )

    reference = pd.Timestamp(
        "2026-01-01T12:30:00+00:00"
    )

    assert calculate_observation_age_hours(
        observation,
        reference,
    ) == 2.5


def test_future_observation_is_rejected():
    """
    An observation cannot be newer than its reference time.
    """

    observation = pd.Timestamp(
        "2026-01-01T13:00:00+00:00"
    )

    reference = pd.Timestamp(
        "2026-01-01T12:00:00+00:00"
    )

    assert calculate_observation_age_hours(
        observation,
        reference,
    ) is None


def test_invalid_observation_age_returns_none():
    """
    Invalid timestamps should not produce an observation age.
    """

    assert calculate_observation_age_hours(
        None,
        pd.Timestamp.now(tz="UTC"),
    ) is None


# ============================================================
# YAHOO FINANCE DATA VALIDATION TESTS
# ============================================================


def test_missing_stock_history_raises_error():
    """
    The client should reject missing underlying price data.
    """

    mock_ticker = make_mock_ticker()

    def empty_history(period):
        return pd.DataFrame()

    mock_ticker.history = empty_history

    with patch(
        "app.market_data.yahoo_client.yf.Ticker",
        return_value=mock_ticker,
    ), pytest.raises(
        RuntimeError,
        match="No underlying price data available",
    ):
        fetch_option_chain()


@pytest.mark.parametrize(
    "stock_price",
    [
        0,
        -100,
        float("nan"),
        float("inf"),
    ],
)
def test_invalid_underlying_price_raises_error(stock_price):
    """
    Stock prices must be positive and finite.
    """

    mock_ticker = make_mock_ticker(
        stock_price=stock_price
    )

    with patch(
        "app.market_data.yahoo_client.yf.Ticker",
        return_value=mock_ticker,
    ), pytest.raises(
        RuntimeError,
        match="Invalid underlying price received",
    ):
        fetch_option_chain()


def test_missing_expirations_raises_error():
    """
    An option chain must contain expiration dates.
    """

    mock_ticker = make_mock_ticker(
        expirations=[]
    )

    with patch(
        "app.market_data.yahoo_client.yf.Ticker",
        return_value=mock_ticker,
    ), pytest.raises(
        RuntimeError,
        match="No options expirations available",
    ):
        fetch_option_chain()


def test_no_eligible_expirations_raises_error():
    """
    Expirations that are too close should be rejected.
    """

    mock_ticker = make_mock_ticker(
        expirations=[make_expiration(2)]
    )

    with patch(
        "app.market_data.yahoo_client.yf.Ticker",
        return_value=mock_ticker,
    ), pytest.raises(
        RuntimeError,
        match="No suitable expiration dates available",
    ):
        fetch_option_chain(
            minimum_days_to_expiry=7
        )


# ============================================================
# OPTION CHAIN PROCESSING TESTS
# ============================================================


def test_fetch_option_chain_returns_valid_dataframe():
    """
    Verify that valid option data produces the expected
    structured DataFrame.
    """

    mock_ticker = make_mock_ticker()

    with (
        patch(
            "app.market_data.yahoo_client.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.yahoo_client.implied_volatility",
            return_value=0.20,
        ),
    ):
        result = fetch_option_chain(
            ticker_symbol="SPY"
        )

    assert isinstance(result, pd.DataFrame)

    assert len(result) == 1

    row = result.iloc[0]

    assert row["Ticker"] == "SPY"
    assert row["UnderlyingPrice"] == 500.0
    assert row["Strike"] == 500.0
    assert row["Bid"] == 19.0
    assert row["Ask"] == 21.0
    assert row["MidPrice"] == 20.0
    assert row["ImpliedVolatility"] == 20.0
    assert row["Moneyness"] == 1.0

    assert row["RelativeSpread"] == pytest.approx(0.1)

    assert row["TimeToExpiration"] > 0

    assert row["RetrievedAtUTC"] is not None

    assert row["UnderlyingObservationAtUTC"] is not None

    assert row["OptionLastTradeAtUTC"] is not None


def test_invalid_quotes_are_filtered():
    """
    Invalid quotes should be removed from the results.
    """

    calls = pd.DataFrame(
        [
            {
                "strike": 500,
                "bid": 19,
                "ask": 21,
            },
            {
                "strike": 510,
                "bid": 0,
                "ask": 20,
            },
            {
                "strike": 520,
                "bid": 25,
                "ask": 20,
            },
            {
                "strike": 530,
                "bid": 10,
                "ask": 20,
            },
        ]
    )

    mock_ticker = make_mock_ticker(
        calls=calls
    )

    with (
        patch(
            "app.market_data.yahoo_client.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.yahoo_client.implied_volatility",
            return_value=0.20,
        ),
    ):
        result = fetch_option_chain()

    assert len(result) == 1
    assert result.iloc[0]["Strike"] == 500


def test_nonfinite_implied_volatility_is_filtered():
    """
    Options with invalid implied volatility are excluded.
    """

    mock_ticker = make_mock_ticker()

    with (
        patch(
            "app.market_data.yahoo_client.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.yahoo_client.implied_volatility",
            return_value=float("nan"),
        ),
    ):
        result = fetch_option_chain()

    assert result.empty

    assert "ImpliedVolatility" in result.columns


def test_empty_option_chain_returns_empty_dataframe():
    """
    An empty option chain should return an empty DataFrame
    with the expected column names.
    """

    mock_ticker = make_mock_ticker(
        calls=pd.DataFrame(
            columns=["strike", "bid", "ask"]
        )
    )

    with patch(
        "app.market_data.yahoo_client.yf.Ticker",
        return_value=mock_ticker,
    ):
        result = fetch_option_chain()

    assert result.empty
    assert "Ticker" in result.columns
    assert "ImpliedVolatility" in result.columns


def test_correct_expiration_is_selected():
    """
    Verify that the first eligible expiration is selected.
    """

    eligible_expiration = make_expiration(30)

    mock_ticker = make_mock_ticker(
        expirations=[
            make_expiration(2),
            eligible_expiration,
            make_expiration(60),
        ]
    )

    with (
        patch(
            "app.market_data.yahoo_client.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.yahoo_client.implied_volatility",
            return_value=0.20,
        ),
    ):
        fetch_option_chain(
            minimum_days_to_expiry=7
        )

    assert mock_ticker.requested_expiration == eligible_expiration