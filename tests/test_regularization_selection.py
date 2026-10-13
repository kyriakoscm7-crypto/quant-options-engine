"""Tests for chronological regularization selection."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.regularization_selection import (
    evaluate_regularization_selection,
)


@pytest.fixture
def predictions():
    indices = np.arange(100, 500, 5)
    actual = (indices % 15 == 0).astype(int)

    return pd.DataFrame(
        {
            "Forecast Index": indices,
            "Horizon": 20,
            "Research Period": np.where(
                indices < 400, "Training", "Validation"
            ),
            "Actual Up": actual,
            "ML C=0.001": np.where(actual == 1, 0.7, 0.3),
            "ML C=0.01": np.full(len(indices), 0.5),
            "ML C=0.1": np.where(actual == 1, 0.3, 0.7),
            "ML C=1": np.full(len(indices), 0.6),
        }
    )


def evaluate(predictions, **kwargs):
    options = {
        "predictions": predictions,
        "candidate_columns": (
            "ML C=0.001",
            "ML C=0.01",
            "ML C=0.1",
            "ML C=1",
        ),
        "minimum_observations": 30,
        "embargo_days": 5,
    }
    options.update(kwargs)
    return evaluate_regularization_selection(**options)


def test_correct_candidate_selected(predictions):
    results, _ = evaluate(predictions)
    assert results["Selected Candidate"].eq("ML C=0.001").all()


def test_selection_respects_maturity(predictions):
    results, _ = evaluate(predictions)
    assert (
        results["Latest Selection Index"]
        + results["Horizon"]
        + 5
        < results["Forecast Index"]
    ).all()


def test_validation_outcomes_cannot_change_selection(predictions):
    original, _ = evaluate(predictions)

    modified = predictions.copy()
    validation = modified["Research Period"].eq("Validation")
    modified.loc[validation, "Actual Up"] = (
        1 - modified.loc[validation, "Actual Up"]
    )

    changed, _ = evaluate(modified)

    assert (
        original["Selected Candidate"].tolist()
        == changed["Selected Candidate"].tolist()
    )


def test_training_outcomes_can_change_selection(predictions):
    original, _ = evaluate(predictions)

    modified = predictions.copy()
    training = modified["Research Period"].eq("Training")
    modified.loc[training, "Actual Up"] = (
        1 - modified.loc[training, "Actual Up"]
    )

    changed, _ = evaluate(modified)

    assert (
        original["Selected Candidate"].tolist()
        != changed["Selected Candidate"].tolist()
    )


def test_baseline_and_selected_use_identical_dates(predictions):
    results, summary = evaluate(predictions)

    assert results["Selected Probability"].notna().all()
    assert results["Baseline Probability"].notna().all()

    counts = summary["N"].unique()
    assert len(counts) == 1
    assert counts[0] == len(results)


def test_neutral_brier_is_quarter(predictions):
    _, summary = evaluate(predictions)

    neutral = summary.loc[summary["Model"].eq("Neutral")]

    assert neutral.iloc[0]["Brier"] == pytest.approx(0.25)


def test_fixed_baseline_probabilities_preserved(predictions):
    results, _ = evaluate(predictions)

    expected = predictions.loc[
        predictions["Research Period"].eq("Validation"),
        "ML C=0.1",
    ].to_numpy()

    np.testing.assert_allclose(
        results["Baseline Probability"].to_numpy(),
        expected,
    )


def test_reserved_test_data_rejected(predictions):
    modified = predictions.copy()
    modified.loc[0, "Research Period"] = "Test"

    with pytest.raises(ValueError, match="Reserved test"):
        evaluate(modified)


def test_unknown_period_rejected(predictions):
    modified = predictions.copy()
    modified.loc[0, "Research Period"] = "Unknown"

    with pytest.raises(ValueError, match="Unknown research period"):
        evaluate(modified)


def test_duplicate_forecast_keys_rejected(predictions):
    modified = pd.concat(
        [predictions, predictions.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate"):
        evaluate(modified)


def test_missing_candidate_rejected(predictions):
    with pytest.raises(ValueError, match="Missing columns"):
        evaluate(
            predictions,
            candidate_columns=("ML C=0.1", "Missing Candidate"),
        )


def test_baseline_must_be_candidate(predictions):
    with pytest.raises(ValueError, match="Baseline"):
        evaluate(
            predictions,
            candidate_columns=("ML C=0.001",),
        )


def test_no_validation_data_rejected(predictions):
    modified = predictions.copy()
    modified["Research Period"] = "Training"

    with pytest.raises(ValueError, match="No validation"):
        evaluate(modified)


def test_insufficient_training_history_rejected(predictions):
    with pytest.raises(ValueError, match="No eligible"):
        evaluate(
            predictions,
            minimum_observations=1000,
        )


def test_inputs_are_not_modified(predictions):
    original = predictions.copy(deep=True)

    evaluate(predictions)

    pd.testing.assert_frame_equal(predictions, original)


def test_summary_has_three_models(predictions):
    _, summary = evaluate(predictions)

    assert set(summary["Model"]) == {
        "Chronological Selection",
        "Fixed C=0.1",
        "Neutral",
    }


def test_summary_scores_are_finite(predictions):
    _, summary = evaluate(predictions)

    assert np.isfinite(
        summary[["Brier", "Log Loss"]].to_numpy()
    ).all()


def test_selected_probability_matches_candidate(predictions):
    results, _ = evaluate(predictions)

    for _, row in results.iterrows():
        source = predictions.loc[
            predictions["Forecast Index"].eq(row["Forecast Index"])
            & predictions["Horizon"].eq(row["Horizon"])
        ].iloc[0]

        assert row["Selected Probability"] == pytest.approx(
            source[row["Selected Candidate"]]
        )


def test_selection_does_not_use_future_training_outcomes(predictions):
    original, _ = evaluate(predictions)

    modified = predictions.copy()

    future_training = (
        modified["Research Period"].eq("Training")
        & (modified["Forecast Index"] >= 380)
    )

    modified.loc[future_training, "Actual Up"] = (
        1 - modified.loc[future_training, "Actual Up"]
    )

    changed, _ = evaluate(modified)

    first_original = original.loc[
        original["Forecast Index"].eq(400),
        "Selected Candidate",
    ].iloc[0]

    first_changed = changed.loc[
        changed["Forecast Index"].eq(400),
        "Selected Candidate",
    ].iloc[0]

    assert first_original == first_changed


def test_validation_results_are_chronologically_sorted(predictions):
    results, _ = evaluate(predictions)

    assert results["Forecast Index"].is_monotonic_increasing
