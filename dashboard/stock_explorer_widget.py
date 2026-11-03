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
<style>html{{height:620px}}body{{height:100%;margin:0;background:#080D1D;color:#ddd}}a{{color:#FF78B7}}
.tradingview-widget-copyright{{font:14px sans-serif;padding:8px 0}}</style></head><body>
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container" style="height:620px;width:100%">
<div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
<div class="tradingview-widget-copyright"><a href="{html.escape(symbol_url)}"
rel="noopener nofollow" target="_blank"><span class="blue-text">{html.escape(symbol)} chart</span></a><span class="trademark"> by TradingView</span></div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
{json.dumps(config)}
</script></div><!-- TradingView Widget END -->
</body></html>'''


def render_stock_explorer() -> None:
    st.title(":primary[:material/search:] Stock Explorer")
    st.caption("REAL STOCKS / TradingView charts · Independent quantitative research workspace")
    choice = st.selectbox("Company / exchange", list(SYMBOLS))
    symbol = SYMBOLS[choice]
    st.caption(
        "Charts by TradingView · Quotes may be delayed; availability varies by exchange. "
        "Use the chart's symbol search for more stocks. Not investment advice."
    )
    st.caption(
        "Loading the external chart shares connection information, displayed symbol and "
        "embedding URL with TradingView. Control loading in Legal / Settings / About."
    )
    if st.session_state.get("qi_external_charts", True):
        components.html(chart_embed_html(symbol), height=640, scrolling=False)
        st.caption("Chart unavailable? The provider may restrict this symbol, or your browser may block external scripts.")
    else:
        st.info("External charts are off. Enable them in Legal / Settings / About to display real stocks.")
    st.link_button("Open chart on TradingView ↗", "https://www.tradingview.com/symbols/" + symbol.replace(":", "-") + "/")
    with st.expander("Experimental analytics / simulation lab"):
        st.markdown(
            "Custom scores, forecasts and risk metrics are **not computed from this chart**. "
            "A separate provider with explicit public-display and derived-data rights is "
            "required before real-stock model outputs can be enabled."
        )
        if st.button("Open fictional-data analytics lab"):
            st.session_state["_navigation_request"] = "🧠 Forecast Intelligence"
            st.rerun()
