"""Tests for company identity resolution."""

import pytest

from app.intelligence.company_identity import (
    normalize_ticker,
    resolve_sec_company,
)

RECORDS = {
    "0": {
        "cik_str": 320193,
        "ticker": "AAPL",
        "title": "Apple Inc.",
    },
    "1": {
        "cik_str": 1067983,
        "ticker": "BRK-B",
        "title": "Berkshire Hathaway Inc.",
    },
}


def test_resolves_apple():
    result = resolve_sec_company("AAPL", RECORDS)
    assert result.name == "Apple Inc."
    assert result.cik == "0000320193"


def test_normalizes_share_class():
    assert normalize_ticker("NYSE:BRK.B") == "BRK-B"
    result = resolve_sec_company("BRK.B", RECORDS)
    assert result.ticker == "BRK-B"


def test_unknown_ticker_does_not_guess():
    assert resolve_sec_company("UNKNOWN", RECORDS) is None


@pytest.mark.parametrize("symbol", ["", "../../etc", "AAPL!", ""])
def test_rejects_invalid_symbols(symbol):
    with pytest.raises(ValueError):
        normalize_ticker(symbol)


def test_ambiguous_identity_is_rejected():
    records = {
        "0": RECORDS["0"],
        "1": {
            "cik_str": 123456,
            "ticker": "AAPL",
            "title": "Different Company",
        },
    }
    with pytest.raises(ValueError, match="Ambiguous"):
        resolve_sec_company("AAPL", records)


def test_no_valid_company_metadata():
    assert resolve_sec_company(
        "AAPL",
        {"0": {"ticker": "AAPL", "title": "", "cik_str": None}},
    ) is None
