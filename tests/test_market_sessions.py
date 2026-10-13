"""Tests for NYSE market-session classification."""

import pandas as pd
import pytest

from app.market_data.market_sessions import get_market_session_status


def test_market_open():
    result = get_market_session_status(
        "2026-10-13",
        pd.Timestamp("2026-10-13 15:00:00", tz="UTC"),
    )
    assert result.is_completed is False
    assert result.status == "In Progress / Not Yet Closed"


def test_immediately_after_close():
    result = get_market_session_status(
        "2026-10-13",
        pd.Timestamp("2026-10-13 20:15:00", tz="UTC"),
    )
    assert result.is_completed is False
    assert result.status == "Awaiting Data Finalization"


def test_after_finalization_delay():
    result = get_market_session_status(
        "2026-10-13",
        pd.Timestamp("2026-10-13 20:31:00", tz="UTC"),
    )
    assert result.is_completed is True
    assert result.status == "Completed"


def test_completed_previous_session():
    result = get_market_session_status(
        "2026-10-12",
        pd.Timestamp("2026-10-13 15:00:00", tz="UTC"),
    )
    assert result.is_completed is True
    assert result.is_current_session is False


@pytest.mark.parametrize(
    "date",
    [
        "2026-10-10",  # Saturday
        "2026-10-11",  # Sunday
        "2026-12-25",  # Christmas
        "2026-01-01",  # New Year's Day
    ],
)
def test_non_trading_days_rejected(date):
    with pytest.raises(ValueError, match="not an NYSE trading session"):
        get_market_session_status(date)


def test_early_close():
    result = get_market_session_status(
        "2026-11-27",
        pd.Timestamp("2026-11-27 18:45:00", tz="UTC"),
    )
    assert result.is_completed is True


def test_early_close_before_finalization():
    result = get_market_session_status(
        "2026-11-27",
        pd.Timestamp("2026-11-27 18:15:00", tz="UTC"),
    )
    assert result.is_completed is False
    assert result.status == "Awaiting Data Finalization"


def test_naive_timestamp_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        get_market_session_status(
            "2026-10-13",
            pd.Timestamp("2026-10-13 15:00:00"),
        )


def test_market_close_uses_exchange_calendar():
    result = get_market_session_status(
        "2026-11-27",
        pd.Timestamp("2026-11-27 18:00:00", tz="UTC"),
    )
    assert result.market_close == pd.Timestamp(
        "2026-11-27 18:00:00", tz="UTC"
    )
