"""Offline GDELT retrieval and data-quality tests."""

import json
from datetime import UTC, datetime, timedelta

import pytest

from app.intelligence import gdelt_news as news


def article(title, url, published):
    return {
        "title": title,
        "url": url,
        "seendate": published.strftime("%Y%m%dT%H%M%SZ"),
        "language": "English",
    }


def test_company_query():
    assert news.build_query("Apple Inc.") == '"Apple Inc."'


@pytest.mark.parametrize("name", ["", "A", "AAPL OR x", "AAPL!"])
def test_rejects_bad_company_queries(name):
    with pytest.raises(ValueError):
        news.build_query(name)


def test_freshness_deduplication_and_url_validation():
    now = datetime.now(UTC)
    current = article("Recent article", "https://example.org/one", now)
    old = article(
        "Old article",
        "https://example.org/old",
        now - timedelta(days=15),
    )
    unsafe = article(
        "Unsafe article",
        "javascript:alert(1)",
        now,
    )
    payload = {"articles": [current, current, old, unsafe]}

    results = news.parse_articles(payload, days=7, now=now)

    assert len(results) == 1
    assert results[0]["title"] == "Recent article"
    assert results[0]["company_match"] == "unverified"


def test_rejects_future_articles():
    now = datetime.now(UTC)
    payload = {
        "articles": [
            article(
                "Future article",
                "https://example.org/future",
                now + timedelta(days=1),
            )
        ]
    }
    assert news.parse_articles(payload, 7, now) == []


def test_rejects_invalid_payload():
    with pytest.raises(ValueError):
        news.parse_articles({"articles": "invalid"}, 7)


def test_live_request_is_mocked(monkeypatch):
    now = datetime.now(UTC)

    class FakeResponse:
        def __init__(self):
            self.closed = False
            self.status_code = 200

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size):
            yield json.dumps({
                "articles": [
                    article(
                        "Company report",
                        "https://example.org/report",
                        now,
                    )
                ]
            }).encode()

        def close(self):
            self.closed = True

    response = FakeResponse()

    def fake_get(url, **kwargs):
        assert url == news.GDELT_URL
        assert kwargs["params"]["sort"] == "DateDesc"
        assert kwargs["params"]["timespan"] == "7d"
        assert kwargs["stream"] is True
        return response

    monkeypatch.setattr(news.requests, "get", fake_get)

    results = news.fetch_gdelt_news("Apple Inc.")

    assert len(results) == 1
    assert results[0]["source"] == "GDELT Project"
    assert response.closed


def test_rejects_oversized_response(monkeypatch):
    class FakeResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def iter_content(self, chunk_size):
            yield b"x" * (news.MAX_BYTES + 1)

        def close(self):
            self.closed = True

    response = FakeResponse()
    monkeypatch.setattr(
        news.requests, "get", lambda *a, **k: response
    )

    with pytest.raises(ValueError, match="size limit"):
        news.fetch_gdelt_news("Apple Inc.")

    assert response.closed


def test_rate_limit_is_handled_and_response_closed(monkeypatch):
    class FakeResponse:
        status_code = 429

        def __init__(self):
            self.closed = False

        def raise_for_status(self):
            raise AssertionError("Should detect 429 before this call")

        def close(self):
            self.closed = True

    response = FakeResponse()

    monkeypatch.setattr(
        news.requests,
        "get",
        lambda *args, **kwargs: response,
    )

    with pytest.raises(RuntimeError, match="rate-limiting"):
        news.fetch_gdelt_news("Apple Inc.")

    assert response.closed
