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
    assert config['allow_symbol_change'] is False
    assert 'postMessage' not in markup
    assert 'fetch(' not in markup


@pytest.mark.parametrize("symbol", ['AAPL', '</script>', 'NASDAQ:AAPL<script>', 'NASDAQ:AAPL"', 'N' * 25 + ':AAPL', 'NASDAQ:' + 'A' * 65])
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
    assert any('External charts are off' in item.value for item in app.caption)


@pytest.mark.parametrize('route', [
    '🔎 Stock Explorer', '🧪 Simulation Lab', '💎 Quant Discovery', '🔍 Market Scanner',
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
    app.session_state['qi_external_charts'] = True
    app.run(timeout=45)
    assert not app.exception, [error.message for error in app.exception]
    if route == '🔎 Stock Explorer':
        assert len(app.get('iframe')) == 6
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
    assert len(app.get('iframe')) == 0
    app.toggle(key='qi_explorer_consent').set_value(True).run()
    assert not app.exception
    assert len(app.get('iframe')) == 6
    app.toggle(key='qi_external_charts').set_value(False).run()
    assert not app.exception
    assert len(app.get('iframe')) == 0
    policy_button = app.button(key="qi_open_legal_settings")
    policy_button.click().run()
    assert not app.exception
    assert app.session_state['selected_page'] == '📄 Legal & Privacy'
    assert {'Financial disclosure', 'Terms of use', 'Privacy'}.issubset(
        {tab.label for tab in app.tabs}
    )


@pytest.mark.parametrize("module,renderer", [
    ("dashboard.market_scanner_page", "render_market_scanner"),
    ("dashboard.portfolio_page", "render_portfolio_manager"),
    ("dashboard.forecast_intelligence_page", "render_forecast_intelligence"),
])
def test_direct_renderers_use_simulations(module, renderer, monkeypatch):
    monkeypatch.setenv("QI_MARKET_DATA_RIGHTS_CONFIRMED", "true")
    source = f"from {module} import {renderer}\n{renderer}()\n"
    app = AppTest.from_string(source).run(timeout=45)
    assert not app.exception
    assert any("SYNTHETIC DEMO" in item.value for item in app.info)


@pytest.mark.parametrize("route", [
    "🏠 Overview", "🔎 Stock Explorer", "🧪 Simulation Lab", "💎 Quant Discovery",
    "🔍 Market Scanner", "💼 Portfolio Manager", "🧠 Forecast Intelligence",
    "💰 Options Lab", "📊 Greeks Analysis", "📈 Scenario Explorer",
    "🧠 Strategy Research", "📚 Learn", "📄 Legal & Privacy",
])
def test_public_routes_make_no_server_http_requests(route, monkeypatch):
    import requests
    from curl_cffi import requests as curl_requests

    def fail(*args, **kwargs):
        raise AssertionError("Public page attempted server-side HTTP")

    monkeypatch.setattr(requests.Session, "request", fail)
    monkeypatch.setattr(curl_requests.Session, "request", fail)
    app = AppTest.from_file(str(Path(__file__).parents[1] / "dashboard/main.py"))
    app.session_state["selected_page"] = route
    app.run(timeout=45)
    assert not app.exception, [error.message for error in app.exception]
    assert len(app.get("iframe")) == 0


def test_top_right_preferences_are_session_local_and_resettable():
    path = Path(__file__).parents[1] / "dashboard/main.py"
    app = AppTest.from_file(str(path)).run(timeout=45)
    assert not app.exception
    assert app.session_state["qi_external_charts"] is False
    assert app.session_state["qi_display_density"] == "Comfortable"
    assert app.session_state["qi_show_research_notes"] is True
    assert app.session_state["qi_reduce_motion"] is False

    app.selectbox(key="qi_display_density").set_value("Compact").run()
    app.toggle(key="qi_show_research_notes").set_value(False).run()
    app.toggle(key="qi_reduce_motion").set_value(True).run()
    assert not app.exception
    assert app.session_state["qi_display_density"] == "Compact"
    assert app.session_state["qi_show_research_notes"] is False
    assert app.session_state["qi_reduce_motion"] is True

    app.button(key="qi_reset_workspace_preferences").click().run()
    assert not app.exception
    assert app.session_state["qi_display_density"] == "Comfortable"
    assert app.session_state["qi_show_research_notes"] is True
    assert app.session_state["qi_reduce_motion"] is False
    assert app.session_state["qi_external_charts"] is False


@pytest.mark.parametrize('view', ['Overview', 'Financials', 'Company', 'Technicals', 'News'])
def test_real_stock_detail_widget_config(view):
    from dashboard.stock_explorer_widget import DETAIL_WIDGETS, detail_embed_html
    markup = detail_embed_html('NYSE:KO', view)
    config = json.loads(re.search(r'async>\s*(\{.*?\})\s*</script>', markup, re.S)[1])
    assert config['symbol'] == 'NYSE:KO'
    assert config['colorTheme'] == 'dark'
    assert f'embed-widget-{DETAIL_WIDGETS[view][0]}.js' in markup
    assert 'tradingview-widget-copyright' in markup
    assert 'fetch(' not in markup and 'postMessage' not in markup
    with pytest.raises(ValueError):
        detail_embed_html('</script>', view)


@pytest.mark.parametrize("enabled", [False, True])
def test_restored_research_tabs_never_request_backend_data(enabled, monkeypatch):
    import requests
    from curl_cffi import requests as curl_requests

    def fail(*args, **kwargs):
        raise AssertionError("Real-stock page attempted a backend data call")

    monkeypatch.setattr(requests.Session, "request", fail)
    monkeypatch.setattr(curl_requests.Session, "request", fail)
    source = "from dashboard.stock_explorer_widget import render_stock_explorer\nrender_stock_explorer()"
    app = AppTest.from_string(source)
    app.session_state["qi_external_charts"] = enabled
    app.run()
    assert not app.exception
    assert [tab.label for tab in app.tabs] == [
        "Performance", "Risk & Scores", "News", "Historical Data", "My analysis",
    ]
    assert len(app.get("iframe")) == (6 if enabled else 0)
    assert len(app.metric) == 0
    assert not any("FICTIONAL MODEL LAB" in caption.value for caption in app.caption)
    # Preserve a download of user-authored notes, never historical prices.
    assert len(app.get("download_button")) == 1


def test_notes_survive_view_change_and_remain_per_symbol():
    source = "from dashboard.stock_explorer_widget import render_stock_explorer\nrender_stock_explorer()"
    app = AppTest.from_string(source)
    app.run()
    app.text_area[0].set_value('My own thesis').run()
    app.selectbox(key='qi_stock_lookback').set_value('5Y').run()
    app.selectbox(key='qi_stock_chart_type').set_value('Candlestick').run()
    assert app.text_area[0].value == 'My own thesis'
    app.selectbox[0].select('Microsoft · MSFT').run()
    assert app.text_area[0].value == ''
    app.selectbox[0].select('Apple · AAPL').run()
    assert app.text_area[0].value == 'My own thesis'
    assert not app.exception


@pytest.mark.parametrize("label,expected_range,expected_interval", [
    ("1D", "1D", "1"), ("1W", "5D", "15"), ("1M", "1M", "30"),
    ("3M", "3M", "60"), ("6M", "6M", "D"), ("1Y", "12M", "D"),
    ("5Y", "60M", "W"), ("All", "ALL", "M"),
])
def test_lookback_is_distinct_from_candle_interval(label, expected_range, expected_interval):
    markup = chart_embed_html("NASDAQ:AAPL", label)
    config = json.loads(re.search(r'async>\s*(\{.*?\})\s*</script>', markup, re.S)[1])
    assert config["range"] == expected_range
    assert config["interval"] == expected_interval
    assert config["withdateranges"] is False


def test_simple_labels_keep_exchange_qualified_symbols():
    assert SYMBOLS["Apple · AAPL"] == "NASDAQ:AAPL"
    assert all(":" not in label and ":" in symbol for label, symbol in SYMBOLS.items())


def test_session_opt_in_automatic_return_range_change_and_revoke():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "dashboard/main.py"))
    app.session_state["selected_page"] = "🔎 Stock Explorer"
    app.run(timeout=45)
    assert len(app.get("iframe")) == 0
    app.toggle(key="qi_explorer_consent").set_value(True).run()
    assert not app.exception
    assert len(app.get("iframe")) == 6
    assert not any(button.label == "Load real-stock chart" for button in app.button)
    app.selectbox(key="qi_stock_lookback").set_value("1D").run()
    app.selectbox[1].select("Microsoft · MSFT").run()
    assert not app.exception
    assert app.session_state["qi_stock_lookback"] == "1D"
    app.session_state["selected_page"] = "🏠 Overview"
    app.run()
    app.session_state["selected_page"] = "🔎 Stock Explorer"
    app.run()
    assert len(app.get("iframe")) == 6
    app.toggle(key="qi_external_charts").set_value(False).run()
    assert len(app.get("iframe")) == 0
    assert app.toggle(key="qi_explorer_consent").value is False
    app.toggle(key="qi_explorer_consent").set_value(True).run()
    app.button(key="qi_reset_workspace_preferences").click().run()
    assert not app.exception
    assert len(app.get("iframe")) == 0


