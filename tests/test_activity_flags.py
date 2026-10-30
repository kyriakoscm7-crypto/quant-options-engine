"""Regression tests for descriptive market activity flags."""

import math

import pytest

from app.market_data.activity_flags import classify_activity


@pytest.mark.parametrize(
    ("gap_z", "volume", "expected"),
    [
        (0.5, 1.1, ()),
        (1.99, 1.99, ()),
        (2.0, 1.0, ("unusual standardized gap",)),
        (-2.0, 1.0, ("unusual standardized gap",)),
        (0.0, 2.0, ("elevated trading volume",)),
        (
            3.5,
            4.0,
            (
                "unusual standardized gap",
                "elevated trading volume",
            ),
        ),
        (math.nan, math.inf, ()),
        (None, None, ()),
    ],
)
def test_activity_classification(gap_z, volume, expected):
    assert classify_activity(gap_z, volume) == expected


def test_invalid_input_does_not_trigger_activity():
    assert classify_activity("not available", None) == ()
