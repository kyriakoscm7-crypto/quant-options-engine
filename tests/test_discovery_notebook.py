"""Research survives rerenders, stays isolated, and never fetches evidence links."""

from urllib.parse import parse_qs, urlsplit

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.discovery_notebook import (
    comparison_rows,
    official_filings_url,
    safe_source_url,
)

APP = '''
import streamlit as st
from dashboard.discovery_notebook import render_discovery_notebook
symbol = st.selectbox('Listing', ['NASDAQ:AAPL', 'NASDAQ:MSFT'], key='listing')
render_discovery_notebook(symbol)
'''


@pytest.mark.parametrize("symbol,cik", [
    ("NASDAQ:AAPL", "0000320193"),
    ("NASDAQ:MSFT", "0000789019"),
])
def test_official_filings_link_uses_verified_issuer_identity(symbol, cik):
    parsed = urlsplit(official_filings_url(symbol))
    assert parsed.hostname == "www.sec.gov"
    assert parsed.path == "/edgar/browse/"
    assert parse_qs(parsed.query) == {"CIK": [cik], "owner": ["exclude"]}


@pytest.mark.parametrize("symbol", [
    "NASDAQ:AAPL&owner=include", "NYSE:UNKNOWN", "TSX:SHOP", "",
    "AAPL", "CIK=000000AAPL",
])
def test_unverified_symbols_use_manual_sec_search_not_fake_cik(symbol):
    assert official_filings_url(symbol) == "https://www.sec.gov/search-filings"


@pytest.mark.parametrize('url', ['javascript:alert(1)', 'http://example.org',
                               'https://user:password@example.org', 'https://',
                               'https://example.org/a b', 'https://[bad'])
def test_unsafe_evidence_links_are_not_offered(url):
    assert not safe_source_url(url)


def test_comparison_never_creates_market_metrics():
    notebook = {'NASDAQ:AAPL': {'Research question': 'Cash flow durability?'}}
    assert comparison_rows(notebook, ['MISSING', 'NASDAQ:AAPL']) == [
        {'Listing': 'NASDAQ:AAPL', 'Research question': 'Cash flow durability?'}]
    assert safe_source_url('https://www.sec.gov/Archives/')


def test_notes_survive_company_switch_and_session_isolation(monkeypatch):
    import requests
    monkeypatch.setattr(requests.Session, 'request', lambda *a, **k: pytest.fail('network call'))
    app = AppTest.from_string(APP).run()
    app.button(key='qi_discovery_add').click().run()
    app.text_area(key='qi_shortlist_NASDAQ:AAPL_Research question').set_value('Check debt maturities').run()
    app.text_input(key='qi_shortlist_NASDAQ:AAPL_Source URL').set_value('https://www.sec.gov/').run()
    app.selectbox(key='listing').select('NASDAQ:MSFT').run()
    app.button(key='qi_discovery_add').click().run()
    app.selectbox(key='qi_shortlist_edit').select('NASDAQ:MSFT').run()
    assert not app.exception
    assert app.text_area(key='qi_shortlist_NASDAQ:MSFT_Research question').value == ''
    app.selectbox(key='qi_shortlist_edit').select('NASDAQ:AAPL').run()
    assert app.text_area(key='qi_shortlist_NASDAQ:AAPL_Research question').value == 'Check debt maturities'
    other = AppTest.from_string(APP).run()
    assert other.session_state['qi_discovery_notebook'] == {}
    app.button(key='qi_shortlist_clear').click().run()
    assert not app.exception
    assert app.session_state['qi_discovery_notebook'] == {}
    app.button(key='qi_discovery_add').click().run()
    assert not app.exception
    assert app.text_area(key='qi_shortlist_NASDAQ:MSFT_Research question').value == ''


def test_shortlist_quick_status_and_exact_listing_handoff():
    app = AppTest.from_string(APP).run()
    app.button(key='qi_discovery_add').click().run()
    app.selectbox(key='qi_shortlist_NASDAQ:AAPL_Status').select('Monitoring').run()
    assert app.session_state['qi_discovery_notebook']['NASDAQ:AAPL']['Status'] == 'Monitoring'
    app.button(key='qi_shortlist_open').click().run()
    assert app.session_state['_research_ticker_request'] == 'NASDAQ:AAPL'
    assert app.session_state['_navigation_request'] == '🔎 Stock Explorer'
    assert not app.exception
