"""Isolated offline visual QA fixture. Not part of the app navigation."""
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import streamlit as st

from app.intelligence.company_directory_service import CompanyDirectoryService
from app.intelligence.news_events import NewsEventsService, Provider
from app.intelligence.news_reliability import NewsRateLimited, NewsReliability
from dashboard.news_events_panel import render_news_events

st.set_page_config(page_title='Offline News QA', layout='wide')
st.markdown(f'<style>{(Path(__file__).parents[1] / "dashboard/premium_theme.css").read_text()}</style>', unsafe_allow_html=True)
st.caption('ILLUSTRATIVE OFFLINE QA · No live headlines or external requests')
scenario = st.selectbox('QA source scenario', ['Available', 'Stale', 'Unavailable', 'Empty', 'Disabled'])
directory = CompanyDirectoryService(fetcher=lambda: {
    '0': {'ticker': 'AAPL', 'title': 'Apple Inc.', 'cik_str': 320193},
    '1': {'ticker': 'MSFT', 'title': 'MICROSOFT CORP', 'cik_str': 789019}})
clock = [0]
cache = NewsReliability(fresh_seconds=10, stale_seconds=100, clock=lambda: clock[0])
now = datetime.now(UTC)
rows = [{'title': 'Illustrative QA: Apple Inc. files a company update', 'url': 'https://publisher.test/qa',
         'published': (now - timedelta(hours=2)).isoformat(), 'timestamp_kind': 'first_seen'}]
def loader(*args, **kwargs):
    if scenario in ('Stale', 'Unavailable'):
        raise NewsRateLimited('QA 429', 600)
    return [] if scenario == 'Empty' else rows

def filings(company):
    if scenario in ('Stale', 'Unavailable'):
        raise ConnectionError('QA SEC outage')
    return {'filings': {'recent': {'accessionNumber': ['0000320193-26-000001'],
        'filingDate': [now.date().isoformat()], 'form': ['8-K'], 'primaryDocument': ['qa.htm']}}}

if scenario == 'Stale':
    cache.fetch('QA fixture', '0000320193|Apple Inc.|7|75|offline fixture', lambda: rows)
    cache.fetch('SEC', '0000320193', lambda: [{'filings': {'recent': {}}}])
    clock[0] = 20
service = NewsEventsService([Provider('QA fixture', loader, scenario != 'Disabled', 'offline fixture')], filings, cache)
with patch('dashboard.news_events_panel._services', return_value=(directory, service)):
    render_news_events()
