"""Tests for historical ranking prediction accuracy."""

import pandas as pd
import pytest

from app.backtesting.prediction_accuracy import (
    evaluate_prediction_accuracy,
)


def test_perfect_ranking_has_positive_correlation():
    predictions = pd.DataFrame(
        {
            "date": ["2025-01-01"] * 10,
            "ticker": [f"STOCK{i}" for i in range(10)],
            "score": list(range(100, 90, -1)),
            "future_return": [
                0.10, 0.09, 0.08, 0.07, 0.06,
                0.05, 0.04, 0.03, 0.02, 0.01,
            ],
        }
    )

    result = evaluate_prediction_accuracy(predictions)

    assert result["mean_spearman_correlation"] == pytest.approx(1.0)
    assert result["mean_top_bottom_spread"] > 0
    assert result["top_group_hit_rate"] == 1.0


def test_reversed_ranking_has_negative_correlation():
    predictions = pd.DataFrame(
        {
            "date": ["2025-01-01"] * 10,
            "ticker": [f"STOCK{i}" for i in range(10)],
            "score": list(range(100, 90, -1)),
            "future_return": [
                0.01, 0.02, 0.03, 0.04, 0.05,
                0.06, 0.07, 0.08, 0.09, 0.10,
            ],
        }
    )

    result = evaluate_prediction_accuracy(predictions)

    assert result["mean_spearman_correlation"] == pytest.approx(-1.0)
    assert result["mean_top_bottom_spread"] < 0
    assert result["top_group_hit_rate"] == 0.0


def test_missing_required_column_raises():
    predictions = pd.DataFrame(
        {
            "date": ["2025-01-01"],
            "ticker": ["TEST"],
            "score": [90],
        }
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        evaluate_prediction_accuracy(predictions)
