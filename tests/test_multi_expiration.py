"""
Tests for the multi-expiration options collector.

These tests verify expiration selection without making
live Yahoo Finance requests.
"""

from datetime import datetime, timedelta

import pytest

from app.market_data.multi_expiration import (
    select_expirations,
)
from app.market_data.yahoo_client import MARKET_TIMEZONE


def make_expiration(days_from_today: int) -> str:
    """
    Create an expiration date relative to today.

    This keeps tests valid regardless of when they run.
    """

    today = datetime.now(MARKET_TIMEZONE).date()

    expiration = today + timedelta(
        days=days_from_today
    )

    return expiration.isoformat()


# ============================================================
# TEST 1: SELECT ELIGIBLE EXPIRATIONS
# ============================================================

def test_select_eligible_expirations():

    expirations = [
        make_expiration(2),
        make_expiration(7),
        make_expiration(14),
        make_expiration(21),
    ]

    result = select_expirations(
        expirations=expirations,
        minimum_days_to_expiry=7,
        maximum_expirations=3,
    )

    assert len(result) == 3

    assert make_expiration(2) not in result


# ============================================================
# TEST 2: RESPECT MAXIMUM EXPIRATIONS
# ============================================================

def test_maximum_expirations():

    expirations = [
        make_expiration(7),
        make_expiration(14),
        make_expiration(21),
        make_expiration(28),
    ]

    result = select_expirations(
        expirations=expirations,
        minimum_days_to_expiry=7,
        maximum_expirations=2,
    )

    assert len(result) == 2


# ============================================================
# TEST 3: SORT EXPIRATIONS
# ============================================================

def test_expiration_sorting():

    expirations = [
        make_expiration(28),
        make_expiration(7),
        make_expiration(21),
        make_expiration(14),
    ]

    result = select_expirations(
        expirations=expirations,
        minimum_days_to_expiry=7,
        maximum_expirations=4,
    )

    assert result == sorted(result)


# ============================================================
# TEST 4: REMOVE DUPLICATES
# ============================================================

def test_duplicate_expirations():

    expiration = make_expiration(14)

    result = select_expirations(
        expirations=[
            expiration,
            expiration,
        ],
        minimum_days_to_expiry=7,
        maximum_expirations=6,
    )

    assert result == [expiration]


# ============================================================
# TEST 5: NO ELIGIBLE EXPIRATIONS
# ============================================================

def test_no_eligible_expirations():

    result = select_expirations(
        expirations=[
            make_expiration(1),
            make_expiration(2),
        ],
        minimum_days_to_expiry=7,
        maximum_expirations=6,
    )

    assert result == []


# ============================================================
# TEST 6: INVALID MINIMUM DAYS
# ============================================================

def test_invalid_minimum_days():

    with pytest.raises(ValueError):

        select_expirations(
            expirations=[],
            minimum_days_to_expiry=-1,
        )


# ============================================================
# TEST 7: INVALID MAXIMUM EXPIRATIONS
# ============================================================

def test_invalid_maximum_expirations():

    with pytest.raises(ValueError):

        select_expirations(
            expirations=[],
            maximum_expirations=0,
        )