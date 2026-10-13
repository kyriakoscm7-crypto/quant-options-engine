"""Tests for leakage-safe chronological probability model selection."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.chronological_selection import (
    select_probability_candidate,
)


@pytest.fixture
def predictions():
    indices = np.arange(100, 500, 5)
    actual = (indices % 15 == 0).astype(int)

    return pd.DataFrame(
        {
            "Forecast Index": indices,
            "Horizon": 20,
            "Actual Up": actual,
            "Neutral": np.full(len(indices), 0.5),
            "Candidate A": np.where(actual == 1, 0.7, 0.3),
            "Candidate B": np.where(actual == 1, 0.3, 0.7),
        }
    )


def select(predictions, **kwargs):
    options = {
        "predictions": predictions,
        "evaluation_index": 450,
        "horizon_days": 20,
        "candidate_columns": (
            "Neutral",
            "Candidate A",
            "Candidate B",
        ),
        "minimum_observations": 30,
        "embargo_days": 5,
    }

    options.update(kwargs)

    return select_probability_candidate(**options)


def test_correct_candidate_selected(predictions):
    result = select(predictions)

    assert result.selected_candidate == "Candidate A"
    assert result.selected_brier == pytest.approx(0.09)


def test_strict_maturity_and_embargo(predictions):
    result = select(predictions)

    assert (
        result.latest_training_index
        + result.horizon_days
        + 5
        < result.evaluation_index
    )

    assert result.latest_training_index == 420


def test_expected_training_observation_count(predictions):
    result = select(predictions)

    assert result.observations == 65


def test_future_outcomes_cannot_change_selection(predictions):
    original = select(predictions)

    modified = predictions.copy()

    future = (
        modified["Forecast Index"] + 20 + 5 >= 450
    )

    modified.loc[future, "Actual Up"] = (
        1 - modified.loc[future, "Actual Up"]
    )

    modified.loc[future, "Candidate A"] = 0.0
    modified.loc[future, "Candidate B"] = 1.0

    changed = select(modified)

    assert changed.selected_candidate == original.selected_candidate

    pd.testing.assert_frame_equal(
        changed.candidate_scores,
        original.candidate_scores,
    )


def test_exact_boundary_is_excluded():
    predictions = pd.DataFrame(
        {
            "Forecast Index": [70, 75, 80],
            "Horizon": [10, 10, 10],
            "Actual Up": [1, 0, 1],
            "Candidate": [0.8, 0.2, 0.8],
        }
    )

    result = select_probability_candidate(
        predictions,
        evaluation_index=100,
        horizon_days=10,
        candidate_columns=("Candidate",),
        minimum_observations=1,
        embargo_days=10,
    )

    assert result.observations == 2
    assert result.latest_training_index == 75


def test_horizons_are_separated(predictions):
    modified = predictions.copy()

    extra = modified.copy()
    extra["Horizon"] = 5
    extra["Candidate A"] = 0.0

    combined = pd.concat(
        [modified, extra],
        ignore_index=True,
    )

    original = select(modified)
    changed = select(combined)

    assert changed.selected_candidate == original.selected_candidate
    assert changed.observations == original.observations


def test_candidate_order_does_not_change_winner(predictions):
    first = select(predictions)

    second = select(
        predictions,
        candidate_columns=(
            "Candidate B",
            "Neutral",
            "Candidate A",
        ),
    )

    assert first.selected_candidate == second.selected_candidate

    pd.testing.assert_frame_equal(
        first.candidate_scores,
        second.candidate_scores,
    )


def test_ties_resolved_alphabetically(predictions):
    modified = predictions.copy()
    modified["Candidate B"] = modified["Candidate A"]

    result = select(
        modified,
        candidate_columns=("Candidate B", "Candidate A"),
    )

    assert result.selected_candidate == "Candidate A"


def test_all_candidates_have_identical_sample_counts(predictions):
    result = select(predictions)

    assert result.candidate_scores["N"].nunique() == 1
    assert (result.candidate_scores["N"] == 65).all()


def test_inputs_not_modified(predictions):
    original = predictions.copy(deep=True)

    select(predictions)

    pd.testing.assert_frame_equal(predictions, original)


def test_insufficient_history_rejected(predictions):
    with pytest.raises(ValueError, match="Insufficient"):
        select(
            predictions,
            minimum_observations=100,
        )


def test_missing_candidate_column_rejected(predictions):
    with pytest.raises(ValueError, match="Missing columns"):
        select(
            predictions,
            candidate_columns=("Nonexistent",),
        )


def test_duplicate_candidates_rejected(predictions):
    with pytest.raises(ValueError, match="unique"):
        select(
            predictions,
            candidate_columns=("Neutral", "Neutral"),
        )


def test_no_candidates_rejected(predictions):
    with pytest.raises(ValueError, match="At least one"):
        select(
            predictions,
            candidate_columns=(),
        )


def test_duplicate_forecast_indices_rejected(predictions):
    modified = pd.concat(
        [predictions, predictions.iloc[[0]]],
        ignore_index=True,
    )

    with pytest.raises(ValueError, match="Duplicate"):
        select(modified)


@pytest.mark.parametrize(
    "column, value",
    [
        ("Actual Up", 2),
        ("Actual Up", np.nan),
        ("Candidate A", -0.1),
        ("Candidate A", 1.1),
        ("Candidate A", np.nan),
        ("Candidate A", np.inf),
    ],
)
def test_invalid_training_values_rejected(
    predictions,
    column,
    value,
):
    modified = predictions.copy()
    modified.loc[0, column] = value

    with pytest.raises(ValueError):
        select(modified)


@pytest.mark.parametrize(
    "parameter, value",
    [
        ("evaluation_index", -1),
        ("evaluation_index", 450.5),
        ("evaluation_index", True),
        ("horizon_days", 0),
        ("horizon_days", 5.5),
        ("minimum_observations", 0),
        ("minimum_observations", True),
        ("embargo_days", -1),
        ("embargo_days", 2.5),
    ],
)
def test_invalid_parameters_rejected(
    predictions,
    parameter,
    value,
):
    with pytest.raises(ValueError):
        select(predictions, **{parameter: value})


def test_later_evaluation_allows_more_history(predictions):
    earlier = select(predictions, evaluation_index=350)
    later = select(predictions, evaluation_index=450)

    assert later.observations > earlier.observations


def test_candidate_scores_sorted_by_brier(predictions):
    result = select(predictions)

    scores = result.candidate_scores["Brier"].to_numpy()

    assert np.all(np.diff(scores) >= 0)


def test_different_embargo_changes_eligible_history(predictions):
    short = select(predictions, embargo_days=0)
    long = select(predictions, embargo_days=30)

    assert short.observations > long.observations


def test_no_future_forecast_can_enter_training(predictions):
    result = select(predictions, evaluation_index=450)

    assert result.latest_training_index < 450


def test_result_contains_correct_horizon(predictions):
    result = select(predictions)

    assert result.horizon_days == 20
    assert result.evaluation_index == 450
