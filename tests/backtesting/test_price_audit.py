"""Tests for historical stock-price anomaly detection."""

import pandas as pd
import pytest

from app.backtesting.price_audit import detect_price_anomalies


def test_detects_large_positive_return():
    dates = pd.bdate_range("2025-01-01", periods=3)

    histories = {
        "AAA": pd.DataFrame(
            {"Close": [10.0, 20.0, 21.0]},
            index=dates,
        )
    }

    result = detect_price_anomalies(histories)

    assert len(result) == 1
    assert result.iloc[0]["Ticker"] == "AAA"
    assert result.iloc[0]["Daily Return (%)"] == pytest.approx(100)


def test_detects_large_negative_return():
    dates = pd.bdate_range("2025-01-01", periods=3)

    histories = {
        "BBB": pd.DataFrame(
            {"Close": [20.0, 8.0, 8.5]},
            index=dates,
        )
    }

    result = detect_price_anomalies(histories)

    assert len(result) == 1
    assert result.iloc[0]["Daily Return (%)"] == pytest.approx(-60)


def test_ignores_small_returns():
    dates = pd.bdate_range("2025-01-01", periods=3)

    histories = {
        "CCC": pd.DataFrame(
            {"Close": [100.0, 105.0, 103.0]},
            index=dates,
        )
    }

    result = detect_price_anomalies(histories)

    assert result.empty


def test_rejects_invalid_threshold():
    with pytest.raises(ValueError, match="threshold"):
        detect_price_anomalies({}, threshold=0)


def test_missing_price_does_not_create_false_return():
    dates = pd.bdate_range("2025-01-01", periods=3)

    histories = {
        "DDD": pd.DataFrame(
            {"Close": [10.0, None, 20.0]},
            index=dates,
        )
    }

    result = detect_price_anomalies(histories)

    assert result.empty


def test_rejects_duplicate_dates():
    dates = pd.to_datetime(
        ["2025-01-01", "2025-01-01", "2025-01-02"]
    )

    histories = {
        "EEE": pd.DataFrame(
            {"Close": [10.0, 20.0, 30.0]},
            index=dates,
        )
    }

    with pytest.raises(ValueError, match="Duplicate dates"):
        detect_price_anomalies(histories)
