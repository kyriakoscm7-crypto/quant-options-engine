"""Safety tests for training-only forecasting experiments."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.feature_experiments import expected_calibration_error
from app.forecasting.ml_walk_forward import ml_walk_forward_predictions
from app.forecasting.research_splits import create_research_split


@pytest.fixture
def prices():
    """Generate deterministic synthetic prices without external data."""
    rng = np.random.default_rng(42)
    returns = rng.normal(0.0003, 0.012, 900)

    return pd.Series(
        100 * np.exp(np.cumsum(returns)),
        index=pd.date_range("2020-01-01", periods=900, freq="B"),
    )


def test_training_only_never_returns_validation_or_test(prices):
    predictions = ml_walk_forward_predictions(
        prices,
        horizons=(1, 5),
        training_window=300,
        step=20,
        training_only=True,
    )

    assert not predictions.empty
    assert set(predictions["Research Period"]) == {"Training"}


def test_training_only_forecast_indices_stay_inside_training(prices):
    predictions = ml_walk_forward_predictions(
        prices,
        horizons=(1, 5),
        training_window=300,
        step=20,
        training_only=True,
    )

    split = create_research_split(len(prices))

    assert not predictions.empty
    assert (
        predictions["Forecast Index"]
        + predictions["Horizon"]
        < split.training_end
    ).all()


def test_training_only_predictions_match_default_training_rows(prices):
    settings = dict(
        horizons=(1, 5),
        training_window=300,
        step=20,
    )

    training = ml_walk_forward_predictions(
        prices,
        **settings,
        training_only=True,
    )

    default = ml_walk_forward_predictions(
        prices,
        **settings,
    )

    expected = default.loc[
        default["Research Period"] == "Training"
    ].reset_index(drop=True)

    pd.testing.assert_frame_equal(training, expected)


def test_training_only_rejects_non_boolean(prices):
    with pytest.raises(ValueError, match="training_only"):
        ml_walk_forward_predictions(
            prices,
            training_only="yes",
        )


def test_calibration_error_is_zero_for_perfect_predictions():
    actual = np.array([0, 1, 0, 1])
    probability = np.array([0.0, 1.0, 0.0, 1.0])

    assert expected_calibration_error(actual, probability) == 0.0


def test_calibration_error_detects_miscalibration():
    actual = np.array([0, 0, 0, 0])
    probability = np.array([0.9, 0.9, 0.9, 0.9])

    assert expected_calibration_error(actual, probability) == pytest.approx(
        0.9
    )


@pytest.mark.parametrize(
    "actual, probability",
    [
        ([0, 1], [0.5]),
        ([0, 1], [0.5, 1.5]),
        ([0, 1], [0.5, float("nan")]),
        ([0, 2], [0.5, 0.5]),
    ],
)
def test_calibration_rejects_invalid_inputs(actual, probability):
    with pytest.raises(ValueError):
        expected_calibration_error(actual, probability)
