"""Real-company provider displays and independent, assumption-driven experiments.

No provider data is fetched by Python, extracted from widgets or passed to models.
"""

import json
import re

import streamlit as st
import streamlit.components.v1 as components

from dashboard.discovery_notebook import official_filings_url, render_discovery_notebook
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
    st.title(":primary[:material/diamond:] Opportunity Discovery")
    st.caption("SCAN → INVESTIGATE → REVIEW · REAL COMPANIES · YOUR RESEARCH")
    mode = st.radio("Research stage", ["Scan", "Investigate"], horizontal=True,
                    index=0, key="qi_discovery_stage")
    if mode == "Scan":
        st.write("Find candidates with the provider's filters and sorting, then enter an exact listing below to investigate. Provider selections stay inside its panel.")
        if render_external_panel_consent("qi_discovery_consent"):
            components.html(screener_embed_html(), height=760, scrolling=False)
        st.caption("TradingView supplies the screening and ratings inside its official display. These are not Quant Intelligence recommendations or validated forecasts. Data can be delayed or unavailable; the app cannot read or export results.")
        st.link_button("Open full stock screener on TradingView ↗", "https://www.tradingview.com/screener/")
    else:
        st.write("Build an evidence trail: identify a listing, read primary reports, challenge your question and set a review trigger.")
    symbol = _select_company("qi_discovery_company")
    if symbol:
        a, b = st.columns(2)
        a.button("Open Stock Explorer", type="primary", key="qi_discovery_open",
                 on_click=_open_company, args=(symbol,))
        b.link_button("Find issuer filings · SEC EDGAR ↗", official_filings_url(symbol))
        st.caption("Verify the issuer match in EDGAR. For listings without SEC coverage, use the issuer's official investor-relations site.")
    render_discovery_notebook(symbol)


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
