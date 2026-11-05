"""Offline integration and adversarial coverage regression checks."""
from datetime import UTC, datetime

import pytest

from app.intelligence.company_identity import CompanyIdentity
from app.intelligence.news_events import NewsEventsService, Provider
from app.intelligence.news_reliability import NewsRateLimited

NOW = datetime(2026, 11, 5, tzinfo=UTC)
COMPANY = CompanyIdentity('AAPL', 'Apple Inc.', '0000320193')


def article(**kwargs):
    return dict(title='Apple Inc. announces results', url='https://publisher.test/story',
                published='2026-11-04T12:00:00Z', **kwargs)


def submissions(company):
    return {'filings': {'recent': {'accessionNumber': ['0000320193-26-000001'],
            'filingDate': ['2026-11-04'], 'form': ['8-K'], 'primaryDocument': ['report.htm']}}}


def test_rights_gate_runs_before_network():
    def forbidden(*a, **k):
        pytest.fail('Unlicensed loader invoked')
    service = NewsEventsService([Provider('blocked', forbidden, True)], submissions)
    report = service.build(COMPANY, now=NOW)
    assert report.diagnostics[0]['status'] == 'disabled'
    assert len(report.filings) == 1


def test_provider_failure_isolated_and_cross_provider_dedup():
    def limited(*a, **k):
        raise NewsRateLimited('429')
    providers = [Provider('limited', limited, True, 'contract'),
                 Provider('one', lambda *a, **k: [article()], True, 'contract'),
                 Provider('two', lambda *a, **k: [article()], True, 'contract')]
    report = NewsEventsService(providers, submissions).build(COMPANY, now=NOW)
    assert len(report.articles) == 1
    assert report.duplicates == 1
    assert report.diagnostics[0]['status'] == 'unavailable'
    assert report.articles[0]['relevance'] == 'likely'


def test_invalid_future_and_unsafe_articles_rejected():
    rows = [article(), {'title': 'bad', 'url': 'javascript:alert(1)', 'published': NOW.isoformat()},
            {'title': 'future', 'url': 'https://a.test', 'published': '2027-01-01T00:00:00Z'},
            {'title': 'naive', 'url': 'https://a.test', 'published': '2026-11-04T00:00:00'}]
    report = NewsEventsService([Provider('test', lambda *a, **k: rows, True, 'contract')], submissions).build(COMPANY, now=NOW)
    assert report.rejected == 3
    assert len(report.articles) == 1


def test_cache_and_event_window_are_independent():
    calls = []
    def loader(company):
        calls.append(company.cik)
        return submissions(company)
    service = NewsEventsService(filings_loader=loader)
    assert len(service.build(COMPANY, now=NOW).filings) == 1
    report = service.build(COMPANY, event_date='2026-10-01', now=NOW)
    assert not report.filings
    assert len(calls) == 1
    assert report.diagnostics[-1]['status'] == 'cached'


def test_sec_failure_not_empty_success():
    def broken(company):
        raise ValueError('private contact must not leak')
    report = NewsEventsService(filings_loader=broken).build(COMPANY, now=NOW)
    assert report.diagnostics[-1]['status'] == 'unavailable'
    assert 'private contact' not in str(report)


@pytest.mark.parametrize('cik', [0, -1, 10000000000])
def test_invalid_sec_identifiers_cannot_enter_registry(cik):
    from app.intelligence.company_registry import CompanyRegistry
    registry = CompanyRegistry({'0': {'ticker': 'BAD', 'title': 'Invalid', 'cik_str': cik}})
    assert not registry.companies


def test_gdelt_is_optional_by_default(monkeypatch):
    from app.intelligence.news_service import get_company_news
    monkeypatch.delenv('QI_GDELT_ENABLED', raising=False)
    result = get_company_news('Apple Inc.')
    assert result.status == 'unavailable'
    assert 'disabled' in result.message
