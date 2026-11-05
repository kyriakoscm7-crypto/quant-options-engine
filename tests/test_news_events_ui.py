"""Render the report without any external network access."""
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from app.intelligence.company_directory_service import CompanyDirectoryService
from app.intelligence.news_events import NewsEventsService, Provider


def test_search_and_render_unified_report():
    directory = CompanyDirectoryService(fetcher=lambda: {'0': {
        'ticker': 'AAPL', 'title': 'Apple Inc.', 'cik_str': 320193}})
    service = NewsEventsService([Provider('test', lambda *a, **k: [{
        'title': 'Apple Inc. results', 'url': 'https://publisher.test/story',
        'published': (datetime.now(UTC) - timedelta(minutes=1)).isoformat()}], True, 'reviewed contract')],
        filings_loader=lambda c: {'filings': {'recent': {}}})
    with patch('dashboard.news_events_panel._services', return_value=(directory, service)):
        app = AppTest.from_string('from dashboard.news_events_panel import render_news_events\nrender_news_events()').run()
        app.toggle[0].set_value(True).run()
        app.text_input[0].input('Apple').run()
        app.button[0].click().run()
        assert not app.exception
        assert app.metric[0].value == '1'
        assert len(app.tabs) == 3
        app.text_input[0].input('NVDA').run()
        assert not app.metric
