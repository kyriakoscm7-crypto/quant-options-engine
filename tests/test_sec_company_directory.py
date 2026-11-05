"""Offline security and parsing tests for the SEC directory."""

import json

import pytest

from app.intelligence import sec_company_directory as directory


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status
        self.closed = False

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError("SEC request failed")

    def iter_content(self, chunk_size):
        yield self.payload

    def close(self):
        self.closed = True


def test_requires_declared_user_agent(monkeypatch):
    monkeypatch.delenv("QI_SEC_USER_AGENT", raising=False)
    with pytest.raises(ValueError, match="QI_SEC_USER_AGENT"):
        directory._declared_user_agent()


def test_download_and_resolve(monkeypatch):
    monkeypatch.setenv(
        "QI_SEC_USER_AGENT",
        "QuantIntelligence Research research@example.org",
    )
    records = {
        "0": {
            "cik_str": 320193,
            "ticker": "AAPL",
            "title": "Apple Inc.",
        }
    }
    response = FakeResponse(json.dumps(records).encode())

    def fake_get(url, **kwargs):
        assert url == directory.SEC_DIRECTORY_URL
        assert "User-Agent" in kwargs["headers"]
        assert kwargs["stream"] is True
        return response

    monkeypatch.setattr(directory.requests, "get", fake_get)

    loaded = directory.fetch_sec_company_directory()
    result = directory.find_sec_company("NASDAQ:AAPL", loaded)

    assert result.name == "Apple Inc."
    assert result.cik == "0000320193"
    assert response.closed


def test_rejects_oversized_directory(monkeypatch):
    monkeypatch.setenv(
        "QI_SEC_USER_AGENT",
        "QuantIntelligence Research research@example.org",
    )
    response = FakeResponse(
        b"x" * (directory.MAX_RESPONSE_BYTES + 1)
    )
    monkeypatch.setattr(
        directory.requests, "get", lambda *args, **kwargs: response
    )

    with pytest.raises(ValueError, match="too large"):
        directory.fetch_sec_company_directory()

    assert response.closed


def test_rejects_invalid_json(monkeypatch):
    monkeypatch.setenv(
        "QI_SEC_USER_AGENT",
        "QuantIntelligence Research research@example.org",
    )
    monkeypatch.setattr(
        directory.requests,
        "get",
        lambda *args, **kwargs: FakeResponse(b"invalid json"),
    )

    with pytest.raises(ValueError):
        directory.fetch_sec_company_directory()
