"""Tests for the forecasting statistical reliability report."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.reliability_report import build_reliability_report


def make_predictions(n=60, horizon=5):
    """Create aligned validation predictions with known probabilities."""
    actual = np.array([0, 1] * (n // 2) + [0] * (n % 2))

    return pd.DataFrame(
        {
            "Forecast Index": np.arange(300, 300 + n * 5, 5),
            "Horizon": horizon,
            "Research Period": ["Validation"] * n,
            "Actual Up": actual,
            "Original Probability": np.full(n, 0.5),
            "Uncertainty Probability": np.full(n, 0.5),
            "Historical Probability": np.where(
                actual == 1, 0.9, 0.1
            ),
        }
    )


def test_report_produces_two_comparisons():
    results = build_reliability_report(
        make_predictions(),
        bootstrap_samples=200,
    )

    assert len(results) == 2
    assert {r.challenger for r in results} == {
        "Original",
        "Uncertainty-aware",
    }


def test_historical_advantage_calculation():
    results = build_reliability_report(
        make_predictions(),
        bootstrap_samples=200,
    )

    for result in results:
        assert result.historical_brier == pytest.approx(0.01)
        assert result.challenger_brier == pytest.approx(0.25)
        assert result.historical_advantage == pytest.approx(0.24)


def test_clear_historical_advantage_is_supported():
    results = build_reliability_report(
        make_predictions(),
        bootstrap_samples=200,
    )

    assert all(
        r.evidence_status == "Historical advantage supported"
        for r in results
    )


def test_insufficient_data_is_reported():
    results = build_reliability_report(
        make_predictions(n=20, horizon=60),
        bootstrap_samples=200,
    )

    assert len(results) == 2

    for result in results:
        assert result.evidence_status == "Insufficient evidence"
        assert result.confidence_lower is None
        assert result.confidence_upper is None


def test_training_predictions_are_excluded():
    validation = make_predictions(n=40)
    training = make_predictions(n=40)

    training["Research Period"] = "Training"
    training["Historical Probability"] = 0.0

    combined = pd.concat(
        [validation, training],
        ignore_index=True,
    )

    expected = build_reliability_report(
        validation,
        bootstrap_samples=200,
    )

    actual = build_reliability_report(
        combined,
        bootstrap_samples=200,
    )

    assert actual == expected


def test_final_test_predictions_are_excluded():
    validation = make_predictions(n=40)
    final_test = make_predictions(n=40)

    final_test["Research Period"] = "Test"
    final_test["Historical Probability"] = 0.0

    combined = pd.concat(
        [validation, final_test],
        ignore_index=True,
    )

    expected = build_reliability_report(
        validation,
        bootstrap_samples=200,
    )

    actual = build_reliability_report(
        combined,
        bootstrap_samples=200,
    )

    assert actual == expected


def test_empty_validation_returns_no_results():
    predictions = make_predictions()
    predictions["Research Period"] = "Training"

    assert build_reliability_report(predictions) == []


def test_report_is_deterministic():
    predictions = make_predictions()

    first = build_reliability_report(
        predictions,
        bootstrap_samples=200,
        random_seed=42,
    )

    second = build_reliability_report(
        predictions,
        bootstrap_samples=200,
        random_seed=42,
    )

    assert first == second


def test_invalid_probabilities_are_rejected():
    predictions = make_predictions()
    predictions.loc[0, "Historical Probability"] = 1.5

    with pytest.raises(ValueError):
        build_reliability_report(
            predictions,
            bootstrap_samples=200,
        )


def test_invalid_outcomes_are_rejected():
    predictions = make_predictions()
    predictions.loc[0, "Actual Up"] = 2

    with pytest.raises(ValueError):
        build_reliability_report(
            predictions,
            bootstrap_samples=200,
        )


def test_missing_columns_are_rejected():
    predictions = make_predictions().drop(
        columns=["Historical Probability"]
    )

    with pytest.raises(ValueError):
        build_reliability_report(predictions)


@pytest.mark.parametrize("bad_step", [0, -1, True])
def test_invalid_step_is_rejected(bad_step):
    with pytest.raises(ValueError):
        build_reliability_report(
            make_predictions(),
            step_days=bad_step,
        )


@pytest.mark.parametrize("bad_samples", [0, 50, True])
def test_invalid_bootstrap_samples_rejected(bad_samples):
    with pytest.raises(ValueError):
        build_reliability_report(
            make_predictions(),
            bootstrap_samples=bad_samples,
        )
