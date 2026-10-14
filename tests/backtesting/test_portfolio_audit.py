"""Tests for independent portfolio concentration diagnostics."""

import pandas as pd
import pytest

from app.backtesting.portfolio_audit import analyze_concentration


def test_equal_weight_portfolio():
    results = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp("2025-01-02"),
                "Portfolio Value": 1000.0,
                "Cash": 0.0,
                "Position Values": {
                    "AAA": 500.0,
                    "BBB": 500.0,
                },
            }
        ]
    )

    audit = analyze_concentration(results)

    assert audit.iloc[0]["Number of Holdings"] == 2
    assert audit.iloc[0]["Largest Weight (%)"] == pytest.approx(50)
    assert audit.iloc[0]["Top 3 Weight (%)"] == pytest.approx(100)
    assert audit.iloc[0]["Concentration HHI"] == pytest.approx(0.5)
    assert audit.iloc[0]["Accounting Error ($)"] == pytest.approx(0)


def test_detects_accounting_difference():
    results = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp("2025-01-02"),
                "Portfolio Value": 1000.0,
                "Cash": 100.0,
                "Position Values": {"AAA": 800.0},
            }
        ]
    )

    audit = analyze_concentration(results)

    assert audit.iloc[0]["Accounting Error ($)"] == pytest.approx(-100)


def test_rejects_negative_position_values():
    results = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp("2025-01-02"),
                "Portfolio Value": 1000.0,
                "Cash": 0.0,
                "Position Values": {"AAA": -100.0},
            }
        ]
    )

    with pytest.raises(ValueError, match="Invalid position value"):
        analyze_concentration(results)


def test_rejects_duplicate_dates():
    row = {
        "Date": pd.Timestamp("2025-01-02"),
        "Portfolio Value": 1000.0,
        "Cash": 0.0,
        "Position Values": {"AAA": 1000.0},
    }

    with pytest.raises(ValueError, match="Duplicate dates"):
        analyze_concentration(pd.DataFrame([row, row]))
