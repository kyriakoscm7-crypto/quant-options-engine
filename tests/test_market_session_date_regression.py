"""Regression tests for daily trading-date normalization."""

import pandas as pd

from app.market_data.market_sessions import get_market_session_status


def test_utc_midnight_preserves_trading_date():
    status = get_market_session_status(
        pd.Timestamp("2026-10-13 00:00:00", tz="UTC"),
        checked_at=pd.Timestamp("2026-10-14 12:00:00", tz="UTC"),
    )

    assert status.session_date == "2026-10-13"
    assert status.is_completed


def test_monday_utc_midnight_is_not_sunday():
    status = get_market_session_status(
        pd.Timestamp("2026-10-19 00:00:00", tz="UTC"),
        checked_at=pd.Timestamp("2026-10-20 12:00:00", tz="UTC"),
    )

    assert status.session_date == "2026-10-19"
    assert status.is_completed


def test_naive_trading_date_is_preserved():
    status = get_market_session_status(
        pd.Timestamp("2026-10-13"),
        checked_at=pd.Timestamp("2026-10-14 12:00:00", tz="UTC"),
    )

    assert status.session_date == "2026-10-13"


def test_actual_check_time_still_uses_timezone_conversion():
    status = get_market_session_status(
        pd.Timestamp("2026-10-13", tz="UTC"),
        checked_at=pd.Timestamp(
            "2026-10-13 17:00:00",
            tz="America/New_York",
        ),
    )

    assert status.checked_at == pd.Timestamp(
        "2026-10-13 21:00:00",
        tz="UTC",
    )
    assert status.is_completed
