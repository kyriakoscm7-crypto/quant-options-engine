"""Offline tests for searchable company identity records."""

import pytest

from app.intelligence.company_registry import CompanyRegistry


@pytest.fixture
def registry():
    return CompanyRegistry({
        "0": {
            "ticker": "AAPL",
            "title": "Apple Inc.",
            "cik_str": 320193,
        },
        "1": {
            "ticker": "NVDA",
            "title": "NVIDIA Corporation",
            "cik_str": 1045810,
        },
        "2": {
            "ticker": "BRK-B",
            "title": "Berkshire Hathaway Inc.",
            "cik_str": 1067983,
        },
        "3": {
            "ticker": "PLTR",
            "title": "Palantir Technologies Inc.",
            "cik_str": 1321655,
        },
        "4": {
            "ticker": "CELH",
            "title": "Celsius Holdings Inc.",
            "cik_str": 1341766,
        },
    })


def test_search_exact_ticker(registry):
    assert registry.search("AAPL")[0].name == "Apple Inc."


def test_search_company_name(registry):
    assert registry.search("Palantir")[0].ticker == "PLTR"


def test_search_is_case_insensitive(registry):
    assert registry.search("nvidia")[0].ticker == "NVDA"


def test_search_share_class(registry):
    assert registry.search("BRK.B")[0].ticker == "BRK-B"


def test_search_partial_company_name(registry):
    assert registry.search("Celsius")[0].ticker == "CELH"


def test_unknown_company_returns_empty(registry):
    assert registry.search("CompletelyUnknownCompany") == []


def test_resolve_cik(registry):
    company = registry.resolve_ticker("AAPL")
    assert company.cik == "0000320193"


def test_duplicate_records_are_removed():
    record = {
        "ticker": "AAPL",
        "title": "Apple Inc.",
        "cik_str": 320193,
    }
    registry = CompanyRegistry({"0": record, "1": record})
    assert len(registry.companies) == 1


def test_ticker_collisions_are_rejected():
    registry = CompanyRegistry({
        "0": {
            "ticker": "ABC",
            "title": "Company One",
            "cik_str": 1001,
        },
        "1": {
            "ticker": "ABC",
            "title": "Company Two",
            "cik_str": 1002,
        },
    })

    assert len(registry.search("ABC")) == 2

    with pytest.raises(ValueError, match="Ambiguous"):
        registry.resolve_ticker("ABC")


def test_exchange_cannot_be_assumed(registry):
    with pytest.raises(ValueError, match="unqualified"):
        registry.resolve_ticker("NASDAQ:AAPL")


@pytest.mark.parametrize("query", ["", "   ", "!!!"])
def test_invalid_search(query, registry):
    with pytest.raises(ValueError):
        registry.search(query)


def test_search_limit(registry):
    assert len(registry.search("Inc", limit=2)) <= 2
