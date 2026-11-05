"""Acceptance regressions from the 2026-11-04 production audit."""

import asyncio
import json
import math
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from app.api.safety import RequestSafetyMiddleware
from app.pricing.black_scholes import BlackScholes
from dashboard.discovery_notebook import FIELDS, validate_import
from dashboard.portfolio_risk_lab import simulate_portfolio_distribution
from dashboard.scenario_workspace import scenario_rows
from dashboard.strategy_research import backtest_stats, run_strategy_backtest

ROOT = Path(__file__).parents[1]


def test_h01_first_day_loss_and_initial_entry():
    history = pd.DataFrame({"Close": [100, 101, 102, 103, 104] + [52] * 35})
    result = run_strategy_backtest(history, 2, 5)
    stats = backtest_stats(result)
    assert stats["max_drawdown_pct"] == pytest.approx(-50.074975)
    assert stats["entry_events"] == 1
    assert result["Strategy value"].iloc[0] < 51


@pytest.mark.parametrize("spot,strike", [(1e-300, 1e300), (1e300, 1e-300)])
def test_extreme_ratio_remains_finite(spot, strike):
    model = BlackScholes(spot, strike, 1, 0.05, 0.2)
    assert math.isfinite(model.d1)
    assert math.isfinite(model.call_price())
    assert math.isfinite(model.put_price())


def test_greeks_remain_full_precision_before_contract_scaling():
    model = BlackScholes(100, 100, 1, 0.05, 0.2)
    greek = model.greeks()["call_delta"]
    assert greek == pytest.approx(0.6368306511756191, abs=1e-14)
    assert abs(greek - round(greek, 4)) > 1e-5


@pytest.mark.parametrize("columns", [["A"], ["A", "B"]])
def test_constant_histories_have_json_safe_undefined_correlation(columns):
    prices = pd.DataFrame({name: np.full(40, 100.0) for name in columns})
    result = simulate_portfolio_distribution(prices, dict.fromkeys(columns, 1))
    assert result["mean_pairwise_correlation"] is None
    assert result["value_at_risk_95"] == 0
    json.dumps(
        {key: value for key, value in result.items() if key != "wealth"},
        allow_nan=False,
    )


def sample_notebook():
    return {
        "format": "Quant Intelligence research notebook v2",
        "records": [
            {
                "Listing": "NASDAQ:AAPL",
                "Status": "Monitoring",
                "Source URL": "https://www.sec.gov/",
                "Source as of": "2026",
                **dict.fromkeys(FIELDS, "public research"),
            }
        ],
    }


def test_notebook_restore_roundtrip():
    raw = json.dumps(sample_notebook()).encode()
    assert (
        validate_import(raw)["NASDAQ:AAPL"]["Next review trigger"] == "public research"
    )


@pytest.mark.parametrize(
    "change",
    ["format", "duplicate", "url", "status", "long", "unknown", "count", "type"],
)
def test_restore_rejects_invalid_records(change):
    data = sample_notebook()
    row = data["records"][0]
    if change == "format":
        data["format"] = "pickle"
    elif change == "duplicate":
        data["records"] *= 2
    elif change == "url":
        row["Source URL"] = "javascript:alert(1)"
    elif change == "status":
        row["Status"] = "Buy now"
    elif change == "long":
        row[FIELDS[0]] = "x" * 6001
    elif change == "unknown":
        row["score"] = 99
    elif change == "count":
        data["records"] *= 51
    elif change == "type":
        row[FIELDS[0]] = 2
    with pytest.raises(ValueError):
        validate_import(json.dumps(data).encode())


def test_restore_size_limit():
    with pytest.raises(ValueError):
        validate_import(b" " * 16_000_001)


def test_m02_model_survives_absent_widgets_and_scenario_navigation():
    app = AppTest.from_file(str(ROOT / "dashboard/main.py"))
    app.session_state["selected_page"] = "💰 Options Lab"
    app.run()
    app.number_input(key="qi_workspace_spot").set_value(123.0).run()
    app.session_state["selected_page"] = "🏠 Overview"
    app.run()
    app.session_state["selected_page"] = "💰 Options Lab"
    app.run()
    assert app.number_input(key="qi_workspace_spot").value == 123.0
    app.button(key="qi_options_to_scenario").click().run()
    assert app.number_input(key="qi_scenario_spot").value == 123.0
    assert not app.exception


