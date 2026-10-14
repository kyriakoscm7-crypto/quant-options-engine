"""Tests for portfolio valuation-change diagnostics."""

import pandas as pd
import pytest

from app.backtesting.attribution import (
    analyze_position_changes,
    largest_position_changes,
)


def test_detects_position_value_changes():
    dates = pd.bdate_range("2025-01-01", periods=2)

    results = pd.DataFrame(
        [
            {
                "Date": dates[0],
                "Portfolio Value": 1000.0,
                "Cash": 0.0,
                "Position Values": {
                    "AAA": 500.0,
                    "BBB": 500.0,
                },
            },
            {
                "Date": dates[1],
                "Portfolio Value": 1100.0,
                "Cash": 0.0,
                "Position Values": {
                    "AAA": 600.0,
                    "BBB": 500.0,
                },
            },
        ]
    )

    changes = analyze_position_changes(results)

    aaa = changes.loc[changes["Ticker"] == "AAA"].iloc[0]

    assert aaa["Position Value Change ($)"] == pytest.approx(100)
    assert aaa["Portfolio Change ($)"] == pytest.approx(100)
    assert not bool(aaa["Possible Trading Activity"])


def test_flags_changes_in_holdings():
    dates = pd.bdate_range("2025-01-01", periods=2)

    results = pd.DataFrame(
        [
            {
                "Date": dates[0],
                "Portfolio Value": 1000.0,
                "Cash": 0.0,
                "Position Values": {"AAA": 1000.0},
            },
            {
                "Date": dates[1],
                "Portfolio Value": 1000.0,
                "Cash": 0.0,
                "Position Values": {"BBB": 1000.0},
            },
        ]
    )

    changes = analyze_position_changes(results)

    assert changes["Possible Trading Activity"].all()


def test_flags_cash_changes():
    dates = pd.bdate_range("2025-01-01", periods=2)

    results = pd.DataFrame(
        [
            {
                "Date": dates[0],
                "Portfolio Value": 1000.0,
                "Cash": 100.0,
                "Position Values": {"AAA": 900.0},
            },
            {
                "Date": dates[1],
                "Portfolio Value": 1000.0,
                "Cash": 200.0,
                "Position Values": {"AAA": 800.0},
            },
        ]
    )

    changes = analyze_position_changes(results)

    assert changes["Possible Trading Activity"].all()


def test_largest_changes_sorted_correctly():
    changes = pd.DataFrame(
        {
            "Position Value Change ($)": [10.0, -100.0, 50.0],
            "Ticker": ["A", "B", "C"],
        }
    )

    result = largest_position_changes(changes, top_n=2)

    assert result["Ticker"].tolist() == ["B", "C"]


def test_rejects_duplicate_dates():
    date = pd.Timestamp("2025-01-01")

    row = {
        "Date": date,
        "Portfolio Value": 1000.0,
        "Cash": 0.0,
        "Position Values": {"AAA": 1000.0},
    }

    with pytest.raises(ValueError, match="Duplicate portfolio dates"):
        analyze_position_changes(pd.DataFrame([row, row]))


def test_rejects_invalid_position_values():
    dates = pd.bdate_range("2025-01-01", periods=2)

    results = pd.DataFrame(
        [
            {
                "Date": dates[0],
                "Portfolio Value": 1000.0,
                "Cash": 0.0,
                "Position Values": {"AAA": 1000.0},
            },
            {
                "Date": dates[1],
                "Portfolio Value": 1000.0,
                "Cash": 0.0,
                "Position Values": {"AAA": -100.0},
            },
        ]
    )

    with pytest.raises(ValueError, match="Invalid position value"):
        analyze_position_changes(results)
