"""
Extended tests for the multi-expiration options data collector.

These tests verify:
- Expiration-date selection and filtering.
- Duplicate expiration removal.
- Maximum expiration limits.
- Invalid parameter handling.
- Collection of multiple option chains.
- Handling of missing and invalid option data.
- Correct sorting and combination of results.

Yahoo Finance and the single-expiration collector are mocked
so tests do not require internet access.
"""

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest

from app.market_data.multi_expiration import (
    fetch_multiple_expirations,
    select_expirations,
)
from app.market_data.yahoo_client import MARKET_TIMEZONE

# ============================================================
# TEST HELPERS
# ============================================================


def make_expiration(days_from_today):
    """
    Generate an expiration date relative to New York time.

    This keeps tests valid regardless of the calendar date.
    """

    today = datetime.now(MARKET_TIMEZONE).date()

    return (
        today + timedelta(days=days_from_today)
    ).isoformat()


def make_option_dataframe(expiration, strikes=(500.0,)):
    """
    Create fake option-chain data for one expiration.

    The columns match those needed by the multi-expiration
    collector.
    """

    days_until_expiration = (
        datetime.strptime(expiration, "%Y-%m-%d").date()
        - datetime.now(MARKET_TIMEZONE).date()
    ).days

    return pd.DataFrame(
        [
            {
                "Ticker": "SPY",
                "Expiration": expiration,
                "Strike": strike,
                "TimeToExpiration": days_until_expiration / 365.0,
                "ImpliedVolatility": 20.0,
            }
            for strike in strikes
        ]
    )


def make_mock_ticker(expirations):
    """
    Create a fake Yahoo Finance ticker containing
    predetermined expiration dates.
    """

    return SimpleNamespace(
        options=expirations
    )


# ============================================================
# EXPIRATION SELECTION TESTS
# ============================================================


def test_select_expirations_returns_chronological_order():
    """
    Expiration dates should be sorted from earliest to latest.
    """

    dates = [
        make_expiration(60),
        make_expiration(14),
        make_expiration(30),
    ]

    result = select_expirations(
        dates,
        minimum_days_to_expiry=7,
    )

    assert result == sorted(dates)


def test_select_expirations_removes_duplicates():
    """
    Duplicate expiration dates should appear only once.
    """

    expiration = make_expiration(30)

    result = select_expirations(
        [
            expiration,
            expiration,
            expiration,
        ]
    )

    assert result == [expiration]


def test_select_expirations_filters_early_dates():
    """
    Expirations earlier than the minimum threshold
    should be removed.
    """

    early = make_expiration(2)
    valid = make_expiration(30)

    result = select_expirations(
        [early, valid],
        minimum_days_to_expiry=7,
    )

    assert result == [valid]


def test_select_expirations_includes_boundary_date():
    """
    An expiration exactly on the minimum threshold
    should be accepted.
    """

    expiration = make_expiration(7)

    result = select_expirations(
        [expiration],
        minimum_days_to_expiry=7,
    )

    assert result == [expiration]


def test_select_expirations_respects_maximum_limit():
    """
    Only the requested number of expirations
    should be selected.
    """

    dates = [
        make_expiration(14),
        make_expiration(30),
        make_expiration(60),
        make_expiration(90),
    ]

    result = select_expirations(
        dates,
        maximum_expirations=2,
    )

    assert len(result) == 2

    assert result == dates[:2]


def test_select_expirations_empty_input():
    """
    An empty expiration list should return an empty list.
    """

    assert select_expirations([]) == []


def test_select_expirations_all_too_early():
    """
    If every expiration is too close, return an empty list.
    """

    result = select_expirations(
        [
            make_expiration(1),
            make_expiration(3),
        ],
        minimum_days_to_expiry=7,
    )

    assert result == []


def test_select_expirations_rejects_negative_minimum():
    """
    Negative minimum days should raise ValueError.
    """

    with pytest.raises(
        ValueError,
        match="minimum_days_to_expiry cannot be negative",
    ):
        select_expirations(
            [make_expiration(30)],
            minimum_days_to_expiry=-1,
        )


@pytest.mark.parametrize(
    "maximum_expirations",
    [
        0,
        -1,
        -10,
    ],
)
def test_select_expirations_rejects_invalid_maximum(
    maximum_expirations,
):
    """
    The maximum number of expirations must be at least one.
    """

    with pytest.raises(
        ValueError,
        match="maximum_expirations must be at least 1",
    ):
        select_expirations(
            [make_expiration(30)],
            maximum_expirations=maximum_expirations,
        )


def test_select_expirations_rejects_invalid_date():
    """
    Malformed expiration dates should raise ValueError.
    """

    with pytest.raises(ValueError):
        select_expirations(
            ["not-a-date"]
        )


# ============================================================
# MULTI-EXPIRATION COLLECTION TESTS
# ============================================================


def test_fetch_multiple_expirations_combines_data():
    """
    Verify that data from multiple expirations is combined
    into one DataFrame.
    """

    expiration_1 = make_expiration(30)
    expiration_2 = make_expiration(60)

    mock_ticker = make_mock_ticker(
        [expiration_1, expiration_2]
    )

    def mock_fetch_option_chain(**kwargs):
        minimum_days = kwargs["minimum_days_to_expiry"]

        if minimum_days <= 30:
            return make_option_dataframe(
                expiration_1,
                strikes=(500.0, 510.0),
            )

        return make_option_dataframe(
            expiration_2,
            strikes=(490.0, 500.0),
        )

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.multi_expiration.fetch_option_chain",
            side_effect=mock_fetch_option_chain,
        ),
    ):
        result = fetch_multiple_expirations(
            ticker_symbol="SPY",
            maximum_expirations=2,
        )

    assert isinstance(result, pd.DataFrame)

    assert len(result) == 4

    assert result["Expiration"].nunique() == 2

    assert set(result["Expiration"]) == {
        expiration_1,
        expiration_2,
    }

    assert result["TimeToExpiration"].is_monotonic_increasing