@pytest.mark.parametrize(
    "key,route",
    [
        ("discover", "💎 Quant Discovery"),
        ("learn", "📚 Learn"),
        ("stock", "🔎 Stock Explorer"),
        ("portfolio", "💼 Portfolio Manager"),
    ],
)
def test_home_cards_use_session_navigation(key, route):
    app = AppTest.from_file(str(ROOT / "dashboard/main.py")).run()
    app.session_state["qi_discovery_notebook"] = {
        "NASDAQ:AAPL": sample_notebook()["records"][0]
    }
    app.button(key=f"qi_home_card_{key}").click().run()
    assert app.session_state["selected_page"] == route
    assert app.session_state["qi_discovery_notebook"] == {
        "NASDAQ:AAPL": sample_notebook()["records"][0]
    }
    assert not app.exception


def test_joint_scenario_matches_independent_engine():
    model = dict(
        kind="Call",
        spot=123.0,
        strike=100.0,
        days=30,
        vol=25,
        rate=4.0,
        dividend=0.0,
        contracts=2,
    )
    row = scenario_rows(model, [-10], 5, 7, -1)[0]
    initial = BlackScholes(123, 100, 30 / 365, 0.04, 0.25).call_price()
    shocked = BlackScholes(123 * 0.9, 100, 23 / 365, 0.04, 0.30).call_price()
    assert row["Position P/L"] == pytest.approx(-200 * (shocked - initial), abs=1e-10)
    with pytest.raises(ValueError):
        scenario_rows(model, [0], -30, 7, 1)


@pytest.mark.parametrize(
    "mode,token", [("production", ""), ("wrong", "a" * 32), ("production", "short")]
)
def test_h04_invalid_production_configuration_fails(mode, token):
    with pytest.raises(ValueError):
        RequestSafetyMiddleware(None, mode=mode, api_token=token)


def test_local_mode_denies_remote_and_still_rate_limits():
    app = FastAPI()
    app.add_middleware(
        RequestSafetyMiddleware, mode="development", requests_per_minute=1
    )

    @app.get("/calculate")
    def calculate():
        return {"ok": True}

    with TestClient(app, client=("203.0.113.1", 1)) as client:
        assert client.get("/calculate").status_code == 403
    with TestClient(app) as client:
        assert client.get("/calculate").status_code == 200
        assert client.get("/calculate").status_code == 429


def test_production_denies_duplicate_authorization_headers():
    app = FastAPI()
    app.add_middleware(RequestSafetyMiddleware, mode="production", api_token="a" * 32)
    with TestClient(app) as client:
        assert client.get("/docs").status_code == 401
        assert (
            client.get(
                "/docs", headers=[("Authorization", "Bearer " + "a" * 32)] * 2
            ).status_code
            == 401
        )


def test_body_timeout_and_concurrency_fail_closed(monkeypatch):
    async def slow():
        raise TimeoutError()

    sent = []

    async def send(message):
        sent.append(message)

    middleware = RequestSafetyMiddleware(None, mode="production", api_token="a" * 32)
    scope = dict(
        type="http",
        path="/calculate",
        method="POST",
        headers=[(b"authorization", b"Bearer " + b"a" * 32)],
    )
    asyncio.run(middleware(scope, slow, send))
    assert sent[0]["status"] == 408
    assert middleware.active_requests == 0
    sent.clear()
    middleware.active_requests = 8
    asyncio.run(middleware(scope, slow, send))
    assert sent[0]["status"] == 503


