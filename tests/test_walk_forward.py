"""Tests for leakage-aware walk-forward forecasting."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.walk_forward import (
    evaluate_predictions,
    walk_forward_predictions,
)


def make_prices(n=400):
    rng = np.random.default_rng(42)
    returns = rng.normal(0.0004, 0.015, n - 1)
    return pd.Series(100.0 * np.exp(np.r_[0.0, np.cumsum(returns)]))


def test_backtest_generates_all_requested_horizons():
    predictions = walk_forward_predictions(
        make_prices(),
        horizons=(1, 5, 20, 60),
    )

    assert set(predictions["Horizon"]) == {1, 5, 20, 60}
    assert len(predictions) > 0
    assert predictions["Probability Up"].between(0, 1).all()


def test_predictions_do_not_use_future_prices():
    prices = make_prices()

    original = walk_forward_predictions(
        prices,
        horizons=(5,),
        step=10,
    )

    modified = prices.copy()

    modified.iloc[350:] *= 1.5

    changed = walk_forward_predictions(
        modified,
        horizons=(5,),
        step=10,
    )

    early_original = original[
        original["Forecast Index"] < 340
    ]

    early_changed = changed[
        changed["Forecast Index"] < 340
    ]

    pd.testing.assert_series_equal(
        early_original["Probability Up"].reset_index(drop=True),
        early_changed["Probability Up"].reset_index(drop=True),
    )


def test_actual_outcome_uses_correct_future_horizon():
    prices = pd.Series(np.linspace(100, 200, 400))

    predictions = walk_forward_predictions(
        prices,
        horizons=(5,),
        step=20,
    )

    assert (predictions["Actual Up"] == 1).all()
    assert (predictions["Realized Return (%)"] > 0).all()


def test_metrics_calculate_correct_brier_score():
    predictions = pd.DataFrame(
        {
            "Horizon": [5, 5, 5, 5],
            "Probability Up": [0.9, 0.8, 0.2, 0.1],
            "Actual Up": [1, 1, 0, 0],
        }
    )

    metrics = evaluate_predictions(predictions)[0]

    assert metrics.predictions == 4
    assert metrics.directional_accuracy == pytest.approx(1.0)
    assert metrics.brier_score == pytest.approx(0.025)
    assert metrics.baseline_brier_score == pytest.approx(0.25)
    assert metrics.actual_up_frequency == pytest.approx(0.5)


def test_invalid_prices_are_rejected():
    prices = make_prices()
    prices.iloc[100] = np.nan

    with pytest.raises(ValueError):
        walk_forward_predictions(prices)


def test_insufficient_history_is_rejected():
    with pytest.raises(ValueError):
        walk_forward_predictions(
            make_prices(100),
            horizons=(60,),
        )


def test_invalid_step_is_rejected():
    with pytest.raises(ValueError):
        walk_forward_predictions(
            make_prices(),
            step=0,
        )


def test_invalid_horizon_is_rejected():
    with pytest.raises(ValueError):
        walk_forward_predictions(
            make_prices(),
            horizons=(-5,),
        )


def test_invalid_probabilities_are_rejected():
    predictions = pd.DataFrame(
        {
            "Horizon": [5, 5],
            "Probability Up": [0.7, 1.5],
            "Actual Up": [1, 0],
        }
    )

    with pytest.raises(ValueError):
        evaluate_predictions(predictions)


def test_each_horizon_uses_all_available_future_outcomes():
    """Short horizons must continue after long horizons become unavailable."""
    import numpy as np
    import pandas as pd

    from app.forecasting.walk_forward import walk_forward_predictions

    rng = np.random.default_rng(42)
    returns = rng.normal(0.0004, 0.01, 399)
    prices = pd.Series(100 * np.exp(np.r_[0, np.cumsum(returns)]))

    predictions = walk_forward_predictions(
        prices,
        horizons=(1, 5, 20, 60),
        training_days=252,
        step=1,
    )

    expected_last_index = {
        1: 398,
        5: 394,
        20: 379,
        60: 339,
    }

    for horizon, last_index in expected_last_index.items():
        subset = predictions[predictions["Horizon"] == horizon]

        assert not subset.empty
        assert subset["Forecast Index"].max() == last_index
        assert (
            subset["Forecast Index"] + subset["Horizon"] < len(prices)
        ).all()


def test_short_horizon_matches_single_horizon_backtest():
    """Adding longer horizons must not change existing 1-day forecasts."""
    import numpy as np
    import pandas as pd

    from app.forecasting.walk_forward import walk_forward_predictions

    rng = np.random.default_rng(123)
    returns = rng.normal(0.0003, 0.012, 399)
    prices = pd.Series(100 * np.exp(np.r_[0, np.cumsum(returns)]))

    single = walk_forward_predictions(
        prices,
        horizons=(1,),
        training_days=252,
        step=5,
    )

    combined = walk_forward_predictions(
        prices,
        horizons=(1, 5, 20, 60),
        training_days=252,
        step=5,
    )

    combined_one_day = combined[
        combined["Horizon"] == 1
    ].reset_index(drop=True)

    pd.testing.assert_frame_equal(
        single.reset_index(drop=True),
        combined_one_day,
    )
