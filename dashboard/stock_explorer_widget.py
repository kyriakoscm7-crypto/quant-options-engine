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
    "Meta · META": "NASDAQ:META",
    "Berkshire Hathaway · BRK.B": "NYSE:BRK.B",
    "S&P 500 ETF · SPY": "AMEX:SPY",
    "Vanguard S&P 500 ETF · VOO": "AMEX:VOO",
    "Nasdaq 100 ETF · QQQ": "NASDAQ:QQQ",
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


def chart_embed_html(symbol: str, lookback: str = "1M", chart_type: str = "Candlestick") -> str:
    """Build official iframe-widget markup with intact, visible attribution."""
    if not re.fullmatch(r"[A-Z0-9_]{1,24}:[A-Z0-9_.-]{1,64}", symbol):
        raise ValueError("Use an exchange-qualified stock symbol")
    date_range, interval, _ = LOOKBACKS[lookback]
    style = {"Line": "2", "Candlestick": "1"}[chart_type]
    symbol_url = "https://www.tradingview.com/symbols/" + symbol.replace(":", "-") + "/"
    config = {
        "autosize": True, "symbol": symbol, "interval": interval, "range": date_range,
        "timezone": "Etc/UTC", "theme": "dark", "style": style,
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
    if not re.fullmatch(r"[A-Z0-9_]{1,24}:[A-Z0-9_.-]{1,64}", symbol):
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


def _render_notes(symbol: str) -> None:
    st.markdown(f"### Your research · {symbol.split(':', 1)[1]}")
    st.caption("Your observations are processed by the server and saved for this session only. Download to keep them. Use public-company research only; do not enter account details, real holdings or personal financial information.")
    notes = {}
    for title in ["Thesis & valuation", "Evidence & source links", "Risks & what would change my mind"]:
        key = f"qi_notes_{symbol}_{title}"
        saved = st.session_state.get("qi_research_notes", {}).get(symbol, {}).get(title, "")
        notes[title] = st.text_area(title, value=saved, key=key, height=140, max_chars=10000,
                                    on_change=_save_research_note, args=(symbol, title, key))
    export = "# " + symbol + "\n\n" + "\n\n".join(f"## {title}\n{value}" for title, value in notes.items())
    st.download_button("Download my research", export, symbol.replace(":", "-") + "-research.md", "text/markdown")


def _render_panel(symbol: str, view: str, enabled: bool) -> None:
    if enabled:
        components.html(detail_embed_html(symbol, view), height=DETAIL_WIDGETS[view][1] + 10, scrolling=False)
    else:
        st.caption("Allow TradingView panels above or in Settings to view this company research.")


def _open_simulation_lab() -> None:
    st.session_state["_navigation_request"] = "🧪 Simulation Lab"


def render_stock_explorer() -> None:
    st.title(":primary[:material/search:] Stock Explorer")
    st.caption("Research stock and ETF price history, company fundamentals and market context.")
    # Preserve requests from existing navigation without guessing an exchange.
    incoming = st.session_state.pop("_research_ticker_request", None)
    if incoming:
        incoming = str(incoming).strip().upper()
        match = next((label for label, value in SYMBOLS.items()
                      if incoming in (value, value.split(":", 1)[1])), None)
        st.session_state["qi_stock_company"] = match or "Other exchange-qualified symbol"
        if not match:
            st.session_state["qi_custom_stock_symbol"] = incoming
    company_col, period_col, chart_col = st.columns([2, 1, 1])
    with company_col:
        choice = st.selectbox("Find a company", [*SYMBOLS, "Other exchange-qualified symbol"],
                              key="qi_stock_company")
    with period_col:
        lookback = st.selectbox("Historical period", list(LOOKBACKS), index=5, key="qi_stock_lookback")
    with chart_col:
        chart_type = st.selectbox("Chart type", ["Line", "Candlestick"], key="qi_stock_chart_type")
    symbol = SYMBOLS.get(choice, "NASDAQ:AAPL")
    if choice == "Other exchange-qualified symbol":
        symbol = st.text_input("Exchange:symbol", "NASDAQ:AAPL", key="qi_custom_stock_symbol", max_chars=89,
                               help="Use the exact exchange listing, for example NYSE:KO or TSX:SHOP. We never guess the exchange.").strip().upper()
        if not re.fullmatch(r"[A-Z0-9_]{1,24}:[A-Z0-9_.-]{1,64}", symbol):
            st.warning("Enter an exchange-qualified symbol such as NASDAQ:AAPL.")
            return
    st.caption("Market information by TradingView · May be delayed or unavailable · Not investment advice")
    symbol_url = "https://www.tradingview.com/symbols/" + symbol.replace(":", "-") + "/"
    enabled = st.session_state.get("qi_external_charts", False)
    if not enabled:
        with st.container(border=True):
            st.markdown("### Your research workspace")
            st.write("Allow TradingView to load the chart and company research automatically for this session, including panels in the tabs below.")
            st.caption("TradingView receives your IP address, selected symbol, widget type and embedding URL. Its privacy policy describes device and usage analytics, including third-party providers. Your notes are not sent to TradingView. Private sign-in does not replace your choice.")
            st.markdown("[TradingView privacy policy](https://www.tradingview.com/privacy-policy/)")
            st.session_state["qi_explorer_consent"] = False
            st.toggle("Allow automatic TradingView panels this session", key="qi_explorer_consent",
                      on_change=_apply_panel_consent)
            st.caption("External charts are off until you choose to allow them. Disable them or reset preferences in Settings at any time.")
    else:
        _render_panel(symbol, "Overview", enabled)
        st.caption(LOOKBACKS[lookback][2] + " requested · Provider sessions, resolution and available history determine coverage.")
        components.html(chart_embed_html(symbol, lookback, chart_type), height=640, scrolling=False)
        st.caption("Historical period selects the lookback; the chart toolbar selects candle size. Panning or zooming changes the visible window. Use the company selector to keep all panels aligned.")
    performance, risk, news, history, analysis = st.tabs(
        ["Performance", "Risk & Scores", "News", "Historical Data", "My analysis"]
    )
    with performance:
        st.subheader("Company overview & financials")
        st.caption("Use Compare in the main chart toolbar to compare another instrument, such as SPY, where supported. Any comparison and scale are controlled by TradingView; no app-calculated relative-return cards are shown.")
        _render_panel(symbol, "Financials", enabled)
        _render_panel(symbol, "Company", enabled)
    with risk:
        st.subheader("Technical assessment")
        _render_panel(symbol, "Technicals", enabled)
        st.caption("TradingView's ratings summarize technical indicators. They are not Quant Intelligence scores, probabilities of profit or a personalized recommendation.")
        st.markdown("#### Historical risk intelligence")
        st.write("Company-specific volatility, drawdown, beta and custom scores need a separately authorized price-history feed. The display panels do not supply data to our quantitative engines.")
        st.button("Explore risk formulas in Simulation Lab", on_click=_open_simulation_lab,
                  key="qi_stock_risk_lab")
    with news:
        st.subheader("Company news")
        _render_panel(symbol, "News", enabled)
        st.caption("Headlines and linked articles are provided by TradingView. Coverage varies; no app-generated or copied company news is substituted.")
    with history:
        st.subheader("Historical Market Data")
        st.write("Explore available price history in the chart above. The current integration is display-only, so raw price tables and historical CSV downloads are unavailable here.")
        st.caption("Restoring the original data table, adjusted-history calculations and exports requires a separately verified data agreement. A TradingView subscription or private login does not supply those permissions.")
        st.link_button("View this company's provider page ↗", symbol_url)
    with analysis:
        _render_notes(symbol)
    if enabled:
        st.caption("Missing panel? Availability depends on the symbol, provider and browser. Missing data is never replaced with fictional values.")
    st.link_button("Open this stock on TradingView ↗", symbol_url)


def _apply_panel_consent() -> None:
    """Apply the disclosed visitor choice before Settings is rebuilt."""
    st.session_state["qi_external_charts"] = st.session_state["qi_explorer_consent"]
