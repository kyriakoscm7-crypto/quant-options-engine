import pytest

from app.education.diversification_models import EVENTS, PORTFOLIOS, stress_test


def test_each_portfolio_has_valid_weights():
    for weights in PORTFOLIOS.values():
        assert sum(weights.values()) == 100


def test_company_specific_loss_is_weighted_correctly():
    event = EVENTS["One company disappoints"]
    concentrated = stress_test(PORTFOLIOS["Concentrated"], event)
    spread = stress_test(PORTFOLIOS["Evenly spread"], event)
    assert concentrated["end"] == pytest.approx(790)
    assert spread["end"] == pytest.approx(925)


def test_broad_selloff_affects_all_portfolios():
    event = EVENTS["A broad market sell-off"]
    for weights in PORTFOLIOS.values():
        assert stress_test(weights, event)["end"] < 1000


def test_change_equals_sum_of_holding_impacts():
    for event in EVENTS.values():
        for weights in PORTFOLIOS.values():
            result = stress_test(weights, event)
            assert sum(d["change"] for d in result["details"]) == pytest.approx(
                result["change"]
            )
            assert result["start"] + result["change"] == pytest.approx(
                result["end"]
            )


def test_rejects_invalid_portfolio_weights():
    with pytest.raises(ValueError):
        stress_test({"A": 70, "B": 20}, {"A": -30, "B": 0})
