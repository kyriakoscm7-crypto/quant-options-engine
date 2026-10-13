"""Integration tests for gap intelligence in the market scanner."""

from unittest.mock import patch

import pandas as pd
import pytest

from app.market_data.market_scanner import scan_market


def make_gap_history():
    """Create synthetic daily candles with a distinctive final-session gap."""
    dates = pd.bdate_range("2026-09-01", periods=30, tz="UTC")
    dates = dates[dates <= pd.Timestamp("2026-10-13", tz="UTC")]

    if dates[-1] != pd.Timestamp("2026-10-13", tz="UTC"):
        dates = dates.append(
            pd.DatetimeIndex([pd.Timestamp("2026-10-13", tz="UTC")])
        )

    count = len(dates)

    history = pd.DataFrame(
        {
            "Date": dates,
            "Open": [100.0] * count,
            "High": [110.0] * count,
            "Low": [90.0] * count,
            "Close": [100.0] * count,
            "Volume": [1_000_000] * count,
        }
    )

    history.loc[history.index[-2], "Open"] = 102.0
    history.loc[history.index[-1], "Open"] = 110.0
    history.loc[history.index[-1], "Volume"] = 3_000_000

    return history


@patch("app.market_data.market_scanner.fetch_stock_history")
@patch("app.market_data.market_scanner.get_market_session_status")
def test_scanner_excludes_incomplete_session(mock_session, mock_fetch):
    mock_fetch.return_value = make_gap_history()
    mock_session.return_value.is_completed = False

    result = scan_market("AAPL")

    assert result.loc[0, "Gap Status"] == "OK"
    assert result.loc[0, "Opening Gap (%)"] == pytest.approx(2.0)
    assert result.loc[0, "Relative Volume"] == pytest.approx(1.0)
    assert result.loc[0, "Gap Signal Date"] == "2026-10-12"


@patch("app.market_data.market_scanner.fetch_stock_history")
@patch("app.market_data.market_scanner.get_market_session_status")
def test_scanner_includes_completed_session(mock_session, mock_fetch):
    mock_fetch.return_value = make_gap_history()
    mock_session.return_value.is_completed = True

    result = scan_market("AAPL")

    assert result.loc[0, "Gap Status"] == "OK"
    assert result.loc[0, "Opening Gap (%)"] == pytest.approx(10.0)
    assert result.loc[0, "Relative Volume"] == pytest.approx(3.0)
    assert result.loc[0, "Gap Signal Date"] == "2026-10-13"


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scanner_handles_insufficient_gap_history(mock_fetch):
    mock_fetch.return_value = pd.DataFrame(
        {
            "Date": pd.bdate_range("2026-10-01", periods=3, tz="UTC"),
            "Open": [100.0, 101.0, 102.0],
            "High": [105.0, 106.0, 107.0],
            "Low": [95.0, 96.0, 97.0],
            "Close": [100.0, 101.0, 102.0],
            "Volume": [1000, 1100, 1200],
        }
    )

    result = scan_market("AAPL")

    assert result.loc[0, "Status"] == "OK"
    assert result.loc[0, "Gap Status"].startswith("Unavailable:")
    assert pd.isna(result.loc[0, "Opening Gap (%)"])
