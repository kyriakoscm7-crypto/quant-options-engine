"""Real-company provider displays and independent, assumption-driven experiments.

No provider data is fetched by Python, extracted from widgets or passed to models.
"""

import json
import re

import streamlit as st
import streamlit.components.v1 as components

from dashboard.stock_explorer_widget import (
    SYMBOLS,
    chart_embed_html,
    detail_embed_html,
    render_external_panel_consent,
)


def screener_embed_html() -> str:
    """Official stock-demo configuration, with visible provider attribution."""
    config = {
        "width": "100%", "height": 720, "defaultColumn": "overview",
        "defaultScreen": "most_capitalized", "showToolbar": True,
        "locale": "en", "market": "us", "colorTheme": "dark",
    }
    return f'''<!doctype html><html lang="en"><head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Stock Screener by TradingView</title>
<style>body{{margin:0;background:#080D1D;color:#ddd}}a{{color:#91b4f4}}</style>
</head><body><div class="tradingview-widget-container">
<div class="tradingview-widget-container__widget"></div>
<div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/screener/"
rel="noopener nofollow" target="_blank"><span class="blue-text">Stock Screener</span></a><span class="trademark"> by TradingView</span></div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-screener.js" async>
{json.dumps(config)}
</script></div></body></html>'''


def _select_company(key: str) -> str | None:
    choice = st.selectbox("Company to research", [*SYMBOLS, "Other exchange-qualified symbol"], key=key)
    if choice in SYMBOLS:
        return SYMBOLS[choice]
    symbol = st.text_input("Exchange:symbol", "NASDAQ:AAPL", max_chars=89,
                           key=f"{key}_custom").strip().upper()
    if not re.fullmatch(r"[A-Z0-9_]{1,24}:[A-Z0-9_.-]{1,64}", symbol):
        st.warning("Enter an exact listing such as NASDAQ:AAPL or TSX:SHOP.")
        return None
    return symbol


def _open_company(symbol: str) -> None:
    st.session_state["_research_ticker_request"] = symbol
    st.session_state["_navigation_request"] = "🔎 Stock Explorer"


def render_market_discovery(*, scanner: bool = False) -> None:
    st.title(":primary[:material/radar:] Market Scanner" if scanner else ":primary[:material/diamond:] Quant Discovery")
    st.caption("REAL COMPANIES · PROVIDER-HOSTED SCREENING · INDEPENDENT RESEARCH")
    st.write("Explore actual stocks by valuation, performance and technical characteristics using TradingView's screener. Change its filters, columns and sorting to investigate your own questions.")
    if render_external_panel_consent("qi_discovery_consent"):
        components.html(screener_embed_html(), height=760, scrolling=False)
    st.caption("Screening and any ratings are provided by TradingView, not a Quant Intelligence ranking, validated forecast or recommendation. Data may be delayed, missing or unavailable. The app does not read or export the screener's results.")
    st.markdown("### Investigate a company")
    symbol = _select_company("qi_discovery_company")
    if symbol:
        st.button("Open company research", type="primary", key="qi_discovery_open",
                  on_click=_open_company, args=(symbol,))
    st.caption("Choose the exact company above to open its chart, financials and news. Selections inside the provider screener do not synchronize with this selector.")
    st.link_button("Open full stock screener on TradingView ↗", "https://www.tradingview.com/screener/")


def render_company_simulation_lab() -> None:
    st.title(":primary[:material/science:] Quant Simulation Lab")
    st.caption("REAL-COMPANY REFERENCE · YOUR ASSUMPTIONS · TRANSPARENT MODELS")
    incoming = st.session_state.pop("_qi_sim_reference_request", None)
    if incoming:
        match = next((label for label, listing in SYMBOLS.items() if listing == incoming), None)
        st.session_state["qi_simulation_company"] = match or "Other exchange-qualified symbol"
        if not match:
            st.session_state["qi_simulation_company_custom"] = incoming
    symbol = _select_company("qi_simulation_company")
    enabled = render_external_panel_consent("qi_simulation_consent")
    if symbol:
        st.markdown("### Market reference")
        st.caption("The selected company's observed prices stay in TradingView's display. They do not populate the experiment below.")
        if enabled:
            components.html(detail_embed_html(symbol, "Overview"), height=260, scrolling=False)
            components.html(chart_embed_html(symbol, "1Y", "Line"), height=640, scrolling=False)
        st.button("Open full company research", key="qi_simulation_open",
                  on_click=_open_company, args=(symbol,))
    st.divider()
    st.info("HYPOTHETICAL MODEL — Set your own growth, volatility and correlation assumptions. Paths are generated mathematical scenarios, not this company's observed history, calibrated forecast or probability of investment success.")
    from dashboard.stock_research_lab import render_research_lab

    render_research_lab()
