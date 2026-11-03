"""Official display-only TradingView embed; never a quantitative data source."""

import html
import json
import re

import streamlit as st
import streamlit.components.v1 as components

SYMBOLS = {
    "Apple · NASDAQ:AAPL": "NASDAQ:AAPL",
    "Microsoft · NASDAQ:MSFT": "NASDAQ:MSFT",
    "NVIDIA · NASDAQ:NVDA": "NASDAQ:NVDA",
    "Amazon · NASDAQ:AMZN": "NASDAQ:AMZN",
    "Alphabet · NASDAQ:GOOGL": "NASDAQ:GOOGL",
    "Tesla · NASDAQ:TSLA": "NASDAQ:TSLA",
    "JPMorgan Chase · NYSE:JPM": "NYSE:JPM",
}


def chart_embed_html(symbol: str) -> str:
    """Build official iframe-widget markup with intact, visible attribution."""
    if not re.fullmatch(r"[A-Z0-9_]+:[A-Z0-9_.-]+", symbol):
        raise ValueError("Use an exchange-qualified stock symbol")
    symbol_url = "https://www.tradingview.com/symbols/" + symbol.replace(":", "-") + "/"
    config = {
        "autosize": True, "symbol": symbol, "interval": "D",
        "timezone": "Etc/UTC", "theme": "dark", "style": "1",
        "locale": "en", "allow_symbol_change": True,
        "hide_top_toolbar": False, "hide_legend": False,
        "withdateranges": True, "save_image": True,
        "backgroundColor": "#080D1D", "gridColor": "rgba(255,255,255,0.06)",
    }
    return f'''<!doctype html><html lang="en"><head><meta name="viewport"
content="width=device-width, initial-scale=1"><title>Stock chart by TradingView</title>
<style>html{{height:620px}}body{{height:100%;margin:0;background:#080D1D;color:#ddd}}</style></head><body>
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container" style="height:620px;width:100%">
<div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
<div class="tradingview-widget-copyright"><a href="{html.escape(symbol_url)}"
rel="noopener nofollow" target="_blank"><span class="blue-text">{html.escape(symbol)} chart</span></a><span class="trademark"> by TradingView</span></div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
{json.dumps(config)}
</script></div><!-- TradingView Widget END -->
</body></html>'''


def _enable_external_charts() -> None:
    """Widget callback runs before the sidebar is rebuilt on the next rerun."""
    st.session_state["qi_external_charts"] = True


def render_stock_explorer() -> None:
    st.title(":primary[:material/search:] Stock Explorer")
    st.caption("MARKET VIEW + QUANTITATIVE WORKBENCH")
    choice = st.selectbox("Company / exchange", list(SYMBOLS))
    symbol = SYMBOLS[choice]
    st.caption("TradingView display only · Quotes may be delayed · Models below use fictional inputs · Not investment advice")
    if st.session_state.get("qi_external_charts", False):
        components.html(chart_embed_html(symbol), height=640, scrolling=False)
    else:
        with st.container(border=True):
            st.markdown("### Your market window")
            st.write("Explore real-stock candles, volume and technical indicators with TradingView.")
            st.caption("Loading shares your IP, symbol and embedding URL with TradingView. Control this in Settings.")
            st.button("Load real-stock chart", type="primary", on_click=_enable_external_charts,
                      key="qi_load_stock_chart")
            st.caption("External charts are off until you choose to load them.")
    st.link_button("Open chart on TradingView ↗", "https://www.tradingview.com/symbols/" + symbol.replace(":", "-") + "/")
    from dashboard.stock_research_lab import render_research_lab
    render_research_lab()
