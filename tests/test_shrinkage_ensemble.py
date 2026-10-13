"""Tests for the conservative probability ensemble."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.shrinkage_ensemble import (
    add_ensemble_predictions,
    shrinkage_probability,
)


def make_predictions():
    return pd.DataFrame(
        {
            "Forecast Index": [300, 305, 310],
            "Historical Probability": [0.6, 0.4, 0.5],
            "ML Probability": [0.8, 0.2, 0.9],
        }
    )


def test_default_weight_is_25_percent():
    result = shrinkage_probability(0.6, 0.8)

    assert result.ml_weight == pytest.approx(0.25)
    assert result.probability_up == pytest.approx(0.65)


def test_zero_weight_uses_historical_only():
    result = shrinkage_probability(0.6, 0.8, ml_weight=0)

    assert result.probability_up == pytest.approx(0.6)


def test_full_weight_uses_ml_only():
    result = shrinkage_probability(0.6, 0.8, ml_weight=1)

    assert result.probability_up == pytest.approx(0.8)


def test_equal_probabilities_remain_unchanged():
    result = shrinkage_probability(0.7, 0.7)

    assert result.probability_up == pytest.approx(0.7)


def test_extreme_probabilities_remain_valid():
    for historical in (0.0, 1.0):
        for ml in (0.0, 1.0):
            result = shrinkage_probability(historical, ml)

            assert 0 <= result.probability_up <= 1


def test_dataframe_ensemble_calculation():
    result = add_ensemble_predictions(make_predictions())

    expected = [0.65, 0.35, 0.60]

    np.testing.assert_allclose(
        result["Ensemble Probability"].to_numpy(),
        expected,
    )


def test_dataframe_zero_weight():
    result = add_ensemble_predictions(
        make_predictions(),
        ml_weight=0,
    )

    pd.testing.assert_series_equal(
        result["Ensemble Probability"],
        result["Historical Probability"],
        check_names=False,
    )


def test_dataframe_full_weight():
    result = add_ensemble_predictions(
        make_predictions(),
        ml_weight=1,
    )

    pd.testing.assert_series_equal(
        result["Ensemble Probability"],
        result["ML Probability"],
        check_names=False,
    )


def test_original_dataframe_is_not_modified():
    original = make_predictions()
    before = original.copy(deep=True)

    add_ensemble_predictions(original)

    pd.testing.assert_frame_equal(original, before)


def test_existing_columns_are_preserved():
    original = make_predictions()

    result = add_ensemble_predictions(original)

    assert set(original.columns).issubset(result.columns)
    assert "Ensemble Probability" in result.columns


def test_dataframe_probabilities_remain_valid():
    result = add_ensemble_predictions(make_predictions())

    assert result["Ensemble Probability"].between(0, 1).all()


@pytest.mark.parametrize(
    "bad_weight",
    [-0.1, 1.1, np.nan, np.inf, True, "0.25"],
)
def test_invalid_weights_rejected(bad_weight):
    with pytest.raises(ValueError):
        shrinkage_probability(0.5, 0.5, bad_weight)


@pytest.mark.parametrize(
    "bad_probability",
    [-0.1, 1.1, np.nan, np.inf, True, "0.5"],
)
def test_invalid_probabilities_rejected(bad_probability):
    with pytest.raises(ValueError):
        shrinkage_probability(bad_probability, 0.5)


def test_missing_dataframe_columns_rejected():
    predictions = make_predictions().drop(
        columns=["ML Probability"]
    )

    with pytest.raises(ValueError):
        add_ensemble_predictions(predictions)


def test_invalid_dataframe_probabilities_rejected():
    predictions = make_predictions()
    predictions.loc[0, "ML Probability"] = 1.5

    with pytest.raises(ValueError):
        add_ensemble_predictions(predictions)


def test_non_numeric_dataframe_probabilities_rejected():
    predictions = make_predictions()
    predictions["ML Probability"] = ["0.8", "0.2", "0.9"]

    with pytest.raises(ValueError):
        add_ensemble_predictions(predictions)


def test_empty_dataframe_preserves_columns():
    predictions = make_predictions().iloc[:0]

    result = add_ensemble_predictions(predictions)

    assert result.empty
    assert "Ensemble Probability" in result.columns
