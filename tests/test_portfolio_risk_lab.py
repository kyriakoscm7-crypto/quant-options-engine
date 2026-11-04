"""Portfolio risk studio is entirely offline, deterministic and mathematically coherent."""

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard.demo_showcase import synthetic_history
from dashboard.portfolio_risk_lab import simulate_portfolio_distribution

SYMBOLS = ("ORION", "HARBOR", "CEDAR")
PRICES = pd.DataFrame({
    s: synthetic_history(s)["Close"].tail(253).to_numpy()
    for s in SYMBOLS
})


def test_monte_carlo_reproducible_and_ordered():
    a = simulate_portfolio_distribution(
        PRICES, {"ORION": 15, "HARBOR": 30, "CEDAR": 8}
    )
    b = simulate_portfolio_distribution(
        PRICES, {"ORION": 15, "HARBOR": 30, "CEDAR": 8}
    )
    np.testing.assert_array_equal(a["wealth"], b["wealth"])
    assert a["wealth"].shape == (1200, 31)
    assert a["quantile5"] <= a["median"] <= a["quantile95"]
    assert 0 <= a["loss_probability"] <= 1
    assert a["value_at_risk_95"] >= 0
    assert a["expected_shortfall_95"] >= a["value_at_risk_95"]
    assert sum(a["weights"].values()) == pytest.approx(1.0)
    assert np.all(a["wealth"] > 0)


def test_zero_quantity_does_not_alter_simulation():
    just_one = simulate_portfolio_distribution(PRICES, {"ORION": 4})
    with_zeros = simulate_portfolio_distribution(
        PRICES, {"ORION": 4, "HARBOR": 0}
    )
    np.testing.assert_allclose(
        just_one["wealth"], with_zeros["wealth"],
        rtol=1e-12, atol=1e-9
    )


@pytest.mark.parametrize("quantities", [
    {"ORION": -1}, {"ORION": float("nan")},
    {"ORION": 0}, {"UNKNOWN": 1}, {},
])
def test_reject_bad_holdings(quantities):
    with pytest.raises(ValueError):
        simulate_portfolio_distribution(PRICES, quantities)


@pytest.mark.parametrize("sessions,paths", [
    (1, 1200), (253, 1200), (30, 10), (30, 10001)
])
def test_reject_bad_simulation_limits(sessions, paths):
    with pytest.raises(ValueError):
        simulate_portfolio_distribution(
            PRICES, {"ORION": 4}, sessions=sessions, paths=paths
        )


def test_private_portfolio_page_monte_carlo_ui_renders_offline(monkeypatch):
    import app.market_data.stock_history as stock_history

    def forbidden(*args, **kwargs):
        raise AssertionError("Risk studio must not request market data")

    monkeypatch.setattr(stock_history, "fetch_stock_history", forbidden)
    app = AppTest.from_string(
        "from dashboard.demo_showcase import render_demo_portfolio\n"
        "render_demo_portfolio()\n"
    ).run(timeout=45)
    assert not app.exception, [str(e.message) for e in app.exception]
    assert any("SYNTHETIC DEMO" in i.value for i in app.info)
    assert any("Monte Carlo" in heading.value for heading in app.markdown)
