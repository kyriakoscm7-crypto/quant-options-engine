"""Regression tests for the public market-data licence safeguard."""

from dashboard.public_safety import (
    market_data_rights_confirmed,
    public_market_data_route_blocked,
)


def test_market_data_disabled_by_default(monkeypatch):
    monkeypatch.delenv("QI_MARKET_DATA_RIGHTS_CONFIRMED", raising=False)
    assert market_data_rights_confirmed() is False
    assert public_market_data_route_blocked("🔎 Stock Explorer") is True
    assert public_market_data_route_blocked("💎 Quant Discovery") is True
    assert public_market_data_route_blocked("🧠 Forecast Intelligence") is True


def test_educational_pages_still_available(monkeypatch):
    monkeypatch.delenv("QI_MARKET_DATA_RIGHTS_CONFIRMED", raising=False)
    for page in ("🏠 Overview", "📚 Learn", "💰 Options Lab", "📊 Greeks Analysis", "📈 Scenario Explorer", "📄 Legal & Privacy"):
        assert public_market_data_route_blocked(page) is False


def test_explicit_enable_flag_only(monkeypatch):
    monkeypatch.setenv("QI_MARKET_DATA_RIGHTS_CONFIRMED", "yes")
    assert market_data_rights_confirmed() is False
    monkeypatch.setenv("QI_MARKET_DATA_RIGHTS_CONFIRMED", "true")
    assert market_data_rights_confirmed() is True
    assert public_market_data_route_blocked("🔎 Stock Explorer") is False
