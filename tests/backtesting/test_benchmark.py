"""Tests for aligned benchmark simulation."""

import pandas as pd
import pytest

from app.backtesting.benchmark import simulate_buy_and_hold


def test_benchmark_buys_at_execution_open():
    dates = pd.to_datetime(
        ["2025-01-02", "2025-01-03", "2025-01-06"]
    )

    benchmark = pd.DataFrame(
        {
            "Open": [100.0, 110.0, 120.0],
            "Close": [105.0, 115.0, 125.0],
        },
        index=dates,
    )

    values = simulate_buy_and_hold(
        benchmark,
        execution_date=dates[1],
        end_date=dates[2],
        initial_capital=10_000,
        transaction_cost=0,
    )

    expected_shares = 10_000 / 110.0

    assert values.iloc[0] == pytest.approx(
        expected_shares * 115.0
    )
    assert values.iloc[-1] == pytest.approx(
        expected_shares * 125.0
    )


def test_benchmark_includes_transaction_cost():
    dates = pd.to_datetime(["2025-01-02", "2025-01-03"])

    benchmark = pd.DataFrame(
        {
            "Open": [100.0, 100.0],
            "Close": [100.0, 100.0],
        },
        index=dates,
    )

    values = simulate_buy_and_hold(
        benchmark,
        execution_date=dates[0],
        end_date=dates[1],
        initial_capital=10_000,
        transaction_cost=0.01,
    )

    assert values.iloc[-1] == pytest.approx(
        10_000 / 1.01
    )


def test_missing_execution_date_raises():
    dates = pd.to_datetime(["2025-01-02", "2025-01-03"])

    benchmark = pd.DataFrame(
        {
            "Open": [100.0, 100.0],
            "Close": [100.0, 100.0],
        },
        index=dates,
    )

    with pytest.raises(ValueError, match="Execution date"):
        simulate_buy_and_hold(
            benchmark,
            execution_date=pd.Timestamp("2025-01-04"),
            end_date=dates[-1],
        )
