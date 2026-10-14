"""Tests for reproducible robustness-window research."""

import pandas as pd
import pytest

from app.backtesting.robustness import (
    TestWindow,
    generate_random_windows,
    summarize_window_returns,
)


def test_random_windows_are_reproducible():
    dates = pd.bdate_range("2024-01-01", periods=400)

    first = generate_random_windows(dates, 100, 10, seed=42)
    second = generate_random_windows(dates, 100, 10, seed=42)

    assert first == second
    assert len(first) == 10
    assert len({window.start for window in first}) == 10


def test_random_windows_have_correct_length():
    dates = pd.bdate_range("2024-01-01", periods=300)

    windows = generate_random_windows(dates, 50, 5, seed=7)

    for window in windows:
        selected = dates[
            (dates >= window.start) & (dates <= window.end)
        ]
        assert len(selected) == 50


def test_rejects_insufficient_history():
    dates = pd.bdate_range("2024-01-01", periods=10)

    with pytest.raises(ValueError, match="Not enough trading dates"):
        generate_random_windows(dates, 50, 2)


def test_rejects_too_many_unique_windows():
    dates = pd.bdate_range("2024-01-01", periods=10)

    with pytest.raises(ValueError, match="more unique windows"):
        generate_random_windows(dates, 9, 5)


def test_window_returns_are_calculated_correctly():
    dates = pd.bdate_range("2024-01-01", periods=3)

    strategy = pd.Series([100, 110, 120], index=dates)
    benchmark = pd.Series([100, 105, 110], index=dates)

    windows = [TestWindow(dates[0], dates[-1])]

    result = summarize_window_returns(
        strategy,
        benchmark,
        windows,
    )

    assert result.iloc[0]["Strategy Return (%)"] == pytest.approx(20)
    assert result.iloc[0]["SPY Return (%)"] == pytest.approx(10)
    assert result.iloc[0]["Excess Return (pp)"] == pytest.approx(10)
    assert bool(result.iloc[0]["Beat SPY"])


def test_rejects_duplicate_valuation_dates():
    dates = pd.to_datetime(
        ["2024-01-01", "2024-01-01", "2024-01-02"]
    )

    strategy = pd.Series([100, 110, 120], index=dates)
    benchmark = pd.Series([100, 105, 110], index=dates)

    with pytest.raises(ValueError, match="Duplicate valuation dates"):
        summarize_window_returns(
            strategy,
            benchmark,
            [TestWindow(dates[0], dates[-1])],
        )
