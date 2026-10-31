"""Fictional stock valuation examples, not market forecasts."""

from math import isfinite

SCENARIOS = {
    "Earnings beat, outlook weakens": {
        "reported_eps": 1.20,
        "expected_quarter_eps": 1.00,
        "future_eps": 4.00,
        "new_multiple": 18.0,
        "explanation": (
            "The latest quarter is better than expected, but "
            "the estimated future earnings and valuation multiple "
            "are lower than investors previously assumed."
        ),
    },
    "Earnings beat, outlook improves": {
        "reported_eps": 1.20,
        "expected_quarter_eps": 1.00,
        "future_eps": 6.00,
        "new_multiple": 22.0,
        "explanation": (
            "Stronger earnings are accompanied by a better outlook "
            "and a higher illustrative valuation multiple."
        ),
    },
    "Good results, largely anticipated": {
        "reported_eps": 1.02,
        "expected_quarter_eps": 1.00,
        "future_eps": 5.00,
        "new_multiple": 20.0,
        "explanation": (
            "The quarter is slightly better than expected, "
            "but the longer-term assumptions barely change."
        ),
    },
}

BASELINE_FUTURE_EPS = 5.0
BASELINE_MULTIPLE = 20.0


def valuation_case(
    expected_quarter_eps: float,
    reported_eps: float,
    old_future_eps: float,
    old_multiple: float,
    new_future_eps: float,
    new_multiple: float,
) -> dict:
    """Compare implied prices using forward EPS times a P/E multiple.

    This is a stylized sensitivity exercise, not a price forecast.
    """
    values = (
        expected_quarter_eps, reported_eps, old_future_eps,
        old_multiple, new_future_eps, new_multiple,
    )
    if not all(
        isinstance(x, (int, float)) and isfinite(x)
        for x in values
    ):
        raise ValueError("Inputs must be finite numbers.")
    if (
        expected_quarter_eps <= 0
        or old_future_eps <= 0
        or new_future_eps <= 0
        or old_multiple <= 0
        or new_multiple <= 0
    ):
        raise ValueError("Forecast earnings and multiples must be positive.")

    before = old_future_eps * old_multiple
    after = new_future_eps * new_multiple
    beat_pct = (
        (reported_eps / expected_quarter_eps - 1) * 100
    )
    change_pct = (after / before - 1) * 100

    return {
        "before": before,
        "after": after,
        "quarter_surprise_pct": beat_pct,
        "implied_change_pct": change_pct,
        "earnings_effect_pct": (
            new_future_eps / old_future_eps - 1
        ) * 100,
        "multiple_effect_pct": (
            new_multiple / old_multiple - 1
        ) * 100,
    }
