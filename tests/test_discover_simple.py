"""Regression coverage for the simple sidebar pages and honest source gaps."""
from datetime import date
from pathlib import Path

from streamlit.testing.v1 import AppTest

from dashboard.discover_intelligence import company_synopsis
from dashboard.earnings_week import week_bounds

MAIN = str(Path(__file__).parents[1] / "dashboard/main.py")


def test_calendar_week_crosses_year_and_has_seven_days():
    assert week_bounds(date(2027, 1, 1)) == (date(2026, 12, 28), date(2027, 1, 3))
    assert week_bounds(date(2027, 1, 1), 1) == (date(2027, 1, 4), date(2027, 1, 10))


def test_synopsis_uses_only_observed_financial_facts():
    assert "not enough" in company_synopsis({})
    text = company_synopsis({"research": {"factors": {"revenue_cagr": -.12, "operating_margin": -.03}}})
    assert "fell by 12.0%" in text and "lost about 3¢" in text
    assert "buy" not in text and "attractive" not in text


def test_two_sidebar_pages_and_calendar_navigation(monkeypatch):
    monkeypatch.delenv("QI_SEC_USER_AGENT", raising=False)
    app = AppTest.from_file(MAIN)
    app.session_state["selected_page"] = "💎 Quant Discovery"
    app.run(timeout=45)
    assert not app.exception
    labels = [b.label.lstrip("●› ") for b in app.sidebar.button]
    assert "Find stocks" in labels and "Earnings calendar" in labels
    assert "Scan & investigate" not in labels
    assert not any(t.label in {"Find stocks", "Earnings this week", "Overview", "8 factors"} for t in app.tabs)
    next(b for b in app.sidebar.button if b.label.endswith("Earnings calendar")).click().run()
    assert not app.exception
    assert app.session_state["selected_page"] == "📅 Earnings this week"
    assert any("tradingview.com/earnings-calendar/" in b.url for b in app.get("link_button"))
    assert not app.dataframe and not app.metric
    next(b for b in app.button if b.label == "Find stocks").click().run()
    assert not app.exception
    assert app.session_state["selected_page"] == "💎 Quant Discovery"
    assert any("research notebook" in e.label for e in app.expander)
    next(b for b in app.sidebar.button if b.label.endswith("Research")).click().run()
    assert any(b.label.endswith("Stock Explorer") for b in app.sidebar.button)
