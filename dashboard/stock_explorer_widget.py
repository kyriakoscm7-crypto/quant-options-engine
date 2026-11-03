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


DETAIL_WIDGETS = {
    "Overview": ("symbol-info", 250),
    "Financials": ("financials", 620),
    "Company": ("symbol-profile", 520),
    "Technicals": ("technical-analysis", 510),
    "News": ("timeline", 620),
}


def detail_embed_html(symbol: str, view: str) -> str:
    """Official provider widgets; never fetch or inspect their returned data."""
    if not re.fullmatch(r"[A-Z0-9_]+:[A-Z0-9_.-]+", symbol):
        raise ValueError("Use an exchange-qualified stock symbol")
    widget, height = DETAIL_WIDGETS[view]
    config = {"symbol": symbol, "width": "100%", "height": height - 32,
              "colorTheme": "dark", "isTransparent": True, "locale": "en"}
    if view == "Technicals":
        config.update(interval="1D", showIntervalTabs=True, displayMode="single")
    elif view == "Financials":
        config.update(displayMode="adaptive", largeChartUrl="")
    elif view == "News":
        config.update(feedMode="symbol", displayMode="regular")
    return f'''<!doctype html><html lang="en"><head><meta name="viewport"
content="width=device-width, initial-scale=1"><title>{html.escape(view)} by TradingView</title>
<style>body{{margin:0;background:#080D1D;color:white}}a{{color:#91b4f4}}</style></head><body>
<div class="tradingview-widget-container">
<div class="tradingview-widget-container__widget"></div>
<div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/"
rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-{widget}.js" async>
{json.dumps(config)}
</script></div></body></html>'''


def _save_research_note(symbol: str, title: str, key: str) -> None:
    st.session_state.setdefault("qi_research_notes", {}).setdefault(symbol, {})[title] = st.session_state[key]


def render_stock_explorer() -> None:
    st.title(":primary[:material/search:] Stock Explorer")
    st.caption("REAL COMPANIES · CHARTS / FINANCIALS / TECHNICALS / NEWS")
    choice = st.selectbox("Company / exchange", [*SYMBOLS, "Other exchange-qualified symbol"])
    symbol = SYMBOLS.get(choice, "NASDAQ:AAPL")
    if choice == "Other exchange-qualified symbol":
        symbol = st.text_input("Exchange:symbol", "NASDAQ:AAPL", help="For example NYSE:KO or NASDAQ:META").strip().upper()
        if not re.fullmatch(r"[A-Z0-9_]+:[A-Z0-9_.-]+", symbol):
            st.warning("Enter an exchange-qualified symbol such as NASDAQ:AAPL.")
            return
    st.caption("Market information by TradingView · May be delayed or unavailable · Not investment advice")
    view = st.radio("Research view", ["Chart", "Overview", "Financials", "Company", "Technicals", "News", "My analysis"],
                    horizontal=True, key="qi_stock_view")
    symbol_url = "https://www.tradingview.com/symbols/" + symbol.replace(":", "-") + "/"
    if view == "My analysis":
        st.markdown(f"### Your research · {symbol}")
        st.caption("Your own observations, saved for this session only. Download to keep them. No automated company scores.")
        notes = {}
        for title in ["Thesis & valuation", "Evidence & source links", "Risks & what would change my mind"]:
            key = f"qi_notes_{symbol}_{title}"
            saved = st.session_state.get("qi_research_notes", {}).get(symbol, {}).get(title, "")
            notes[title] = st.text_area(title, value=saved, key=key, height=140,
                                        on_change=_save_research_note, args=(symbol, title, key))
        export = "# " + symbol + "\n\n" + "\n\n".join(f"## {title}\n{value}" for title, value in notes.items())
        st.download_button("Download my research", export, symbol.replace(":", "-") + "-research.md", "text/markdown")
    elif st.session_state.get("qi_external_charts", False):
        if view == "Chart":
            components.html(chart_embed_html(symbol), height=640, scrolling=False)
            st.caption("Use Indicators for technical studies and the chart toolbar for comparisons where available. Chart-only symbol changes do not update the other views; use the company selector above to keep them aligned.")
        else:
            components.html(detail_embed_html(symbol, view), height=DETAIL_WIDGETS[view][1] + 10, scrolling=False)
            if view == "Technicals":
                st.caption("Provider-generated technical ratings summarize indicators, not your own conclusion. Change the interval inside the panel.")
        st.caption("Missing data or a blocked panel? Availability depends on the symbol, provider and browser. Use the TradingView link below; no fictional substitute is shown.")
    else:
        with st.container(border=True):
            st.markdown("### Research actual stocks")
            st.write("Explore price history, company financials, technical indicators and related news through TradingView's hosted panels.")
            st.caption("Loading shares your IP, symbol and embedding URL with TradingView. Control all panels in Settings.")
            st.button("Load real-stock chart", type="primary", on_click=_enable_external_charts,
                      key="qi_load_stock_chart")
            st.caption("External charts are off until you choose to load them.")
    st.link_button("Open this stock on TradingView ↗", symbol_url)
