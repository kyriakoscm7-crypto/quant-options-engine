"""Tests for historical portfolio performance calculations."""

import pandas as pd
import pytest

from app.backtesting.performance import calculate_performance


def test_total_return_uses_initial_capital():
    values = pd.Series(
        [9_900.0, 11_000.0, 13_789.0],
        index=pd.to_datetime(
            ["2021-10-04", "2023-10-04", "2026-10-13"]
        ),
    )

    result = calculate_performance(values, initial_capital=10_000)

    assert result["total_return_pct"] == pytest.approx(37.89)
    assert result["final_value"] == pytest.approx(13_789)


def test_initial_loss_is_included_in_drawdown():
    values = pd.Series(
        [9_000.0, 9_500.0],
        index=pd.to_datetime(
            ["2025-01-02", "2025-01-03"]
        ),
    )

    result = calculate_performance(values, initial_capital=10_000)

    assert result["max_drawdown_pct"] == pytest.approx(-10.0)


def test_rejects_nonpositive_capital():
    values = pd.Series(
        [100.0, 110.0],
        index=pd.to_datetime(
            ["2025-01-02", "2025-01-03"]
        ),
    )

    with pytest.raises(ValueError, match="Initial capital"):
        calculate_performance(values, initial_capital=0)


def test_rejects_duplicate_dates():
    values = pd.Series(
        [100.0, 110.0],
        index=pd.to_datetime(
            ["2025-01-02", "2025-01-02"]
        ),
    )

    with pytest.raises(ValueError, match="unique"):
        calculate_performance(values, initial_capital=100)
