"""
Tests for the 3D volatility visualization data preparation.

These tests use synthetic data and do not require
live Yahoo Finance requests.
"""

import pandas as pd
import pytest

from app.visualization.volatility_surface_3d import (
    prepare_surface_data,
)


# ============================================================
# SYNTHETIC TEST DATA
# ============================================================

@pytest.fixture
def sample_surface_data():

    return pd.DataFrame({
        "Moneyness": [
            0.90,
            0.97,
            1.00,
            1.03,
            1.10,
        ],
        "TimeToExpiration": [
            0.02,
            0.02,
            0.03,
            0.04,
            0.05,
        ],
        "ImpliedVolatility": [
            15.0,
            12.0,
            11.0,
            12.5,
            16.0,
        ],
        "Strike": [
            700,
            750,
            775,
            800,
            850,
        ],
        "Expiration": [
            "2026-10-19",
            "2026-10-19",
            "2026-10-23",
            "2026-10-30",
            "2026-10-30",
        ],
    })


# ============================================================
# TEST 1: MONEYNESS FILTERING
# ============================================================

def test_moneyness_filtering(sample_surface_data):

    result = prepare_surface_data(
        sample_surface_data,
        minimum_moneyness=0.95,
        maximum_moneyness=1.05,
    )

    assert len(result) == 3

    assert result["Moneyness"].between(
        0.95,
        1.05
    ).all()


# ============================================================
# TEST 2: DAYS TO EXPIRATION
# ============================================================

def test_days_to_expiration(sample_surface_data):

    result = prepare_surface_data(
        sample_surface_data
    )

    assert "DaysToExpiration" in result.columns

    assert result["DaysToExpiration"].iloc[0] == pytest.approx(
        0.02 * 365.0
    )


# ============================================================
# TEST 3: ORIGINAL DATA IS NOT MODIFIED
# ============================================================

def test_original_dataframe_unchanged(sample_surface_data):

    original_columns = list(
        sample_surface_data.columns
    )

    prepare_surface_data(
        sample_surface_data
    )

    assert list(
        sample_surface_data.columns
    ) == original_columns


# ============================================================
# TEST 4: INVALID MONEYNESS RANGE
# ============================================================

def test_invalid_moneyness_range(sample_surface_data):

    with pytest.raises(ValueError):

        prepare_surface_data(
            sample_surface_data,
            minimum_moneyness=1.05,
            maximum_moneyness=0.95,
        )


# ============================================================
# TEST 5: MISSING REQUIRED COLUMN
# ============================================================

def test_missing_required_column(sample_surface_data):

    incomplete = sample_surface_data.drop(
        columns=["ImpliedVolatility"]
    )

    with pytest.raises(ValueError):

        prepare_surface_data(
            incomplete
        )


# ============================================================
# TEST 6: NEGATIVE IMPLIED VOLATILITY
# ============================================================

def test_negative_implied_volatility(sample_surface_data):

    modified = sample_surface_data.copy()

    modified.loc[
        modified.index[2],
        "ImpliedVolatility"
    ] = -10.0

    result = prepare_surface_data(
        modified
    )

    assert (
        result["ImpliedVolatility"] > 0
    ).all()


# ============================================================
# TEST 7: NEGATIVE TIME TO EXPIRATION
# ============================================================

def test_negative_time_to_expiration(sample_surface_data):

    modified = sample_surface_data.copy()

    modified.loc[
        modified.index[2],
        "TimeToExpiration"
    ] = -0.01

    result = prepare_surface_data(
        modified
    )

    assert (
        result["TimeToExpiration"] > 0
    ).all()