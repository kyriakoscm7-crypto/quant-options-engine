"""Tests for the four-configuration training-only ML experiment."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting import feature_experiments
from app.forecasting.feature_experiments import (
    CONFIGURATIONS,
    expected_calibration_error,
    run_feature_experiments,
)


def test_four_configurations_are_defined():
    assert len(CONFIGURATIONS) == 4
    assert [len(config.features) for config in CONFIGURATIONS] == [
        9, 9, 4, 4
    ]
    assert [config.regularization_c for config in CONFIGURATIONS] == [
        0.1, 0.01, 0.1, 0.01
    ]


def test_calibration_error_known_example():
    actual = np.array([0, 0, 1, 1])
    probability = np.array([0.1, 0.3, 0.7, 0.9])

    assert expected_calibration_error(
        actual, probability, bins=2
    ) == pytest.approx(0.2)


def test_experiment_scores_training_only(monkeypatch):
    calls = []

    def fake_walk_forward(close_prices, **kwargs):
        calls.append(kwargs)

        assert kwargs["training_only"] is True

        return pd.DataFrame(
            {
                "Forecast Index": [100, 101, 102, 103, 800, 900],
                "Horizon": [5, 5, 5, 5, 5, 5],
                "Research Period": [
                    "Training",
                    "Training",
                    "Training",
                    "Training",
                    "Validation",
                    "Test",
                ],
                "Actual Up": [1, 0, 1, 0, 1, 0],
                "ML Probability": [0.8, 0.2, 0.7, 0.3, 0.0, 1.0],
                "Historical Probability": [
                    0.6, 0.4, 0.6, 0.4, 0.5, 0.5
                ],
            }
        )

    monkeypatch.setattr(
        feature_experiments,
        "ml_walk_forward_predictions",
        fake_walk_forward,
    )

    results = run_feature_experiments(
        pd.Series([100.0, 101.0]),
        horizons=(5,),
    )

    assert len(calls) == 4
    assert len(results) == 4
    assert set(results["Configuration"]) == {
        config.name for config in CONFIGURATIONS
    }
    assert (results["N"] == 4).all()
    assert (results["Horizon"] == 5).all()
    assert results["Brier"].to_numpy() == pytest.approx([0.065] * 4)
    assert results["Historical Brier"].to_numpy() == pytest.approx([0.16] * 4)
    assert (results["Brier Improvement"] > 0).all()
    assert results["ROC AUC"].between(0, 1).all()
    assert results["Calibration Error"].between(0, 1).all()


def test_experiment_skips_empty_training_predictions(monkeypatch):
    def fake_walk_forward(close_prices, **kwargs):
        return pd.DataFrame(
            {
                "Horizon": [5],
                "Research Period": ["Validation"],
                "Actual Up": [1],
                "ML Probability": [0.8],
                "Historical Probability": [0.6],
            }
        )

    monkeypatch.setattr(
        feature_experiments,
        "ml_walk_forward_predictions",
        fake_walk_forward,
    )

    results = run_feature_experiments(
        pd.Series([100.0, 101.0]),
        horizons=(5,),
    )

    assert results.empty
