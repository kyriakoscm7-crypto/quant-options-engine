"""The public research showcase is synthetic, deterministic and offline."""

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard.demo_showcase import (
    DEMO_ASSETS,
    RESEARCH_ROUTES,
    _pct_change,
    _ranking,
    forecast_demo_metrics,
    synthetic_history,
)
from dashboard.public_safety import public_market_data_route_blocked


@pytest.mark.parametrize("symbol", list(DEMO_ASSETS))
def test_synthetic_ohlcv_is_deterministic_and_well_formed(symbol):
    first = synthetic_history(symbol)
    second = synthetic_history(symbol)
    pd.testing.assert_frame_equal(first, second)
    assert len(first) == 1008
    assert first.index.is_monotonic_increasing
    assert first.notna().all().all()
    assert (first[["Open", "High", "Low", "Close"]] > 0).all().all()
    assert (first["High"] >= first[["Open", "Close"]].max(axis=1)).all()
    assert (first["Low"] <= first[["Open", "Close"]].min(axis=1)).all()


def test_demo_symbols_are_fictional_and_explicitly_named():
    assert {"AAPL", "MSFT", "NVDA", "SPY"}.isdisjoint(DEMO_ASSETS)
    assert all("demo" not in name.lower() for name in DEMO_ASSETS)
    assert DEMO_ASSETS["ATLAS"]["sector"] == "Synthetic index"


def test_scanner_rankings_use_real_math_on_synthetic_inputs():
    table = _ranking()
    assert len(table) == len(DEMO_ASSETS) - 1
    assert table["Symbol"].is_unique
    assert table["Technical score / 100"].between(0, 100).all()
    assert (table["Synthetic volatility (%)"] > 0).all()
    assert (table["Synthetic drawdown (%)"] <= 0).all()
    assert all(
        isinstance(_pct_change(synthetic_history(symbol), 20), float)
        for symbol in table["Symbol"]
    )


@pytest.mark.parametrize("horizon", [1, 5, 20])
def test_forecast_example_uses_historical_inputs_and_future_targets(horizon):
    out = forecast_demo_metrics("ORION", horizon)
    source = synthetic_history("ORION")["Close"]
    assert len(out) == 120
    assert (out["No-change baseline"] == source.loc[out.index]).all()
    expected = source.shift(-horizon).loc[out.index]
    pd.testing.assert_series_equal(
        out["Synthetic actual"], expected.rename("Synthetic actual")
    )


def test_unknown_symbol_and_horizon_are_rejected():
    with pytest.raises(ValueError):
        synthetic_history("AAPL")
    with pytest.raises(ValueError):
        forecast_demo_metrics("ORION", 999)


def test_every_public_data_sensitive_route_is_in_the_demo_router(monkeypatch):
    monkeypatch.delenv("QI_MARKET_DATA_RIGHTS_CONFIRMED", raising=False)
    assert len(RESEARCH_ROUTES) == 5
    for route in RESEARCH_ROUTES:
        assert public_market_data_route_blocked(route)


@pytest.mark.parametrize("route", sorted(RESEARCH_ROUTES))
def test_every_synthetic_research_page_renders_without_exception(route):
    # Exercise real Streamlit widget code, not only pure pricing logic.
    source = (
        "from dashboard.demo_showcase import render_demo_research_page\n"
        f"render_demo_research_page({route!r})\n"
    )
    app = AppTest.from_string(source).run(timeout=45)
    assert not app.exception, [str(error.message) for error in app.exception]
