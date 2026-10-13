"""Tests for matched regularization candidate generation."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting import regularization_candidates as module


@pytest.fixture
def prices():
    return pd.Series(np.linspace(100, 200, 1000))


@pytest.fixture
def mock_predictions(monkeypatch):
    calls = []

    def fake_walk_forward(
        close_prices,
        horizons,
        training_window,
        step,
        regularization_c,
    ):
        calls.append(regularization_c)

        return pd.DataFrame(
            {
                "Forecast Index": [400, 405, 410],
                "Horizon": [5, 5, 5],
                "Research Period": [
                    "Training",
                    "Training",
                    "Validation",
                ],
                "Actual Up": [1, 0, 1],
                "Historical Probability": [0.55, 0.45, 0.60],
                "ML Probability": [
                    0.50 + regularization_c * 0.01,
                    0.50 - regularization_c * 0.01,
                    0.55,
                ],
            }
        )

    monkeypatch.setattr(
        module,
        "ml_walk_forward_predictions",
        fake_walk_forward,
    )

    return calls


def test_all_regularization_values_are_evaluated(
    prices, mock_predictions
):
    result = module.generate_regularization_candidates(prices)

    assert mock_predictions == [0.001, 0.01, 0.1, 1.0]
    assert len(result) == 3

    for value in mock_predictions:
        assert f"ML C={value:g}" in result.columns


def test_predictions_are_correctly_aligned(
    prices, mock_predictions
):
    result = module.generate_regularization_candidates(prices)

    assert result["Forecast Index"].tolist() == [400, 405, 410]
    assert result["Actual Up"].tolist() == [1, 0, 1]


def test_training_and_validation_periods_preserved(
    prices, mock_predictions
):
    result = module.generate_regularization_candidates(prices)

    assert result["Research Period"].tolist() == [
        "Training",
        "Training",
        "Validation",
    ]


def test_candidate_probabilities_match_expected_values(
    prices, mock_predictions
):
    result = module.generate_regularization_candidates(prices)

    assert result.loc[0, "ML C=0.001"] == pytest.approx(
        0.50001
    )
    assert result.loc[0, "ML C=1"] == pytest.approx(0.51)


def test_empty_regularization_values_rejected(prices):
    with pytest.raises(ValueError):
        module.generate_regularization_candidates(
            prices,
            regularization_values=(),
        )


@pytest.mark.parametrize(
    "values",
    [
        (0,),
        (-1,),
        (float("nan"),),
        (float("inf"),),
        (True,),
        (0.1, 0.1),
    ],
)
def test_invalid_regularization_values_rejected(prices, values):
    with pytest.raises(ValueError):
        module.generate_regularization_candidates(
            prices,
            regularization_values=values,
        )


def test_mismatched_forecast_dates_rejected(
    prices, monkeypatch
):
    def fake_walk_forward(
        close_prices,
        horizons,
        training_window,
        step,
        regularization_c,
    ):
        index = 400 if regularization_c == 0.1 else 405

        return pd.DataFrame(
            {
                "Forecast Index": [index],
                "Horizon": [5],
                "Research Period": ["Training"],
                "Actual Up": [1],
                "Historical Probability": [0.5],
                "ML Probability": [0.6],
            }
        )

    monkeypatch.setattr(
        module,
        "ml_walk_forward_predictions",
        fake_walk_forward,
    )

    with pytest.raises(ValueError, match="mismatched"):
        module.generate_regularization_candidates(
            prices,
            regularization_values=(0.1, 1.0),
        )


def test_reserved_test_predictions_rejected(
    prices, monkeypatch
):
    def fake_walk_forward(
        close_prices,
        horizons,
        training_window,
        step,
        regularization_c,
    ):
        return pd.DataFrame(
            {
                "Forecast Index": [400],
                "Horizon": [5],
                "Research Period": ["Test"],
                "Actual Up": [1],
                "Historical Probability": [0.5],
                "ML Probability": [0.6],
            }
        )

    monkeypatch.setattr(
        module,
        "ml_walk_forward_predictions",
        fake_walk_forward,
    )

    with pytest.raises(ValueError, match="Reserved test"):
        module.generate_regularization_candidates(
            prices,
            regularization_values=(0.1,),
        )


@pytest.mark.parametrize(
    "invalid_probability",
    [-0.1, 1.1, float("nan"), float("inf")],
)
def test_invalid_probabilities_rejected(
    prices, monkeypatch, invalid_probability
):
    def fake_walk_forward(
        close_prices,
        horizons,
        training_window,
        step,
        regularization_c,
    ):
        return pd.DataFrame(
            {
                "Forecast Index": [400],
                "Horizon": [5],
                "Research Period": ["Training"],
                "Actual Up": [1],
                "Historical Probability": [0.5],
                "ML Probability": [invalid_probability],
            }
        )

    monkeypatch.setattr(
        module,
        "ml_walk_forward_predictions",
        fake_walk_forward,
    )

    with pytest.raises(ValueError):
        module.generate_regularization_candidates(
            prices,
            regularization_values=(0.1,),
        )


def test_duplicate_forecast_keys_rejected(
    prices, monkeypatch
):
    def fake_walk_forward(
        close_prices,
        horizons,
        training_window,
        step,
        regularization_c,
    ):
        return pd.DataFrame(
            {
                "Forecast Index": [400, 400],
                "Horizon": [5, 5],
                "Research Period": ["Training", "Training"],
                "Actual Up": [1, 0],
                "Historical Probability": [0.5, 0.5],
                "ML Probability": [0.6, 0.4],
            }
        )

    monkeypatch.setattr(
        module,
        "ml_walk_forward_predictions",
        fake_walk_forward,
    )

    with pytest.raises(ValueError, match="Duplicate"):
        module.generate_regularization_candidates(
            prices,
            regularization_values=(0.1,),
        )
