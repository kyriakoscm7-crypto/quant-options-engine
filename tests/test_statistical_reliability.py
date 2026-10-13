"""Tests for statistical reliability of probability forecasts."""

import numpy as np
import pytest

from app.forecasting.statistical_reliability import (
    block_bootstrap_brier_improvement,
)


def test_perfect_model_beats_benchmark():
    actual = np.tile([0, 1], 100)
    model = actual.astype(float)
    benchmark = np.full(200, 0.5)

    result = block_bootstrap_brier_improvement(
        model,
        benchmark,
        actual,
        horizon_days=5,
    )

    assert result.brier_improvement == pytest.approx(0.25)
    assert result.confidence_lower == pytest.approx(0.25)
    assert result.confidence_upper == pytest.approx(0.25)
    assert result.statistically_distinguishable_from_zero


def test_perfect_benchmark_beats_model():
    actual = np.tile([0, 1], 100)
    model = np.full(200, 0.5)
    benchmark = actual.astype(float)

    result = block_bootstrap_brier_improvement(
        model,
        benchmark,
        actual,
        horizon_days=5,
    )

    assert result.brier_improvement == pytest.approx(-0.25)
    assert result.confidence_upper < 0
    assert result.statistically_distinguishable_from_zero


def test_identical_models_have_zero_improvement():
    actual = np.tile([0, 1], 100)
    probabilities = np.full(200, 0.6)

    result = block_bootstrap_brier_improvement(
        probabilities,
        probabilities,
        actual,
        horizon_days=20,
    )

    assert result.brier_improvement == pytest.approx(0.0)
    assert result.confidence_lower == pytest.approx(0.0)
    assert result.confidence_upper == pytest.approx(0.0)
    assert not result.statistically_distinguishable_from_zero


@pytest.mark.parametrize(
    ("horizon", "expected_block_length"),
    [
        (1, 1),
        (5, 1),
        (20, 4),
        (60, 12),
    ],
)
def test_block_length_matches_horizon(horizon, expected_block_length):
    actual = np.tile([0, 1], 100)
    model = np.full(200, 0.6)
    benchmark = np.full(200, 0.5)

    result = block_bootstrap_brier_improvement(
        model,
        benchmark,
        actual,
        horizon_days=horizon,
        step_days=5,
        bootstrap_samples=100,
    )

    assert result.block_length == expected_block_length


def test_bootstrap_is_reproducible():
    rng = np.random.default_rng(123)
    actual = rng.integers(0, 2, size=200)
    model = rng.uniform(0.3, 0.7, size=200)
    benchmark = np.full(200, 0.5)

    first = block_bootstrap_brier_improvement(
        model,
        benchmark,
        actual,
        horizon_days=20,
        random_seed=42,
    )

    second = block_bootstrap_brier_improvement(
        model,
        benchmark,
        actual,
        horizon_days=20,
        random_seed=42,
    )

    assert first == second


def test_too_few_observations_are_rejected():
    with pytest.raises(ValueError):
        block_bootstrap_brier_improvement(
            [0.5] * 20,
            [0.5] * 20,
            [0] * 20,
            horizon_days=5,
        )


def test_invalid_probabilities_are_rejected():
    with pytest.raises(ValueError):
        block_bootstrap_brier_improvement(
            [1.5] * 100,
            [0.5] * 100,
            [1] * 100,
            horizon_days=5,
        )


def test_invalid_outcomes_are_rejected():
    with pytest.raises(ValueError):
        block_bootstrap_brier_improvement(
            [0.5] * 100,
            [0.5] * 100,
            [2] * 100,
            horizon_days=5,
        )


def test_insufficient_blocks_are_rejected():
    with pytest.raises(ValueError):
        block_bootstrap_brier_improvement(
            [0.5] * 30,
            [0.5] * 30,
            [0] * 30,
            horizon_days=60,
            step_days=5,
        )
