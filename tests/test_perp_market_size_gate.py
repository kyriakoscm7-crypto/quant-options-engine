"""Unapproved integration must not issue requests or reuse cached data."""

import pytest

from dashboard import perp_market_size


@pytest.mark.parametrize("value", [None, "", "false", "1"])
def test_disabled_integration_never_fetches_or_displays(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("QI_PERPEQUITIES_ENABLED", raising=False)
    else:
        monkeypatch.setenv("QI_PERPEQUITIES_ENABLED", value)
    monkeypatch.setattr(perp_market_size, "_market_universe", lambda: pytest.fail("snapshot accessed"))
    with pytest.raises(ValueError, match="disabled"):
        perp_market_size.market_universe()
    perp_market_size.render_perp_market_size("NASDAQ:AAPL")


def test_explicit_approved_opt_in(monkeypatch):
    monkeypatch.setenv("QI_PERPEQUITIES_ENABLED", "true")
    snapshot = {"records": []}
    monkeypatch.setattr(perp_market_size, "_market_universe", lambda: snapshot)
    assert perp_market_size.market_universe() is snapshot


def test_search_remains_available_without_provider(monkeypatch):
    from dashboard import stock_search

    monkeypatch.delenv("QI_PERPEQUITIES_ENABLED", raising=False)
    monkeypatch.setattr(perp_market_size, "_market_universe", lambda: pytest.fail("snapshot accessed"))
    monkeypatch.setattr(stock_search, "sec_search_directory", lambda agent: [])
    assert any("NASDAQ:AAPL" in item for item in stock_search.autocomplete_options("AAPL"))
