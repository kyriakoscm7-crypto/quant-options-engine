"""Tests for probability calibration and discrimination diagnostics."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.calibration_diagnostics import analyze_calibration


def test_perfect_predictions():
    actual = np.array([0, 1, 0, 1])
    probabilities = actual.astype(float)

    report = analyze_calibration(actual, probabilities)

    assert report.brier_score == pytest.approx(0.0)
    assert report.log_loss == pytest.approx(0.0, abs=1e-10)
    assert report.expected_calibration_error == pytest.approx(0.0)
    assert report.maximum_calibration_error == pytest.approx(0.0)
    assert report.roc_auc == pytest.approx(1.0)


def test_neutral_probabilities():
    actual = np.array([0, 1, 0, 1])
    probabilities = np.full(4, 0.5)

    report = analyze_calibration(actual, probabilities)

    assert report.brier_score == pytest.approx(0.25)
    assert report.log_loss == pytest.approx(np.log(2))
    assert report.expected_calibration_error == pytest.approx(0.0)
    assert report.probability_std == pytest.approx(0.0)
    assert report.roc_auc == pytest.approx(0.5)


def test_known_brier_score():
    actual = np.array([1, 0])
    probabilities = np.array([0.8, 0.3])

    report = analyze_calibration(actual, probabilities)

    assert report.brier_score == pytest.approx(0.065)


def test_known_log_loss():
    actual = np.array([1, 0])
    probabilities = np.array([0.8, 0.3])

    report = analyze_calibration(actual, probabilities)

    expected = -(np.log(0.8) + np.log(0.7)) / 2

    assert report.log_loss == pytest.approx(expected)


def test_perfect_discrimination():
    actual = np.array([0, 0, 1, 1])
    probabilities = np.array([0.1, 0.2, 0.8, 0.9])

    report = analyze_calibration(actual, probabilities)

    assert report.roc_auc == pytest.approx(1.0)


def test_reversed_discrimination():
    actual = np.array([0, 0, 1, 1])
    probabilities = np.array([0.9, 0.8, 0.2, 0.1])

    report = analyze_calibration(actual, probabilities)

    assert report.roc_auc == pytest.approx(0.0)


def test_single_class_auc_is_undefined():
    actual = np.ones(5)
    probabilities = np.full(5, 0.7)

    report = analyze_calibration(actual, probabilities)

    assert report.roc_auc is None


def test_empty_bins_are_reported():
    actual = np.array([0, 1])
    probabilities = np.array([0.1, 0.9])

    report = analyze_calibration(actual, probabilities, n_bins=10)

    assert len(report.bins) == 10
    assert report.bins["Count"].sum() == 2
    assert (report.bins["Count"] == 0).sum() == 8

    empty = report.bins.loc[report.bins["Count"] == 0]

    assert empty["Mean Predicted"].isna().all()
    assert empty["Observed Frequency"].isna().all()


def test_probability_one_in_final_bin():
    actual = np.array([1])
    probabilities = np.array([1.0])

    report = analyze_calibration(actual, probabilities)

    assert report.bins.iloc[-1]["Count"] == 1


def test_probability_zero_in_first_bin():
    actual = np.array([0])
    probabilities = np.array([0.0])

    report = analyze_calibration(actual, probabilities)

    assert report.bins.iloc[0]["Count"] == 1


def test_bin_count_does_not_change_brier():
    actual = np.array([0, 1, 0, 1])
    probabilities = np.array([0.1, 0.6, 0.4, 0.9])

    first = analyze_calibration(actual, probabilities, n_bins=2)
    second = analyze_calibration(actual, probabilities, n_bins=20)

    assert first.brier_score == pytest.approx(second.brier_score)
    assert first.log_loss == pytest.approx(second.log_loss)


def test_inputs_are_not_modified():
    actual = np.array([0, 1, 0, 1])
    probabilities = np.array([0.1, 0.9, 0.3, 0.7])

    actual_copy = actual.copy()
    probabilities_copy = probabilities.copy()

    analyze_calibration(actual, probabilities)

    np.testing.assert_array_equal(actual, actual_copy)
    np.testing.assert_array_equal(probabilities, probabilities_copy)


def test_extreme_forecast_rate():
    actual = np.array([0, 1, 0, 1])
    probabilities = np.array([0.1, 0.9, 0.4, 0.6])

    report = analyze_calibration(
        actual,
        probabilities,
        extreme_threshold=0.8,
    )

    assert report.extreme_forecast_rate == pytest.approx(0.5)


def test_calibration_bins_are_dataframe():
    report = analyze_calibration(
        np.array([0, 1]),
        np.array([0.2, 0.8]),
    )

    assert isinstance(report.bins, pd.DataFrame)


@pytest.mark.parametrize(
    "actual, probabilities",
    [
        ([], []),
        ([0, 1], [0.5]),
        ([[0, 1]], [[0.5, 0.5]]),
        ([0, 2], [0.5, 0.5]),
        ([0, np.nan], [0.5, 0.5]),
        ([0, 1], [0.5, np.nan]),
        ([0, 1], [0.5, np.inf]),
        ([0, 1], [-0.1, 0.5]),
        ([0, 1], [0.5, 1.1]),
    ],
)
def test_invalid_inputs_rejected(actual, probabilities):
    with pytest.raises(ValueError):
        analyze_calibration(actual, probabilities)


@pytest.mark.parametrize("n_bins", [0, 1, 2.5, True])
def test_invalid_bin_counts_rejected(n_bins):
    with pytest.raises(ValueError):
        analyze_calibration(
            np.array([0, 1]),
            np.array([0.2, 0.8]),
            n_bins=n_bins,
        )


@pytest.mark.parametrize(
    "threshold",
    [0.5, 0.4, 1.1, np.nan, np.inf],
)
def test_invalid_extreme_thresholds_rejected(threshold):
    with pytest.raises(ValueError):
        analyze_calibration(
            np.array([0, 1]),
            np.array([0.2, 0.8]),
            extreme_threshold=threshold,
        )
