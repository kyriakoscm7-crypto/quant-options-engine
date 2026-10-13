"""Regression tests for multi-stock statistical reliability analysis."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.research_reliability import (
    analyze_research_reliability,
)


def make_predictions(n=100, horizon=5):
    """Create deterministic validation predictions."""

    actual = np.tile([0, 1], n // 2 + 1)[:n]

    return pd.DataFrame(
        {
            "Stock": ["TEST"] * n,
            "Forecast Index": np.arange(300, 300 + n * 5, 5),
            "Horizon": [horizon] * n,
            "Research Period": ["Validation"] * n,
            "Actual Up": actual,
            "Historical Probability": np.full(n, 0.5),
            "ML Probability": actual.astype(float),
            "Ensemble Probability": np.where(
                actual == 1, 0.75, 0.25
            ),
        }
    )


def test_two_model_comparisons_generated():
    result = analyze_research_reliability(
        make_predictions(),
        bootstrap_samples=200,
    )

    assert len(result) == 2
    assert set(result["Model"]) == {"ML", "Ensemble"}


def test_ml_improvement_is_correct():
    result = analyze_research_reliability(
        make_predictions(),
        bootstrap_samples=200,
    )

    ml = result.loc[result["Model"] == "ML"].iloc[0]

    assert ml["Brier Improvement"] == pytest.approx(0.25)
    assert ml["Evidence"] == "Model advantage"


def test_ensemble_improvement_is_correct():
    result = analyze_research_reliability(
        make_predictions(),
        bootstrap_samples=200,
    )

    ensemble = result.loc[
        result["Model"] == "Ensemble"
    ].iloc[0]

    assert ensemble["Brier Improvement"] == pytest.approx(
        0.1875
    )


def test_training_observations_are_excluded():
    validation = make_predictions()
    training = make_predictions()

    training["Research Period"] = "Training"
    training["ML Probability"] = 0.5

    combined = pd.concat(
        [validation, training],
        ignore_index=True,
    )

    expected = analyze_research_reliability(
        validation,
        bootstrap_samples=200,
    )

    actual = analyze_research_reliability(
        combined,
        bootstrap_samples=200,
    )

    pd.testing.assert_frame_equal(actual, expected)


def test_reserved_test_observations_are_rejected():
    predictions = make_predictions()
    predictions.loc[0, "Research Period"] = "Test"

    with pytest.raises(ValueError, match="Reserved test"):
        analyze_research_reliability(
            predictions,
            bootstrap_samples=200,
        )


def test_insufficient_evidence_is_reported():
    result = analyze_research_reliability(
        make_predictions(n=20, horizon=60),
        bootstrap_samples=200,
    )

    assert len(result) == 2
    assert (
        result["Evidence"] == "Insufficient evidence"
    ).all()

    assert result["CI Lower"].isna().all()
    assert result["CI Upper"].isna().all()


def test_reliability_analysis_is_reproducible():
    predictions = make_predictions()

    first = analyze_research_reliability(
        predictions,
        bootstrap_samples=200,
        random_seed=42,
    )

    second = analyze_research_reliability(
        predictions,
        bootstrap_samples=200,
        random_seed=42,
    )

    pd.testing.assert_frame_equal(first, second)


def test_invalid_probabilities_are_rejected():
    predictions = make_predictions()
    predictions.loc[0, "ML Probability"] = 1.5

    with pytest.raises(ValueError):
        analyze_research_reliability(
            predictions,
            bootstrap_samples=200,
        )


def test_missing_columns_are_rejected():
    predictions = make_predictions().drop(
        columns=["Historical Probability"]
    )

    with pytest.raises(ValueError, match="Missing columns"):
        analyze_research_reliability(predictions)


def test_multiple_stocks_and_horizons():
    first = make_predictions(n=100, horizon=5)

    second = make_predictions(n=100, horizon=20)
    second["Stock"] = "OTHER"

    combined = pd.concat(
        [first, second],
        ignore_index=True,
    )

    result = analyze_research_reliability(
        combined,
        bootstrap_samples=200,
    )

    assert len(result) == 4
    assert set(result["Stock"]) == {"TEST", "OTHER"}
    assert set(result["Horizon"]) == {5, 20}