def test_fetch_multiple_expirations_sorts_strikes():
    """
    Within an expiration, strikes should be sorted.
    """

    expiration = make_expiration(30)

    mock_ticker = make_mock_ticker(
        [expiration]
    )

    unsorted_data = make_option_dataframe(
        expiration,
        strikes=(520.0, 480.0, 500.0),
    )

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.multi_expiration.fetch_option_chain",
            return_value=unsorted_data,
        ),
    ):
        result = fetch_multiple_expirations()

    assert result["Strike"].tolist() == [
        480.0,
        500.0,
        520.0,
    ]


def test_fetch_multiple_expirations_missing_expirations():
    """
    Missing expiration dates should raise RuntimeError.
    """

    mock_ticker = make_mock_ticker([])

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        pytest.raises(
            RuntimeError,
            match="No option expiration dates available",
        ),
    ):
        fetch_multiple_expirations()


def test_fetch_multiple_expirations_no_eligible_dates():
    """
    Expirations that are too close should be rejected.
    """

    mock_ticker = make_mock_ticker(
        [make_expiration(2)]
    )

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        pytest.raises(
            RuntimeError,
            match="No eligible option expirations available",
        ),
    ):
        fetch_multiple_expirations(
            minimum_days_to_expiry=7
        )


def test_fetch_multiple_expirations_skips_empty_data():
    """
    Empty option-chain results should be skipped.
    """

    expiration_1 = make_expiration(30)
    expiration_2 = make_expiration(60)

    mock_ticker = make_mock_ticker(
        [expiration_1, expiration_2]
    )

    def mock_fetch_option_chain(**kwargs):
        minimum_days = kwargs["minimum_days_to_expiry"]

        if minimum_days <= 30:
            return pd.DataFrame()

        return make_option_dataframe(
            expiration_2
        )

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.multi_expiration.fetch_option_chain",
            side_effect=mock_fetch_option_chain,
        ),
    ):
        result = fetch_multiple_expirations()

    assert len(result) == 1

    assert result.iloc[0]["Expiration"] == expiration_2


def test_fetch_multiple_expirations_skips_wrong_expiration():
    """
    Data returned for the wrong expiration should be ignored.
    """

    expiration_1 = make_expiration(30)
    expiration_2 = make_expiration(60)

    mock_ticker = make_mock_ticker(
        [expiration_1, expiration_2]
    )

    def mock_fetch_option_chain(**kwargs):
        minimum_days = kwargs["minimum_days_to_expiry"]

        if minimum_days <= 30:
            return make_option_dataframe(
                expiration_2
            )

        return make_option_dataframe(
            expiration_2
        )

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.multi_expiration.fetch_option_chain",
            side_effect=mock_fetch_option_chain,
        ),
    ):
        result = fetch_multiple_expirations()

    assert len(result) == 1

    assert result.iloc[0]["Expiration"] == expiration_2


@pytest.mark.parametrize(
    "exception",
    [
        RuntimeError("Market data unavailable"),
        ValueError("Invalid option data"),
    ],
)
def test_fetch_multiple_expirations_skips_failed_requests(
    exception,
):
    """
    A failed expiration should not prevent processing
    another valid expiration.
    """

    expiration_1 = make_expiration(30)
    expiration_2 = make_expiration(60)

    mock_ticker = make_mock_ticker(
        [expiration_1, expiration_2]
    )

    def mock_fetch_option_chain(**kwargs):
        minimum_days = kwargs["minimum_days_to_expiry"]

        if minimum_days <= 30:
            raise exception

        return make_option_dataframe(
            expiration_2
        )

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.multi_expiration.fetch_option_chain",
            side_effect=mock_fetch_option_chain,
        ),
    ):
        result = fetch_multiple_expirations()

    assert len(result) == 1

    assert result.iloc[0]["Expiration"] == expiration_2


def test_fetch_multiple_expirations_all_empty_raises_error():
    """
    If no valid observations are collected,
    the function should raise RuntimeError.
    """

    expiration = make_expiration(30)

    mock_ticker = make_mock_ticker(
        [expiration]
    )

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.multi_expiration.fetch_option_chain",
            return_value=pd.DataFrame(),
        ),
        pytest.raises(
            RuntimeError,
            match="No valid option data collected",
        ),
    ):
        fetch_multiple_expirations()


def test_fetch_multiple_expirations_passes_parameters():
    """
    Verify that the collector forwards important parameters
    to the single-expiration function.
    """

    expiration = make_expiration(30)

    mock_ticker = make_mock_ticker(
        [expiration]
    )

    with (
        patch(
            "app.market_data.multi_expiration.yf.Ticker",
            return_value=mock_ticker,
        ),
        patch(
            "app.market_data.multi_expiration.fetch_option_chain",
            return_value=make_option_dataframe(expiration),
        ) as mock_fetch,
    ):
        fetch_multiple_expirations(
            ticker_symbol="QQQ",
            risk_free_rate=0.05,
            dividend_yield=0.01,
            maximum_relative_spread=0.15,
        )

    mock_fetch.assert_called_once()

    kwargs = mock_fetch.call_args.kwargs

    assert kwargs["ticker_symbol"] == "QQQ"
    assert kwargs["risk_free_rate"] == 0.05
    assert kwargs["dividend_yield"] == 0.01
    assert kwargs["maximum_relative_spread"] == 0.15
    assert kwargs["minimum_days_to_expiry"] == 30