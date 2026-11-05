"""Regressions found during the release audit; all providers remain offline."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.intelligence.company_directory_service import CompanyDirectoryService
from app.intelligence.news_reliability import (
    NewsRateLimited,
    NewsReliability,
    retry_after_seconds,
)


def test_google_429_closes_response_and_starts_cross_company_cooldown(monkeypatch):
    from app.intelligence import news_engine
    closed = []
    calls = []
    response = SimpleNamespace(status_code=429, headers={"Retry-After": "600"}, close=lambda: closed.append(True))
    def get(*args, **kwargs):
        calls.append(True)
        return response
    monkeypatch.setattr(news_engine.requests, 'get', get)
    clock = [0]
    cache = NewsReliability(clock=lambda: clock[0])
    def loader():
        return news_engine.fetch_company_news('AAPL', 'Apple Inc.')
    assert cache.fetch('Google', 'Apple', loader).status == 'unavailable'
    clock[0] = 301
    assert cache.fetch('Google', 'Microsoft', loader).status == 'unavailable'
    assert calls == [True]
    assert closed == [True]


def test_directory_rate_limit_does_not_repeat_on_each_rerender():
    calls = []
    clock = [0]
    def fetch():
        calls.append(True)
        raise NewsRateLimited('SEC', 600)
    service = CompanyDirectoryService(fetcher=fetch, clock=lambda: clock[0])
    assert service.get().status == 'unavailable'
    clock[0] = 301
    assert service.get().status == 'unavailable'
    assert len(calls) == 1
    clock[0] = 601
    service.get()
    assert len(calls) == 2


@pytest.mark.parametrize('value', ['invalid', '', '-10'])
def test_invalid_retry_after_is_safe(value):
    assert retry_after_seconds(SimpleNamespace(headers={'Retry-After': value})) == 0


def test_http_date_retry_after():
    from email.utils import format_datetime
    value = format_datetime(datetime.now(UTC) + timedelta(seconds=900))
    assert 895 <= retry_after_seconds(SimpleNamespace(headers={'Retry-After': value})) <= 900


def test_sec_submissions_mismatched_cik_rejected_and_closed(monkeypatch):
    import json

    from app.intelligence import news_events
    from app.intelligence.company_identity import CompanyIdentity
    closed = []
    response = SimpleNamespace(status_code=200, raise_for_status=lambda: None,
        iter_content=lambda size: [json.dumps({'cik': 789019, 'filings': {'recent': {}}}).encode()],
        close=lambda: closed.append(True))
    monkeypatch.setenv('QI_SEC_USER_AGENT', 'Quant Intelligence contact@example.org')
    monkeypatch.setattr(news_events.requests, 'get', lambda *a, **k: response)
    with pytest.raises(ValueError, match='identity mismatch'):
        news_events.fetch_submissions(CompanyIdentity('AAPL', 'Apple Inc.', '0000320193'))
    assert closed == [True]


def test_gdelt_first_seen_is_not_publication_time():
    from app.intelligence.gdelt_news import parse_articles
    rows = parse_articles({'articles': [{'title': 'Example', 'url': 'https://publisher.test/a',
        'seendate': '20261104T120000Z'}]}, 7, datetime(2026, 11, 5, tzinfo=UTC))
    assert rows[0]['timestamp_kind'] == 'first_seen'


def test_optional_malformed_sec_descriptions_do_not_break_filings():
    from app.intelligence.sec_filings import filings_near_event
    rows = filings_near_event({'filings': {'recent': {
        'accessionNumber': ['0000320193-26-000001'], 'filingDate': ['2026-11-04'],
        'form': ['8-K'], 'primaryDocument': ['report.htm'], 'primaryDocDescription': None}}},
        320193, '2026-11-05')
    assert len(rows) == 1
    assert rows[0]['description'] == ''
