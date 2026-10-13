"""Tests for probability calibration diagnostics."""

import pandas as pd
import pytest

from app.forecasting.calibration import analyze_calibration


def make_predictions(probabilities, outcomes):
    return pd.DataFrame(
        {
            "Probability Up": probabilities,
            "Actual Up": outcomes,
        }
    )


def test_perfect_predictions_have_zero_error():
    data = make_predictions(
        [0.0, 1.0, 1.0, 0.0],
        [0, 1, 1, 0],
    )

    summary, calibration_bins = analyze_calibration(data)

    assert summary.brier_score == pytest.approx(0.0)
    assert summary.expected_calibration_error == pytest.approx(0.0)
    assert summary.maximum_calibration_error == pytest.approx(0.0)
    assert sum(b.predictions for b in calibration_bins) == 4


def test_perfectly_calibrated_groups():
    data = make_predictions(
        [0.25] * 4 + [0.75] * 4,
        [1, 0, 0, 0, 1, 1, 1, 0],
    )

    summary, calibration_bins = analyze_calibration(data)

    assert summary.expected_calibration_error == pytest.approx(0.0)
    assert summary.brier_score == pytest.approx(0.1875)
    assert len(calibration_bins) == 2


def test_overconfident_predictions_are_detected():
    data = make_predictions(
        [0.9, 0.9, 0.9, 0.9],
        [1, 0, 0, 0],
    )

    summary, calibration_bins = analyze_calibration(data)

    assert summary.observed_up_frequency == pytest.approx(0.25)
    assert summary.average_predicted_probability == pytest.approx(0.9)
    assert summary.expected_calibration_error == pytest.approx(0.65)
    assert summary.maximum_calibration_error == pytest.approx(0.65)
    assert len(calibration_bins) == 1


def test_probability_one_belongs_to_final_bin():
    data = make_predictions([0.0, 1.0], [0, 1])

    summary, calibration_bins = analyze_calibration(data, bins=5)

    assert summary.predictions == 2
    assert calibration_bins[0].lower_bound == pytest.approx(0.0)
    assert calibration_bins[-1].upper_bound == pytest.approx(1.0)


def test_all_predictions_are_counted():
    data = make_predictions(
        [0.0, 0.1, 0.5, 0.9, 1.0],
        [0, 0, 1, 1, 1],
    )

    summary, calibration_bins = analyze_calibration(data)

    assert summary.predictions == 5
    assert sum(b.predictions for b in calibration_bins) == 5


@pytest.mark.parametrize(
    "probability",
    [-0.1, 1.1, float("nan"), float("inf")],
)
def test_invalid_probabilities_are_rejected(probability):
    data = make_predictions([probability], [1])

    with pytest.raises(ValueError):
        analyze_calibration(data)


@pytest.mark.parametrize(
    "outcome",
    [-1, 2, 0.5, float("nan")],
)
def test_invalid_outcomes_are_rejected(outcome):
    data = make_predictions([0.5], [outcome])

    with pytest.raises(ValueError):
        analyze_calibration(data)


def test_empty_predictions_are_rejected():
    data = make_predictions([], [])

    with pytest.raises(ValueError):
        analyze_calibration(data)


def test_missing_columns_are_rejected():
    data = pd.DataFrame({"Probability Up": [0.5]})

    with pytest.raises(ValueError):
        analyze_calibration(data)


@pytest.mark.parametrize("bins", [0, 1, -5, True, 2.5])
def test_invalid_bin_counts_are_rejected(bins):
    data = make_predictions([0.5], [1])

    with pytest.raises(ValueError):
        analyze_calibration(data, bins=bins)


def test_invalid_input_type_is_rejected():
    with pytest.raises(TypeError):
        analyze_calibration([0.5, 0.7])
