"""Tests for chronological forecasting research evaluation."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.research_evaluation import evaluate_research_periods
from app.forecasting.research_splits import (
    assign_research_periods,
    create_research_split,
)
from app.forecasting.walk_forward import walk_forward_predictions


def make_prices(n=1200, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0003, 0.012, n - 1)
    prices = 100.0 * np.exp(np.r_[0.0, np.cumsum(returns)])
    return pd.Series(prices)


def test_final_test_hidden_by_default():
    _, results = evaluate_research_periods(
        make_prices(),
        horizons=(1, 5, 20, 60),
    )

    periods = {result.period for result in results}

    assert "Training" in periods
    assert "Validation" in periods
    assert "Test" not in periods


def test_final_test_requires_explicit_opt_in():
    _, results = evaluate_research_periods(
        make_prices(),
        horizons=(5,),
        include_final_test=True,
    )

    periods = {result.period for result in results}

    assert "Test" in periods


def test_research_split_matches_price_history():
    prices = make_prices()

    split, _ = evaluate_research_periods(
        prices,
        horizons=(5,),
    )

    assert split.total_observations == len(prices)
    assert split.embargo_days == 5


def test_every_reported_horizon_is_requested():
    _, results = evaluate_research_periods(
        make_prices(),
        horizons=(1, 20),
    )

    assert {result.horizon_days for result in results} == {1, 20}


def test_reported_metrics_are_valid():
    _, results = evaluate_research_periods(
        make_prices(),
        horizons=(5,),
    )

    assert len(results) > 0

    for result in results:
        assert result.predictions > 0
        assert 0 <= result.brier_score <= 1
        assert 0 <= result.directional_accuracy <= 1
        assert 0 <= result.average_probability <= 1
        assert 0 <= result.observed_up_frequency <= 1


def test_report_matches_independent_manual_calculation():
    prices = make_prices()

    split, results = evaluate_research_periods(
        prices,
        horizons=(5,),
        training_days=252,
        step=5,
    )

    predictions = walk_forward_predictions(
        prices,
        horizons=(5,),
        training_days=252,
        step=5,
    )

    assigned = assign_research_periods(predictions, split)

    validation = assigned[
        assigned["Research Period"] == "Validation"
    ]

    expected_brier = np.mean(
        (
            validation["Probability Up"].to_numpy()
            - validation["Actual Up"].to_numpy()
        ) ** 2
    )

    reported = next(
        result for result in results
        if result.period == "Validation"
        and result.horizon_days == 5
    )

    assert reported.predictions == len(validation)
    assert reported.brier_score == pytest.approx(expected_brier)


def test_predictions_crossing_boundaries_are_excluded():
    split = create_research_split(1000, embargo_days=60)

    predictions = pd.DataFrame(
        {
            "Forecast Index": [550, 700, 750, 900],
            "Horizon": [60, 20, 60, 20],
        }
    )

    assigned = assign_research_periods(predictions, split)

    assert assigned["Research Period"].tolist() == [
        "Excluded",
        "Validation",
        "Excluded",
        "Test",
    ]


def test_invalid_final_test_flag_is_rejected():
    with pytest.raises(ValueError):
        evaluate_research_periods(
            make_prices(),
            include_final_test="yes",
        )


def test_invalid_price_history_is_rejected():
    prices = make_prices()
    prices.iloc[100] = np.nan

    with pytest.raises(ValueError):
        evaluate_research_periods(prices)


def test_evaluation_is_deterministic():
    prices = make_prices()

    first = evaluate_research_periods(
        prices,
        horizons=(5,),
    )

    second = evaluate_research_periods(
        prices,
        horizons=(5,),
    )

    assert first == second


def test_final_test_prices_never_reach_forecasting_engine(monkeypatch):
    """Development forecasts must not receive reserved test prices."""
    from unittest.mock import Mock

    import app.forecasting.research_evaluation as research_module

    prices = make_prices(1200)
    expected_split = create_research_split(
        len(prices),
        embargo_days=60,
    )

    original_forecaster = research_module.walk_forward_predictions
    spy = Mock(wraps=original_forecaster)

    monkeypatch.setattr(
        research_module,
        "walk_forward_predictions",
        spy,
    )

    evaluate_research_periods(
        prices,
        horizons=(1, 5, 20, 60),
        include_final_test=False,
    )

    assert spy.call_count == 1

    received_prices = spy.call_args.args[0]

    assert len(received_prices) == expected_split.validation_end

    pd.testing.assert_series_equal(
        received_prices,
        prices.iloc[: expected_split.validation_end],
    )


def test_changing_final_test_prices_cannot_change_validation_results():
    """Reserved test prices must not influence development metrics."""
    original_prices = make_prices(1200)

    modified_prices = original_prices.copy()

    split = create_research_split(
        len(original_prices),
        embargo_days=60,
    )

    modified_prices.iloc[split.test_start :] *= 10

    original_split, original_results = evaluate_research_periods(
        original_prices,
        horizons=(1, 5, 20, 60),
        include_final_test=False,
    )

    modified_split, modified_results = evaluate_research_periods(
        modified_prices,
        horizons=(1, 5, 20, 60),
        include_final_test=False,
    )

    assert original_split == modified_split
    assert original_results == modified_results
