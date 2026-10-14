"""Tests for historical portfolio concentration analysis."""

import pandas as pd
import pytest

from app.backtesting.concentration import analyze_concentration


def test_equal_weight_portfolio():
    result = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp("2025-01-01"),
                "Portfolio Value": 1000.0,
                "Position Values": {
                    "A": 250.0,
                    "B": 250.0,
                    "C": 250.0,
                    "D": 250.0,
                },
            }
        ]
    )

    analysis = analyze_concentration(result)

    assert analysis.iloc[0]["Largest Weight (%)"] == 25.0
    assert analysis.iloc[0]["Top 3 Weight (%)"] == 75.0
    assert analysis.iloc[0]["Concentration HHI"] == 0.25
    assert bool(analysis.iloc[0]["Above 20%"])
    assert not bool(analysis.iloc[0]["Above 30%"])


def test_concentrated_portfolio():
    result = pd.DataFrame(
        [
            {
                "Date": pd.Timestamp("2026-01-29"),
                "Portfolio Value": 1000.0,
                "Position Values": {
                    "BNAI": 600.0,
                    "OTHER": 400.0,
                },
            }
        ]
    )

    analysis = analyze_concentration(result)

    assert analysis.iloc[0]["Largest Stock"] == "BNAI"
    assert analysis.iloc[0]["Largest Weight (%)"] == 60.0
    assert bool(analysis.iloc[0]["Above 50%"])


def test_missing_positions_column():
    result = pd.DataFrame(
        [{"Date": pd.Timestamp("2025-01-01"), "Portfolio Value": 1000}]
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        analyze_concentration(result)
