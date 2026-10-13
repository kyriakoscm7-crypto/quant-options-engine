"""Tests for chronological research splits and label maturity."""

import pandas as pd
import pytest

from app.forecasting.research_splits import (
    assign_research_periods,
    create_research_split,
)


def test_default_split_boundaries():
    split = create_research_split(1000)

    assert split.training_end == 600
    assert split.validation_start == 660
    assert split.validation_end == 800
    assert split.test_start == 860
    assert split.total_observations == 1000
    assert split.embargo_days == 60


def test_training_forecast_must_mature_before_training_ends():
    split = create_research_split(1000)

    predictions = pd.DataFrame(
        {
            "Forecast Index": [500, 550, 599],
            "Horizon": [60, 60, 1],
        }
    )

    result = assign_research_periods(predictions, split)

    assert result["Research Period"].tolist() == [
        "Training",
        "Excluded",
        "Excluded",
    ]


def test_validation_forecast_must_mature_within_validation():
    split = create_research_split(1000)

    predictions = pd.DataFrame(
        {
            "Forecast Index": [660, 700, 750, 799],
            "Horizon": [5, 20, 60, 1],
        }
    )

    result = assign_research_periods(predictions, split)

    assert result["Research Period"].tolist() == [
        "Validation",
        "Validation",
        "Excluded",
        "Excluded",
    ]


def test_test_forecast_must_mature_within_test():
    split = create_research_split(1000)

    predictions = pd.DataFrame(
        {
            "Forecast Index": [860, 900, 950, 999],
            "Horizon": [60, 20, 60, 1],
        }
    )

    result = assign_research_periods(predictions, split)

    assert result["Research Period"].tolist() == [
        "Test",
        "Test",
        "Excluded",
        "Excluded",
    ]


def test_embargo_periods_are_excluded():
    split = create_research_split(1000)

    predictions = pd.DataFrame(
        {
            "Forecast Index": [600, 630, 800, 830],
            "Horizon": [1, 1, 1, 1],
        }
    )

    result = assign_research_periods(predictions, split)

    assert (result["Research Period"] == "Excluded").all()


def test_missing_columns_are_rejected():
    split = create_research_split(1000)

    predictions = pd.DataFrame({"Forecast Index": [100]})

    with pytest.raises(ValueError):
        assign_research_periods(predictions, split)


@pytest.mark.parametrize(
    "observations",
    [0, 100, 299, True],
)
def test_invalid_observation_counts_are_rejected(observations):
    with pytest.raises(ValueError):
        create_research_split(observations)


@pytest.mark.parametrize(
    "training_fraction, validation_fraction",
    [
        (0.0, 0.2),
        (1.0, 0.2),
        (0.6, 0.0),
        (0.6, 1.0),
        (0.8, 0.3),
    ],
)
def test_invalid_fractions_are_rejected(
    training_fraction,
    validation_fraction,
):
    with pytest.raises(ValueError):
        create_research_split(
            1000,
            training_fraction=training_fraction,
            validation_fraction=validation_fraction,
        )


@pytest.mark.parametrize("embargo", [-1, True, 1000])
def test_invalid_embargo_is_rejected(embargo):
    with pytest.raises(ValueError):
        create_research_split(1000, embargo_days=embargo)


def test_original_dataframe_is_not_modified():
    split = create_research_split(1000)

    predictions = pd.DataFrame(
        {
            "Forecast Index": [700],
            "Horizon": [5],
        }
    )

    original = predictions.copy()

    assign_research_periods(predictions, split)

    pd.testing.assert_frame_equal(predictions, original)
