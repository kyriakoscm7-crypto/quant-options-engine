"""Real company displays never turn into implicit model data feeds."""

import json
import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from dashboard.market_research_workspace import screener_embed_html

ROOT = Path(__file__).parents[1]


def test_screener_matches_official_stock_demo_and_preserves_attribution():
    markup = screener_embed_html()
    config = json.loads(re.search(r'async>\s*(\{.*?\})\s*</script>', markup, re.S)[1])
    assert config['market'] == 'us'
    assert config['defaultScreen'] == 'most_capitalized'
    assert config['showToolbar'] is True
    assert 'https://s3.tradingview.com/external-embedding/embed-widget-screener.js' in markup
    assert 'Stock Screener' in markup and 'by TradingView' in markup
    assert 'tradingview-widget-copyright' in markup
    assert 'fetch(' not in markup and 'postMessage' not in markup


@pytest.mark.parametrize('route,embed_count', [
    ('💎 Quant Discovery', 1), ('🔍 Market Scanner', 1), ('🧪 Simulation Lab', 2),
])
def test_real_research_routes_opt_in_without_backend_requests(route, embed_count, monkeypatch):
    import requests
    from curl_cffi import requests as curl_requests

    def fail(*args, **kwargs):
        raise AssertionError('Attempted backend request')

    monkeypatch.setattr(requests.Session, 'request', fail)
    monkeypatch.setattr(curl_requests.Session, 'request', fail)
    monkeypatch.setenv('QI_MARKET_DATA_RIGHTS_CONFIRMED', 'true')
    app = AppTest.from_file(str(ROOT / 'dashboard/main.py'))
    app.session_state['selected_page'] = route
    app.run(timeout=45)
    assert not app.exception
    assert len(app.get('iframe')) == 0
    assert not any('SYNTHETIC DEMO' in item.value for item in app.info)
    consent_key = 'qi_simulation_consent' if route == '🧪 Simulation Lab' else 'qi_discovery_consent'
    app.toggle(key=consent_key).set_value(True).run()
    assert not app.exception
    assert len(app.get('iframe')) == embed_count
    assert not any('ORION' in str(element.value) for element in app.selectbox)
    app.toggle(key='qi_external_charts').set_value(False).run()
    assert not app.exception
    assert len(app.get('iframe')) == 0
    assert app.toggle(key=consent_key).value is False


def test_discovery_company_handoff_uses_exact_listing():
    app = AppTest.from_file(str(ROOT / 'dashboard/main.py'))
    app.session_state['selected_page'] = '💎 Quant Discovery'
    app.run(timeout=45)
    app.selectbox(key='qi_discovery_company').select('Microsoft · MSFT').run()
    app.button(key='qi_discovery_open').click().run()
    assert not app.exception
    assert app.session_state['selected_page'] == '🔎 Stock Explorer'
    assert app.session_state['qi_active_stock_symbol'] == 'NASDAQ:MSFT'


def test_reference_company_does_not_relabel_or_recalibrate_model_metrics():
    app = AppTest.from_string('from dashboard.market_research_workspace import render_company_simulation_lab\nrender_company_simulation_lab()').run()
    assert not app.exception
    initial = [metric.value for metric in app.metric]
    app.selectbox(key='qi_simulation_company').select('Microsoft · MSFT').run()
    assert not app.exception
    assert [metric.value for metric in app.metric] == initial
    assert all('MSFT' not in metric.label for metric in app.metric)
    app.slider(key='lab_vol').set_value(50).run()
    assert app.metric[1].value != initial[1]
    assert any('HYPOTHETICAL MODEL' in item.value for item in app.info)


def test_invalid_custom_reference_is_never_embedded():
    app = AppTest.from_string('from dashboard.market_research_workspace import render_company_simulation_lab\nrender_company_simulation_lab()')
    app.session_state['qi_external_charts'] = True
    app.session_state['qi_external_panels_notice_version'] = 2
    app.run()
    app.selectbox(key='qi_simulation_company').select('Other exchange-qualified symbol').run()
    app.text_input(key='qi_simulation_company_custom').set_value('</script>').run()
    assert not app.exception
    assert len(app.get('iframe')) == 0
    assert app.warning
    # Models remain usable, without attributing results to a malformed company.
    assert app.slider(key='lab_vol')



def test_old_chart_only_consent_requires_new_disclosure_before_new_pages_load():
    app = AppTest.from_file(str(ROOT / 'dashboard/main.py'))
    app.session_state['selected_page'] = '💎 Quant Discovery'
    app.session_state['qi_external_charts'] = True
    # A session from before the cross-page screener disclosure has no version.
    app.run(timeout=45)
    assert not app.exception
    assert len(app.get('iframe')) == 0
    assert app.session_state['qi_external_charts'] is False
    app.toggle(key='qi_discovery_consent').set_value(True).run()
    assert len(app.get('iframe')) == 1
    assert app.session_state['qi_external_panels_notice_version'] == 2
    app.button(key='qi_reset_workspace_preferences').click().run()
    assert len(app.get('iframe')) == 0
    assert app.session_state['qi_external_panels_notice_version'] == 0


def test_settings_opt_in_records_current_scope_for_other_research_pages():
    app = AppTest.from_file(str(ROOT / 'dashboard/main.py'))
    app.session_state['selected_page'] = '💎 Quant Discovery'
    app.run(timeout=45)
    app.toggle(key='qi_external_charts').set_value(True).run()
    assert not app.exception
    assert len(app.get('iframe')) == 1
    app.session_state['selected_page'] = '🧪 Simulation Lab'
    app.run()
    assert len(app.get('iframe')) == 2
    assert not any(toggle.key == 'qi_simulation_consent' for toggle in app.toggle)
