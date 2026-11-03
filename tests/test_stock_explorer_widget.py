"""Display embeds cannot become an implicit market-data feed."""

import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.stock_explorer_widget import SYMBOLS, chart_embed_html


@pytest.mark.parametrize("symbol", SYMBOLS.values())
def test_official_embed_preserves_attribution_and_configuration(symbol):
    markup = chart_embed_html(symbol)
    assert 'src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js"' in markup
    assert 'tradingview-widget-copyright' in markup
    assert 'by TradingView' in markup
    assert 'height:calc(100% - 32px)' in markup
    assert 'html{height:620px}' in markup
    config = json.loads(re.search(r'async>\s*(\{.*?\})\s*</script>', markup, re.S)[1])
    assert config['symbol'] == symbol
    assert config['theme'] == 'dark'
    assert config['allow_symbol_change'] is True
    assert 'postMessage' not in markup
    assert 'fetch(' not in markup


@pytest.mark.parametrize("symbol", ['AAPL', '</script>', 'NASDAQ:AAPL<script>', 'NASDAQ:AAPL"'])
def test_symbol_injection_rejected(symbol):
    with pytest.raises(ValueError):
        chart_embed_html(symbol)


def test_external_chart_control_removes_embed():
    source = '''import streamlit as st
from dashboard.stock_explorer_widget import render_stock_explorer
st.session_state['qi_external_charts'] = False
render_stock_explorer()
'''
    app = AppTest.from_string(source).run()
    assert not app.exception
    assert len(app.get('iframe')) == 0
    assert any('External charts are off' in item.value for item in app.info)


@pytest.mark.parametrize('route', [
    '🔎 Stock Explorer', '💎 Quant Discovery', '🔍 Market Scanner',
    '💼 Portfolio Manager', '🧠 Forecast Intelligence', '📄 Legal & Privacy',
])
def test_main_public_routes_cannot_reenable_legacy_feeds(route, monkeypatch):
    monkeypatch.setenv('QI_MARKET_DATA_RIGHTS_CONFIRMED', 'true')
    def fail(*args, **kwargs):
        raise AssertionError('Public UI attempted a backend market-data request')
    import app.market_data.stock_history as history
    import app.market_data.yahoo_client as yahoo
    monkeypatch.setattr(history, 'fetch_stock_history', fail)
    monkeypatch.setattr(yahoo, 'fetch_option_chain', fail)
    app = AppTest.from_file(str(Path(__file__).parents[1] / 'dashboard/main.py'))
    app.session_state['selected_page'] = route
    app.run(timeout=45)
    assert not app.exception, [error.message for error in app.exception]
    if route == '🔎 Stock Explorer':
        assert len(app.get('iframe')) == 1
        assert not any('SYNTHETIC DEMO' in item.value for item in app.info)
    elif route != '📄 Legal & Privacy':
        assert any('SYNTHETIC DEMO' in item.value for item in app.info)


def test_direct_discovery_remains_simulated_even_with_legacy_flag(monkeypatch):
    monkeypatch.setenv('QI_MARKET_DATA_RIGHTS_CONFIRMED', 'true')
    path = Path(__file__).parents[1] / 'dashboard/pages/2_Quant_Discovery.py'
    app = AppTest.from_file(str(path)).run(timeout=45)
    assert not app.exception
    assert any('SYNTHETIC DEMO' in item.value for item in app.info)


def test_compact_menu_opens_policies_and_can_disable_charts():
    path = Path(__file__).parents[1] / 'dashboard/main.py'
    app = AppTest.from_file(str(path))
    app.session_state['selected_page'] = '🔎 Stock Explorer'
    app.run(timeout=45)
    app.toggle(key='qi_external_charts').set_value(False).run()
    assert not app.exception
    assert len(app.get('iframe')) == 0
    policy_button = next(button for button in app.button
                         if button.label == 'Disclosures, Terms, Privacy & About')
    policy_button.click().run()
    assert not app.exception
    assert app.session_state['selected_page'] == '📄 Legal & Privacy'
    assert {tab.label for tab in app.tabs} == {'Financial disclosure', 'Terms of use', 'Privacy'}
