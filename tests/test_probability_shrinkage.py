"""Tests for probability shrinkage."""

import numpy as np
import pytest

from app.forecasting.probability_shrinkage import shrink_probabilities


def test_reference_only():
    result = shrink_probabilities([0.9], [0.5], 0.0)
    np.testing.assert_allclose(result, [0.5])


def test_model_only():
    result = shrink_probabilities([0.9], [0.5], 1.0)
    np.testing.assert_allclose(result, [0.9])


def test_quarter_weight():
    result = shrink_probabilities([0.85], [0.55], 0.25)
    np.testing.assert_allclose(result, [0.625])


def test_multiple_probabilities():
    result = shrink_probabilities(
        [0.9, 0.1, 0.7],
        [0.5, 0.5, 0.5],
        0.25,
    )
    np.testing.assert_allclose(result, [0.6, 0.4, 0.55])


def test_equal_probabilities_unchanged():
    result = shrink_probabilities([0.6, 0.4], [0.6, 0.4], 0.3)
    np.testing.assert_allclose(result, [0.6, 0.4])


def test_extreme_inputs():
    result = shrink_probabilities([0, 1], [1, 0], 0.5)
    np.testing.assert_allclose(result, [0.5, 0.5])


def test_inputs_not_modified():
    model = np.array([0.8, 0.2])
    reference = np.array([0.6, 0.4])

    model_original = model.copy()
    reference_original = reference.copy()

    shrink_probabilities(model, reference, 0.25)

    np.testing.assert_array_equal(model, model_original)
    np.testing.assert_array_equal(reference, reference_original)


@pytest.mark.parametrize(
    "model, reference",
    [
        ([], []),
        ([0.5], [0.5, 0.5]),
        ([[0.5]], [[0.5]]),
        ([-0.1], [0.5]),
        ([1.1], [0.5]),
        ([np.nan], [0.5]),
        ([np.inf], [0.5]),
        ([0.5], [np.nan]),
        ([0.5], [np.inf]),
        ([0.5], [-0.1]),
        ([0.5], [1.1]),
    ],
)
def test_invalid_probabilities(model, reference):
    with pytest.raises(ValueError):
        shrink_probabilities(model, reference, 0.25)


@pytest.mark.parametrize(
    "weight",
    [-0.1, 1.1, np.nan, np.inf, True, None, "invalid", [0.25]],
)
def test_invalid_weights(weight):
    with pytest.raises(ValueError):
        shrink_probabilities([0.8], [0.5], weight)