def test_offline_rss_rejects_entity_expansion_and_oversized_body(monkeypatch):
    from defusedxml.common import DefusedXmlException

    from app.intelligence.news_engine import fetch_company_news

    response = Mock()
    response.iter_content.return_value = [
        b'<!DOCTYPE foo [<!ENTITY x "expanded">]><rss>&x;</rss>'
    ]
    monkeypatch.setattr(
        "app.intelligence.news_engine.requests.get", lambda *a, **k: response
    )
    with pytest.raises(DefusedXmlException):
        fetch_company_news("AAPL")
    response.close.assert_called()
    response.iter_content.return_value = [b"x" * 1_000_001]
    with pytest.raises(ValueError, match="1 MB"):
        fetch_company_news("AAPL")


def test_final_form_field_snapshot_and_v1_restore():
    app = AppTest.from_string("""
from dashboard.discovery_notebook import render_discovery_notebook
render_discovery_notebook('NASDAQ:AAPL')
""").run()
    app.button(key="qi_discovery_add").click().run()
    app.text_area(key="qi_edit_NASDAQ:AAPL_Next review trigger").set_value(
        "last edit ✓"
    )
    next(b for b in app.button if b.label == "Save & prepare export").click().run()
    data = json.loads(app.session_state["qi_notebook_snapshot"])
    assert data["records"][0]["Next review trigger"] == "last edit ✓"
    assert data["revision"] == 1
    data["format"] = "Quant Intelligence research notebook v1"
    del data["records"][0]["Thesis & valuation"]
    assert (
        validate_import(json.dumps(data).encode())["NASDAQ:AAPL"]["Thesis & valuation"]
        == ""
    )


def test_delete_frees_slot_while_archived_records_count():
    app = AppTest.from_string("""
from dashboard.discovery_notebook import render_discovery_notebook
render_discovery_notebook('NASDAQ:NEW')
""")
    row = sample_notebook()["records"][0]
    app.session_state["qi_discovery_notebook"] = {
        f"NASDAQ:T{i}": {k: v for k, v in row.items() if k != "Listing"}
        for i in range(50)
    }
    app.run()
    assert app.button(key="qi_discovery_add").disabled
    app.selectbox(key="qi_edit_NASDAQ:T0_status").set_value("Archived")
    next(b for b in app.button if b.label == "Save & prepare export").click().run()
    assert app.button(key="qi_discovery_add").disabled
    app.button(key="qi_record_delete").click().run()
    assert len(app.session_state["qi_discovery_notebook"]) == 49
    assert not app.button(key="qi_discovery_add").disabled
    app.button(key="qi_discovery_add").click().run()
    assert "NASDAQ:NEW" in app.session_state["qi_discovery_notebook"]
    assert not app.exception


def test_negative_option_volatility_shock_is_rejected_visibly():
    app = AppTest.from_string(
        "from dashboard.options_workspace import render_options_workspace\nrender_options_workspace()"
    ).run()
    app.slider(key="qi_workspace_vol").set_value(5).run()
    app.slider(key="qi_workspace_volmove").set_value(-20).run()
    assert app.error and "No flooring" in app.error[0].value


@pytest.mark.parametrize(
    "params",
    [
        dict(T=1000, r=-1000, sigma=0.2),
        dict(T=1, r=0.05, sigma=1e200),
        dict(T=1e-300, r=0.05, sigma=1e-300),
    ],
)
def test_explicit_floating_point_domain(params):
    with pytest.raises(ValueError, match="supported numerical range"):
        BlackScholes(100, 100, **params)


def test_zero_loss_simulation_still_has_sampling_uncertainty():
    result = simulate_portfolio_distribution(
        pd.DataFrame({"A": np.full(40, 100.0)}), {"A": 1}
    )
    low, high = result["loss_probability_interval95"]
    assert low == pytest.approx(0, abs=1e-15)
    assert high > 0


def test_maximum_unicode_notebook_can_restore_its_own_export():
    data = sample_notebook()
    row = data["records"][0]
    row.update(dict.fromkeys(FIELDS, "💖" * 6000))
    data["records"] = [{**row, "Listing": f"NASDAQ:T{i}"} for i in range(50)]
    encoded = json.dumps(data, ensure_ascii=False).encode()
    assert len(encoded) > 2_000_000
    assert len(validate_import(encoded)) == 50
    with pytest.raises(ValueError, match="Invalid notebook JSON"):
        validate_import(b"[" * 2000 + b"]" * 2000)
