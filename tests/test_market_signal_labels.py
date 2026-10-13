"""Tests for beginner-friendly market signal classifications."""

import math

import pytest

from app.market_data.market_signal_labels import classify_market_signal


@pytest.mark.parametrize(
    ("one_month", "three_month", "expected"),
    [
        (5.0, 12.0, "🟢 Bullish"),
        (-5.0, -12.0, "🔴 Bearish"),
        (5.0, -12.0, "🟡 Mixed"),
        (-5.0, 12.0, "🟡 Mixed"),
        (0.0, 5.0, "🟡 Mixed"),
        (0.0, 0.0, "🟡 Mixed"),
        (math.nan, 5.0, "⚪ Unavailable"),
        (math.inf, 5.0, "⚪ Unavailable"),
        (None, 5.0, "⚪ Unavailable"),
        ("invalid", 5.0, "⚪ Unavailable"),
    ],
)
def test_market_signal_classification(
    one_month,
    three_month,
    expected,
):
    signal, explanation = classify_market_signal(
        one_month,
        three_month,
    )

    assert signal == expected
    assert explanation


def test_unranked_stock_is_unavailable():
    signal, explanation = classify_market_signal(
        5.0,
        12.0,
        ranking_status="Insufficient Data",
    )

    assert signal == "⚪ Unavailable"
    assert explanation
