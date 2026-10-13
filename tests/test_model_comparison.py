"""Tests for forecasting-model comparisons."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.model_comparison import compare_model_to_benchmark


def make_prices(seed=42, n=500):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0003, 0.015, n - 1)

    return pd.Series(
        100.0 * np.exp(
            np.r_[0.0, np.cumsum(returns)]
        )
    )


def test_comparison_supports_all_horizons():
    results = compare_model_to_benchmark(make_prices())

    assert [result.horizon_days for result in results] == [
        1, 5, 20, 60
    ]

    assert all(result.predictions > 0 for result in results)


def test_brier_scores_are_valid():
    results = compare_model_to_benchmark(
        make_prices(),
        horizons=(5,),
    )

    result = results[0]

    assert 0 <= result.model_brier_score <= 1
    assert 0 <= result.benchmark_brier_score <= 1

    assert result.brier_improvement == pytest.approx(
        result.benchmark_brier_score - result.model_brier_score
    )


def test_directional_accuracies_are_valid():
    results = compare_model_to_benchmark(
        make_prices(),
        horizons=(5,),
    )

    result = results[0]

    assert 0 <= result.model_directional_accuracy <= 1
    assert 0 <= result.benchmark_directional_accuracy <= 1


def test_comparison_is_deterministic():
    prices = make_prices()

    first = compare_model_to_benchmark(
        prices,
        horizons=(5,),
    )

    second = compare_model_to_benchmark(
        prices,
        horizons=(5,),
    )

    assert first == second


def test_invalid_prices_are_rejected():
    prices = make_prices()
    prices.iloc[100] = np.nan

    with pytest.raises(ValueError):
        compare_model_to_benchmark(prices)
