"""Tests for chronological three-model forecasting comparisons."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.three_model_comparison import compare_three_models


def make_prices(n=1200, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.015, n - 1)
    prices = 100 * np.exp(np.r_[0.0, np.cumsum(returns)])
    return pd.Series(prices)


def test_comparison_produces_results():
    results = compare_three_models(
        make_prices(),
        horizons=(1, 5, 20, 60),
    )

    assert results
    assert {r.horizon_days for r in results} == {1, 5, 20, 60}


def test_training_and_validation_are_separated():
    results = compare_three_models(
        make_prices(),
        horizons=(5,),
    )

    periods = {r.period for r in results}

    assert periods == {"Training", "Validation"}


def test_final_test_results_are_never_reported():
    results = compare_three_models(make_prices())

    assert all(r.period != "Test" for r in results)


def test_all_brier_scores_are_valid():
    results = compare_three_models(make_prices())

    for result in results:
        assert result.predictions > 0
        assert 0 <= result.original_brier <= 1
        assert 0 <= result.uncertainty_aware_brier <= 1
        assert 0 <= result.historical_brier <= 1


def test_improvement_calculations_are_correct():
    results = compare_three_models(
        make_prices(),
        horizons=(5,),
    )

    for result in results:
        assert result.improvement_vs_original == pytest.approx(
            result.original_brier - result.uncertainty_aware_brier
        )

        assert result.improvement_vs_historical == pytest.approx(
            result.historical_brier - result.uncertainty_aware_brier
        )


def test_final_test_price_changes_do_not_affect_results():
    prices = make_prices()

    original_results = compare_three_models(
        prices,
        horizons=(5, 20),
    )

    modified = prices.copy()

    modified.iloc[1000:] *= 10

    modified_results = compare_three_models(
        modified,
        horizons=(5, 20),
    )

    assert original_results == modified_results


def test_comparison_is_deterministic():
    prices = make_prices()

    first = compare_three_models(
        prices,
        horizons=(5,),
    )

    second = compare_three_models(
        prices,
        horizons=(5,),
    )

    assert first == second


@pytest.mark.parametrize("bad_horizon", [0, -1, 1.5, True])
def test_invalid_horizons_are_rejected(bad_horizon):
    with pytest.raises(ValueError):
        compare_three_models(
            make_prices(),
            horizons=(bad_horizon,),
        )


@pytest.mark.parametrize("bad_step", [0, -1, True])
def test_invalid_step_is_rejected(bad_step):
    with pytest.raises(ValueError):
        compare_three_models(
            make_prices(),
            horizons=(5,),
            step=bad_step,
        )


@pytest.mark.parametrize("bad_value", [0.0, -5.0, np.nan, np.inf])
def test_invalid_prices_are_rejected(bad_value):
    prices = make_prices()
    prices.iloc[100] = bad_value

    with pytest.raises(ValueError):
        compare_three_models(prices)


def test_insufficient_history_is_rejected():
    with pytest.raises(ValueError):
        compare_three_models(make_prices(100))