@pytest.mark.parametrize("chart_type,style", [("Line", "2"), ("Candlestick", "1")])
def test_original_chart_types_use_official_display_styles(chart_type, style):
    markup = chart_embed_html("NASDAQ:AAPL", "1Y", chart_type)
    config = json.loads(re.search(r'async>\s*(\{.*?\})\s*</script>', markup, re.S)[1])
    assert config["style"] == style
    assert config["range"] == "12M"


@pytest.mark.parametrize("incoming,expected", [
    ("MSFT", "Microsoft · MSFT"), ("AMEX:SPY", "S&P 500 ETF · SPY"),
    ("NYSE:KO", "Other exchange-qualified symbol"),
])
def test_existing_navigation_keeps_company_requests_aligned(incoming, expected):
    app = AppTest.from_string("from dashboard.stock_explorer_widget import render_stock_explorer\nrender_stock_explorer()")
    app.session_state["_research_ticker_request"] = incoming
    app.run()
    assert not app.exception
    assert app.selectbox(key="qi_stock_company").value == expected
    if incoming == "NYSE:KO":
        assert app.text_input(key="qi_custom_stock_symbol").value == incoming


def test_unknown_navigation_symbol_never_guesses_an_exchange():
    app = AppTest.from_string("from dashboard.stock_explorer_widget import render_stock_explorer\nrender_stock_explorer()")
    app.session_state["_research_ticker_request"] = "UNKNOWN"
    app.session_state["qi_external_charts"] = True
    app.run()
    assert not app.exception
    assert len(app.get("iframe")) == 0
    assert app.warning


def test_risk_shortcut_keeps_simulations_separate_from_real_company():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "dashboard/main.py"))
    app.session_state["selected_page"] = "🔎 Stock Explorer"
    app.run(timeout=45)
    app.button(key="qi_stock_risk_lab").click().run()
    assert not app.exception
    assert app.session_state["selected_page"] == "🧪 Simulation Lab"
    assert any("SYNTHETIC DEMO" in item.value for item in app.info)
