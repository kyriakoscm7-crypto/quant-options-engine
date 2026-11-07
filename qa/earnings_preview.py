"""Synthetic earnings browser fixture; never used by production routing."""
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st

from app.intelligence.earnings_api_provider import EarningsEvent, WeekResult
from dashboard.earnings_week import render_earnings_week

st.caption('SYNTHETIC QA — no provider requests')
if st.session_state.get('_research_ticker_request'):
    st.write('Research selection: ' + st.session_state['_research_ticker_request'])
else:
    featured = st.query_params.get('no_featured') != '1'
    events = tuple(EarningsEvent((['NVDA', 'AAPL', 'MSFT', 'AMZN', 'META', 'TSLA', 'JPM', 'WMT', 'COST', 'AMD', 'DIS', 'UBER'][i - 1258] if featured and i >= 1258 else f'T{i:04}'), 'Synthetic Nvidia' if featured and i == 1258 else f'Synthetic Company {i}', date(2026, 11, 9 + i % 5), 'Before market' if i % 2 else 'After market') for i in range(1270))
    result = WeekResult(events=events, retrieved_at=1794229200)
    with patch('app.intelligence.earnings_api_provider.reporting_week', return_value=date(2026, 11, 9)), patch('dashboard.earnings_week._earnings_api_key', return_value='synthetic'), patch('app.intelligence.earnings_api_provider.earnings_api_service.load_week', return_value=result):
        render_earnings_week()
