"""Offline browser fixture using the production Stock Explorer integration."""
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import streamlit as st

from dashboard.stock_explorer_widget import render_stock_explorer

st.set_page_config(layout='wide')

st.session_state['qi_external_charts'] = False
with patch('dashboard.company_briefing.render_company_briefing'), patch('dashboard.perp_market_size.render_perp_market_size'):
    render_stock_explorer()
