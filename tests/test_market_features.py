"""Tests for market features and forward-return labels."""

import numpy as np
import pandas as pd
import pytest

from app.forecasting.market_features import (
    FEATURE_COLUMNS,
    build_forward_labels,
    build_market_features,
)


def make_prices(n=350, seed=42):
    rng = np.random.default_rng(seed)
    returns = rng.normal(0.0004, 0.012, n - 1)
    return pd.Series(100 * np.exp(np.r_[0.0, np.cumsum(returns)]))


def test_all_expected_features_exist():
    features = build_market_features(make_prices())

    assert list(features.columns) == list(FEATURE_COLUMNS)


def test_feature_index_matches_prices():
    prices = make_prices()
    features = build_market_features(prices)

    assert features.index.equals(prices.index)


def test_momentum_calculation():
    prices = make_prices()
    features = build_market_features(prices)

    expected = np.log(prices.iloc[220] / prices.iloc[215])

    assert features["momentum_5d"].iloc[220] == pytest.approx(
        expected
    )


def test_reversal_calculation():
    prices = make_prices()
    features = build_market_features(prices)

    expected = -np.log(prices.iloc[220] / prices.iloc[219])

    assert features["reversal_1d"].iloc[220] == pytest.approx(
        expected
    )


def test_volatility_calculation():
    prices = make_prices()
    features = build_market_features(prices)

    returns = np.log(prices).diff()
    expected = returns.iloc[201:221].std()

    assert features["volatility_20d"].iloc[220] == pytest.approx(
        expected
    )


def test_trend_calculation():
    prices = make_prices()
    features = build_market_features(prices)

    expected = prices.iloc[220] / prices.iloc[21:221].mean() - 1

    assert features["trend_200d"].iloc[220] == pytest.approx(
        expected
    )


def test_future_prices_do_not_change_past_features():
    prices = make_prices()

    original = build_market_features(prices)

    modified = prices.copy()
    modified.iloc[250:] *= 3

    updated = build_market_features(modified)

    pd.testing.assert_frame_equal(
        original.iloc[:250],
        updated.iloc[:250],
    )


def test_prefix_features_match_full_history():
    prices = make_prices()

    full = build_market_features(prices)
    prefix = build_market_features(prices.iloc[:260])

    pd.testing.assert_frame_equal(
        full.iloc[:260],
        prefix,
    )


def test_initial_features_are_missing_until_available():
    features = build_market_features(make_prices())

    assert pd.isna(features["trend_200d"].iloc[198])
    assert pd.notna(features["trend_200d"].iloc[199])


def test_forward_labels_are_correct():
    prices = pd.Series([100.0, 110.0, 105.0, 120.0])

    labels = build_forward_labels(prices, horizon_days=1)

    assert labels.iloc[0] == 1
    assert labels.iloc[1] == 0
    assert labels.iloc[2] == 1
    assert pd.isna(labels.iloc[3])


def test_unmatured_labels_are_missing():
    labels = build_forward_labels(
        make_prices(),
        horizon_days=20,
    )

    assert labels.iloc[-20:].isna().all()
    assert labels.iloc[:-20].notna().all()


def test_constant_prices_have_zero_momentum():
    prices = pd.Series(np.full(350, 100.0))

    features = build_market_features(prices)

    assert features["momentum_20d"].iloc[-1] == pytest.approx(0)
    assert features["volatility_20d"].iloc[-1] == pytest.approx(0)
    assert pd.isna(features["volatility_ratio"].iloc[-1])


@pytest.mark.parametrize("bad_price", [0, -1, np.nan, np.inf])
def test_invalid_prices_are_rejected(bad_price):
    prices = make_prices()
    prices.iloc[100] = bad_price

    with pytest.raises(ValueError):
        build_market_features(prices)


@pytest.mark.parametrize("bad_horizon", [0, -1, True, 1.5])
def test_invalid_horizons_are_rejected(bad_horizon):
    with pytest.raises(ValueError):
        build_forward_labels(make_prices(), bad_horizon)


def test_duplicate_price_index_is_rejected():
    prices = make_prices()
    prices.index = [0] * len(prices)

    with pytest.raises(ValueError):
        build_market_features(prices)


def test_insufficient_history_is_rejected():
    with pytest.raises(ValueError):
        build_market_features(make_prices(n=150))
