import pytest

from app.education.market_expectations import (
    SCENARIOS,
    valuation_case,
)


def test_earnings_beat_can_imply_lower_valuation():
    case = SCENARIOS["Earnings beat, outlook weakens"]
    result = valuation_case(
        case["expected_quarter_eps"], case["reported_eps"],
        5, 20, case["future_eps"], case["new_multiple"],
    )
    assert result["quarter_surprise_pct"] == pytest.approx(20)
    assert result["before"] == pytest.approx(100)
    assert result["after"] == pytest.approx(72)
    assert result["implied_change_pct"] == pytest.approx(-28)


def test_stronger_outlook_implies_higher_valuation():
    case = SCENARIOS["Earnings beat, outlook improves"]
    result = valuation_case(
        case["expected_quarter_eps"], case["reported_eps"],
        5, 20, case["future_eps"], case["new_multiple"],
    )
    assert result["after"] > result["before"]


def test_unchanged_assumptions_keep_same_implied_value():
    result = valuation_case(1, 1.2, 5, 20, 5, 20)
    assert result["implied_change_pct"] == pytest.approx(0)


def test_compounded_valuation_effect():
    result = valuation_case(1, 1.1, 5, 20, 5.5, 22)
    assert result["implied_change_pct"] == pytest.approx(21)


@pytest.mark.parametrize("eps,multiple", [
    (0, 20), (-1, 20), (5, 0), (5, -2)
])
def test_invalid_forward_assumptions(eps, multiple):
    with pytest.raises(ValueError):
        valuation_case(1, 1.2, 5, 20, eps, multiple)
