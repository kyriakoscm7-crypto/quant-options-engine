from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.market_data.yahoo_client import (
    calculate_time_to_expiration,
    is_valid_option_quote,
    normalize_timestamp,
    calculate_observation_age_hours
)


# TEST 1:
# A future expiration must have positive remaining time.
def test_future_expiration():

    market_timezone = ZoneInfo("America/New_York")

    today = datetime.now(market_timezone).date()

    future_date = today + timedelta(days=30)

    expiration = future_date.strftime("%Y-%m-%d")

    T = calculate_time_to_expiration(expiration)

    assert T > 0


# TEST 2:
# An expiration in the past must have zero remaining time.
def test_past_expiration():

    market_timezone = ZoneInfo("America/New_York")

    today = datetime.now(market_timezone).date()

    past_date = today - timedelta(days=30)

    expiration = past_date.strftime("%Y-%m-%d")

    T = calculate_time_to_expiration(expiration)

    assert T == 0.0


# TEST 3:
# An expiration approximately one year away should
# produce approximately one year of remaining time.
def test_one_year_expiration():

    market_timezone = ZoneInfo("America/New_York")

    today = datetime.now(market_timezone).date()

    future_date = today + timedelta(days=365)

    expiration = future_date.strftime("%Y-%m-%d")

    T = calculate_time_to_expiration(expiration)

    assert T == pytest.approx(1.0, abs=0.01)


# TEST 4:
# Invalid expiration strings must be rejected.
def test_invalid_expiration_format():

    with pytest.raises(ValueError):

        calculate_time_to_expiration("not-a-date")


# TEST 5:
# A normal option quote should pass validation.
def test_valid_option_quote():

    assert is_valid_option_quote(
        strike=100,
        bid=9.80,
        ask=10.20
    ) is True


# TEST 6:
# Reject quotes with excessively wide bid-ask spreads.
def test_wide_bid_ask_spread():

    assert is_valid_option_quote(
        strike=100,
        bid=1.00,
        ask=2.00
    ) is False


# TEST 7:
# Reject crossed markets where bid exceeds ask.
def test_crossed_market():

    assert is_valid_option_quote(
        strike=100,
        bid=10.50,
        ask=10.00
    ) is False


# TEST 8:
# Reject zero bids.
def test_zero_bid():

    assert is_valid_option_quote(
        strike=100,
        bid=0,
        ask=1.00
    ) is False


# TEST 9:
# Reject missing quote values.
def test_missing_quote():

    assert is_valid_option_quote(
        strike=100,
        bid=None,
        ask=10.00
    ) is False


# TEST 10:
# Reject non-finite quote values.
def test_infinite_quote():

    assert is_valid_option_quote(
        strike=100,
        bid=float("inf"),
        ask=10.00
    ) is False


# TEST 11:
# Verify that we can configure the maximum relative spread.
def test_custom_spread_threshold():

    # Bid = 9, Ask = 11, midpoint = 10.
    # Relative spread = 20%.

    assert is_valid_option_quote(
        strike=100,
        bid=9,
        ask=11,
        maximum_relative_spread=0.30
    ) is True

    assert is_valid_option_quote(
        strike=100,
        bid=9,
        ask=11,
        maximum_relative_spread=0.10
    ) is False


    # TEST 12:
# Verify that timezone-aware timestamps convert to UTC.
def test_normalize_timestamp():

    result = normalize_timestamp(
        "2026-10-12T12:00:00-04:00"
    )

    assert result.startswith(
        "2026-10-12T16:00:00"
    )

    assert result.endswith(
        "+00:00"
    )


# TEST 13:
# Missing timestamps should return None.
def test_missing_timestamp():

    assert normalize_timestamp(None) is None


# TEST 14:
# Naive timestamps should be rejected.
def test_naive_timestamp():

    assert normalize_timestamp(
        "2026-10-12T12:00:00"
    ) is None


# TEST 15:
# Verify observation age calculations.
def test_observation_age():

    observation = "2026-10-12T12:00:00+00:00"

    reference = "2026-10-12T15:30:00+00:00"

    result = calculate_observation_age_hours(
        observation,
        reference
    )

    assert result == 3.5


# TEST 16:
# Future observations should not produce negative ages.
def test_future_observation():

    observation = "2026-10-12T16:00:00+00:00"

    reference = "2026-10-12T15:00:00+00:00"

    result = calculate_observation_age_hours(
        observation,
        reference
    )

    assert result is None