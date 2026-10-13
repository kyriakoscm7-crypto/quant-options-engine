"""Tests for historical gap and volume intelligence."""

import numpy as np
import pandas as pd
import pytest

from app.market_data.gap_intelligence import calculate_gap_volume_signals


def make_history(
    rows: int = 30,
    *,
    gap_pct: float = 5.0,
    latest_volume: float = 2000.0,
) -> pd.DataFrame:
    """Create deterministic daily OHLCV data with a known final gap."""

    dates = pd.bdate_range("2025-01-02", periods=rows, tz="UTC")

    closes = np.full(rows, 100.0)
    opens = np.full(rows, 100.0)
    volumes = np.full(rows, 1000.0)

    opens[-1] = 100.0 * (1.0 + gap_pct / 100.0)
    volumes[-1] = latest_volume

    return pd.DataFrame(
        {
            "Date": dates,
            "Open": opens,
            "Close": closes,
            "Volume": volumes,
        }
    )


def test_positive_gap_and_relative_volume():
    history = make_history()

    result = calculate_gap_volume_signals(
        history,
        ticker="aapl",
        lookback=20,
        latest_session_complete=True,
    )

    assert result.ticker == "AAPL"
    assert result.opening_gap_pct == pytest.approx(5.0)
    assert result.relative_volume == pytest.approx(2.0)
    assert result.gap_direction == "Gap Up"


def test_negative_gap():
    history = make_history(gap_pct=-4.0)

    result = calculate_gap_volume_signals(
        history,
        "MSFT",
        latest_session_complete=True,
    )

    assert result.opening_gap_pct == pytest.approx(-4.0)
    assert result.gap_direction == "Gap Down"


def test_zero_gap():
    history = make_history(gap_pct=0.0)

    result = calculate_gap_volume_signals(
        history,
        "SPY",
        latest_session_complete=True,
    )

    assert result.opening_gap_pct == pytest.approx(0.0)
    assert result.gap_direction == "No Gap"


def test_zero_historical_gap_variance():
    history = make_history()

    result = calculate_gap_volume_signals(
        history,
        "AAPL",
        latest_session_complete=True,
    )

    assert result.gap_z_score is None


def test_gap_z_score_uses_only_prior_gaps():
    history = make_history()

    history.loc[5, "Open"] = 98.0
    history.loc[10, "Open"] = 102.0
    history.loc[15, "Open"] = 99.0
    history.loc[20, "Open"] = 101.0

    result = calculate_gap_volume_signals(
        history,
        "AAPL",
        lookback=20,
        latest_session_complete=True,
    )

    historical_gaps = (
        history["Open"] / history["Close"].shift(1) - 1
    ) * 100

    baseline = historical_gaps.iloc[-21:-1]

    expected = (
        5.0 - baseline.mean()
    ) / baseline.std(ddof=1)

    assert result.gap_z_score == pytest.approx(expected)


def test_latest_incomplete_session_is_excluded():
    history = make_history(rows=31)

    history.loc[29, "Open"] = 103.0
    history.loc[29, "Volume"] = 1500.0

    result = calculate_gap_volume_signals(
        history,
        "AAPL",
        latest_session_complete=False,
    )

    assert result.opening_gap_pct == pytest.approx(3.0)
    assert result.relative_volume == pytest.approx(1.5)
    assert result.latest_date == history.loc[29, "Date"]


def test_default_excludes_latest_session():
    history = make_history(rows=31)

    result = calculate_gap_volume_signals(
        history,
        "AAPL",
    )

    assert result.latest_date == history.loc[29, "Date"]
    assert result.opening_gap_pct == pytest.approx(0.0)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("Open", 0.0),
        ("Open", -1.0),
        ("Close", 0.0),
        ("Close", -1.0),
        ("Volume", -1.0),
        ("Open", np.inf),
        ("Close", np.nan),
        ("Volume", np.inf),
    ],
)
def test_invalid_market_data_is_rejected(column, value):
    history = make_history()

    history.loc[5, column] = value

    with pytest.raises(ValueError):
        calculate_gap_volume_signals(
            history,
            "AAPL",
            latest_session_complete=True,
        )


def test_duplicate_dates_are_rejected():
    history = make_history()

    history.loc[1, "Date"] = history.loc[0, "Date"]

    with pytest.raises(ValueError, match="duplicate"):
        calculate_gap_volume_signals(
            history,
            "AAPL",
            latest_session_complete=True,
        )


def test_insufficient_history_is_rejected():
    history = make_history(rows=10)

    with pytest.raises(ValueError, match="At least"):
        calculate_gap_volume_signals(
            history,
            "AAPL",
            lookback=20,
            latest_session_complete=True,
        )


def test_zero_historical_volume_is_rejected():
    history = make_history()

    history.loc[:28, "Volume"] = 0.0

    with pytest.raises(ValueError, match="average volume"):
        calculate_gap_volume_signals(
            history,
            "AAPL",
            latest_session_complete=True,
        )


def test_invalid_lookback_is_rejected():
    history = make_history()

    for lookback in [0, 4, 2.5, True]:
        with pytest.raises(ValueError):
            calculate_gap_volume_signals(
                history,
                "AAPL",
                lookback=lookback,
            )


def test_future_data_does_not_change_prior_signal():
    history = make_history(rows=31)

    original = calculate_gap_volume_signals(
        history,
        "AAPL",
        latest_session_complete=False,
    )

    modified = history.copy()

    modified.loc[30, "Open"] = 500.0
    modified.loc[30, "Close"] = 500.0
    modified.loc[30, "Volume"] = 10_000_000.0

    updated = calculate_gap_volume_signals(
        modified,
        "AAPL",
        latest_session_complete=False,
    )

    assert updated.opening_gap_pct == pytest.approx(
        original.opening_gap_pct
    )

    assert updated.relative_volume == pytest.approx(
        original.relative_volume
    )

    assert updated.gap_z_score == original.gap_z_score
