"""Official display-only TradingView embed; never a quantitative data source."""

import html
import json
import re

import streamlit as st
import streamlit.components.v1 as components

from dashboard.workspace_settings import (
    initialize_workspace_preferences,
    record_external_panel_choice,
)

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
<style>html{{height:620px}}body{{height:100%;margin:0;background:#080D1D;color:#ddd}}</style></head><body>
<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container" style="height:620px;width:100%">
<div class="tradingview-widget-container__widget" style="height:calc(100% - 32px);width:100%"></div>
<div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/"
rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
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
<style>body{{margin:0;background:#080D1D;color:white}}</style></head><body>
<div class="tradingview-widget-container">
<div class="tradingview-widget-container__widget"></div>
<div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/"
rel="noopener nofollow" target="_blank"><span class="blue-text">Track all markets on TradingView</span></a></div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-{widget}.js" async>
{json.dumps(config)}
</script></div></body></html>'''


def _render_notes(symbol: str) -> None:
    from dashboard.discovery_notebook import _add, render_record_editor
    st.markdown(f"### Shared research · {symbol}")
    st.caption("Session only. Public-company observations and fictional inputs only; no account records or sensitive personal financial information.")
    _add(symbol)
    if symbol in st.session_state.get("qi_discovery_notebook", {}):
        render_record_editor(symbol)
    else:
        st.warning("50-record limit reached. Delete a record in Discovery to free a slot. Archives still count.")


def _render_panel(symbol: str, view: str, enabled: bool) -> None:
    if enabled:
        components.html(detail_embed_html(symbol, view), height=DETAIL_WIDGETS[view][1] + 10, scrolling=False)
    else:
        st.caption("Allow TradingView panels above or in Settings to view this company research.")


def _open_options_lab(symbol: str) -> None:
    st.session_state["qi_model_reference"] = symbol
    st.session_state["_navigation_request"] = "💰 Options Lab"


def render_external_panel_consent(key: str = "qi_explorer_consent") -> bool:
    """One disclosed choice per session, shared by all official panel pages."""
    initialize_workspace_preferences()
    if st.session_state.get("qi_external_charts", False):
        return True
    with st.container(border=True):
        st.markdown("### External research panels")
        st.write("Optional TradingView displays load for this workspace after you allow them. TradingView receives your IP address, symbol, widget type and embedding page URL. Your notes are not sent to TradingView.")
        with st.expander("Privacy & display details"):
            st.caption("TradingView may process device and usage analytics, including third-party providers, under its privacy policy. Private sign-in does not replace this choice. Display data is never read into our models or exports.")
            st.markdown("[TradingView privacy policy](https://www.tradingview.com/privacy-policy/)")
        st.session_state[key] = False
        st.toggle("Allow automatic TradingView panels this session", key=key,
                  on_change=_apply_panel_consent, args=(key,))
        st.caption("External charts are off until you choose to allow them. Disable them or reset preferences in Settings at any time.")
    return False


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
    enabled = render_external_panel_consent()


    st.markdown("## Company overview")
    st.caption(
        "The company at a glance. Prices and financial figures "
        "are supplied by TradingView and may be delayed."
    )
    _render_panel(symbol, "Overview", enabled)

    st.markdown("## Historical price chart")
    st.caption(
        "Explore how prices changed over your selected period. "
        + LOOKBACKS[lookback][2]
        + " requested; availability depends on TradingView."
    )
    if enabled:
        components.html(
            chart_embed_html(symbol, lookback, chart_type),
            height=640,
            scrolling=False,
        )
    else:
        st.info("Enable TradingView panels to see historical prices.")

    st.markdown("## Financial performance")
    st.caption(
        "Explore revenue, earnings and financial statements. "
        "Check the reporting dates, units and currency."
    )
    _render_panel(symbol, "Financials", enabled)

    st.markdown("## Inside the business")
    st.caption(
        "Understand the business model, products and industry "
        "behind the stock symbol."
    )
    _render_panel(symbol, "Company", enabled)


    st.markdown("## Technical analysis")
    st.caption(
        "A snapshot of price trends and momentum, calculated "
        "by TradingView using technical indicators."
    )

    a, b, c = st.columns(3)

    with a, st.container(border=True):
        st.markdown("**What is measured?**")
        st.write(
            "Moving averages measure price trends. "
            "Oscillators help measure momentum and "
            "potentially stretched conditions."
        )

    with b, st.container(border=True):
        st.markdown("**What do the numbers mean?**")
        st.write(
            "Sell, Neutral and Buy count indicator signals. "
            "For example, 17 Buy and 1 Sell means more "
            "indicators currently lean positive. "
            "They are not analyst votes."
        )

    with c, st.container(border=True):
        st.markdown("**Why select a timeframe?**")
        st.write(
            "Daily uses daily price bars; weekly uses weekly "
            "bars. The same stock can show different "
            "signals at different timeframes."
        )

    st.caption(
        "A Strong Buy rating summarizes indicator conditions. "
        "It does not calculate the probability of a price rise "
        "or specify when to sell."
    )

    _render_panel(symbol, "Technicals", enabled)
    st.caption(
        "These are TradingView's technical ratings, "
        "not Quant Intelligence recommendations."
    )

    st.markdown("## Company news")
    st.caption(
        "News is displayed by TradingView. Check each article's "
        "publication date and original source before relying on it."
    )
    _render_panel(symbol, "News", enabled)
    st.link_button(
        "Browse full company news on TradingView",
        symbol_url + "news/",
    )
    st.caption(
        "The embedded feed may have limited coverage for some "
        "listings. The full provider page may offer more stories."
    )


    st.markdown("## Continue your investigation")
    st.caption(
        "Build and export your source-linked research record "
        "in Opportunity Discovery, or explore a theoretical "
        "options scenario using your own assumptions."
    )
    _render_notes(symbol)
    st.button("Model manual assumptions in Options Lab", on_click=_open_options_lab, args=(symbol,), key="qi_stock_risk_lab")
    if enabled:
        st.caption("Missing panel? Availability depends on the symbol, provider and browser. Missing data is never replaced with fictional values.")
    st.link_button("Open this stock on TradingView ↗", symbol_url)


def _apply_panel_consent(key: str = "qi_explorer_consent") -> None:
    """Apply the disclosed visitor choice before Settings is rebuilt."""
    st.session_state["qi_external_charts"] = st.session_state[key]
    record_external_panel_choice()
