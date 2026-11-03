"""Official display-only TradingView embed; never a quantitative data source."""

import html
import json
import re

import streamlit as st
import streamlit.components.v1 as components

SYMBOLS = {
    "Apple · AAPL": "NASDAQ:AAPL",
    "Microsoft · MSFT": "NASDAQ:MSFT",
    "NVIDIA · NVDA": "NASDAQ:NVDA",
    "Amazon · AMZN": "NASDAQ:AMZN",
    "Alphabet · GOOGL": "NASDAQ:GOOGL",
    "Tesla · TSLA": "NASDAQ:TSLA",
    "JPMorgan Chase · JPM": "NYSE:JPM",
}


# Range is visible history; interval is the size of each candle. Never substitute
# a daily candle interval for a one-day lookback.
LOOKBACKS = {
    "1D": ("1D", "1", "Latest trading day · 1-minute candles"),
    "1W": ("5D", "15", "Latest five trading days · 15-minute candles"),
    "1M": ("1M", "30", "Past month · 30-minute candles"),
    "3M": ("3M", "60", "Past three months · 1-hour candles"),
    "6M": ("6M", "D", "Past six months · daily candles"),
    "1Y": ("12M", "D", "Past year · daily candles"),
    "5Y": ("60M", "W", "Past five years · weekly candles"),
    "All": ("ALL", "M", "All available history · monthly candles"),
}


def chart_embed_html(symbol: str, lookback: str = "1M") -> str:
    """Build official iframe-widget markup with intact, visible attribution."""
    if not re.fullmatch(r"[A-Z0-9_]+:[A-Z0-9_.-]+", symbol):
        raise ValueError("Use an exchange-qualified stock symbol")
    date_range, interval, _ = LOOKBACKS[lookback]
    symbol_url = "https://www.tradingview.com/symbols/" + symbol.replace(":", "-") + "/"
    config = {
        "autosize": True, "symbol": symbol, "interval": interval, "range": date_range,
        "timezone": "Etc/UTC", "theme": "dark", "style": "1",
        "locale": "en", "allow_symbol_change": False,
        "hide_top_toolbar": False, "hide_legend": False,
        "withdateranges": False, "save_image": True,
        "backgroundColor": "#080D1D", "gridColor": "rgba(255,255,255,0.06)",
    }
    return f'''<!doctype html><html lang="en"><head><meta name="viewport"
content="width=device-width, initial-scale=1"><title>Stock chart by TradingView</title>
<style>html{{height:620px}}body{{height:100%;margin:0;background:#080D1D;color:#ddd}}a{{color:#91b4f4}} .tradingview-widget-copyright{{font:12px sans-serif;padding:6px 0}}</style></head><body>
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container" style="height:620px;width:100%">
<div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
<div class="tradingview-widget-copyright"><a href="{html.escape(symbol_url)}"
rel="noopener nofollow" target="_blank"><span class="blue-text">{html.escape(symbol)} chart</span></a><span class="trademark"> by TradingView</span></div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
{json.dumps(config)}
</script></div><!-- TradingView Widget END -->
</body></html>'''


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
    choice = st.selectbox("Find a company", [*SYMBOLS, "Other exchange-qualified symbol"])
    symbol = SYMBOLS.get(choice, "NASDAQ:AAPL")
    if choice == "Other exchange-qualified symbol":
        symbol = st.text_input("Exchange:symbol", "NASDAQ:AAPL", help="For example NYSE:KO or NASDAQ:META").strip().upper()
        if not re.fullmatch(r"[A-Z0-9_]+:[A-Z0-9_.-]+", symbol):
            st.warning("Enter an exchange-qualified symbol such as NASDAQ:AAPL.")
            return
    st.caption("Market information by TradingView · May be delayed or unavailable · Not investment advice")
    symbol_url = "https://www.tradingview.com/symbols/" + symbol.replace(":", "-") + "/"
    enabled = st.session_state.get("qi_external_charts", False)
    if not enabled:
        with st.container(border=True):
            st.markdown("### Your research workspace")
            st.write("Allow TradingView to load charts and company research automatically for this session.")
            st.caption("TradingView receives your IP address, selected symbol, widget type and embedding URL. Its privacy policy describes device and usage analytics, including third-party providers. Your notes are not sent to TradingView. Private sign-in does not replace your choice.")
            st.markdown("[TradingView privacy policy](https://www.tradingview.com/privacy-policy/)")
            st.session_state["qi_explorer_consent"] = False
            st.toggle("Allow automatic TradingView panels this session", key="qi_explorer_consent",
                      on_change=_apply_panel_consent)
            st.caption("External charts are off until you choose to allow them. You can also enable or disable them in Settings.")
    else:
        components.html(detail_embed_html(symbol, "Overview"), height=260, scrolling=False)
        lookback = st.radio("Price history · lookback", list(LOOKBACKS), index=2,
                            horizontal=True, key="qi_stock_lookback")
        st.caption(LOOKBACKS[lookback][2] + " · Exchange sessions and available history determine coverage.")
        components.html(chart_embed_html(symbol, lookback), height=640, scrolling=False)
        st.caption("Lookback controls the visible history; the chart toolbar controls candle size. Panning or zooming changes the visible window. Choose another lookback to reset it. Use the company selector to keep all panels aligned.")
        st.markdown("### Company research")
    view = st.radio("Research view", ["Chart", "Overview", "Financials", "Company", "Technicals", "News", "My analysis"],
                    horizontal=True, key="qi_stock_view",
                    help="The price chart stays open above. Overview opens financials and company background together.")
    if enabled and view != "My analysis":
        panels = ["Financials", "Company"] if view in ("Chart", "Overview") else [view]
        for panel in panels:
            st.markdown(f"#### {panel}")
            components.html(detail_embed_html(symbol, panel), height=DETAIL_WIDGETS[panel][1] + 10, scrolling=False)
        if view == "Technicals":
            st.caption("TradingView's technical ratings summarize indicators, not a Quant Intelligence recommendation.")
        st.caption("Panel unavailable? Coverage depends on the symbol, provider and browser. Open TradingView below; missing data is never replaced with fictional values.")
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
    st.link_button("Open this stock on TradingView ↗", symbol_url)


def _apply_panel_consent() -> None:
    """Apply the disclosed visitor choice before Settings is rebuilt."""
    st.session_state["qi_external_charts"] = st.session_state["qi_explorer_consent"]
