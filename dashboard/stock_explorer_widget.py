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

    from dashboard.stock_search import render_search, suggested_tickers

    symbol = render_search()

    if symbol is None:
        query = st.session_state.get("qi_universal_stock_search", "")
        suggestions = suggested_tickers(query)
        if suggestions:
            st.caption(
                "Did you mean: " + ", ".join(suggestions) + "?"
            )
        return

    with st.expander("Chart settings"):
        period_col, type_col = st.columns(2)
        with period_col:
            lookback = st.selectbox(
                "Historical period",
                list(LOOKBACKS),
                index=next(
                    (
                        i for i, key in enumerate(LOOKBACKS)
                        if str(key).upper() in ("1W", "1WK", "1 WEEK")
                    ),
                    0,
                ),
                key="qi_stock_lookback",
            )
        with type_col:
            chart_type = st.selectbox(
                "Chart type",
                ["Line", "Candlestick"],
                key="qi_stock_chart_type",
            )

    st.caption("Market information by TradingView · May be delayed or unavailable · Not investment advice")
    if symbol == "AMEX:SPY":
        st.caption(
            "S&P 500 market overview · SPY ETF proxy · USD. "
            "This tracks the index but is not the index itself."
        )

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

    from dashboard.volatility_intelligence import render_volatility_intelligence

    render_volatility_intelligence(symbol)

    st.markdown("## Understanding the numbers")

    from dashboard.perp_market_size import render_perp_market_size

    render_perp_market_size(symbol)
    from dashboard.company_briefing import render_company_briefing

    if symbol == "AMEX:SPY":
        st.caption(
            "SPY is an ETF tracking the S&P 500, not an individual "
            "company. Company financial analysis is available when "
            "you select a company."
        )
    else:
        render_company_briefing(symbol)

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

    st.markdown("## Financial performance")
    st.caption(
        "Explore revenue, earnings and financial statements. "
        "Check the reporting dates, units and currency."
    )
    if symbol == "AMEX:SPY":
        st.info(
            "SPY is an exchange-traded fund, not an operating company. "
            "Revenue, earnings and corporate balance-sheet ratios "
            "do not apply in the same way. Relevant fund measures "
            "include net assets, expense ratio, holdings and "
            "tracking performance."
        )
    else:
        _render_panel(symbol, "Financials", enabled)

    st.markdown("## Inside the business")
    st.caption(
        "Understand the business model, products and industry "
        "behind the stock symbol."
    )
    _render_panel(symbol, "Company", enabled)


    with st.expander("More headlines from TradingView"):
        st.caption(
            "Independent external news display. Check original "
            "publication dates and publisher sources."
        )
        _render_panel(symbol, "News", enabled)
        st.link_button(
            "Browse all company news on TradingView",
            symbol_url + "news/",
        )


    if symbol in st.session_state.get("qi_discovery_notebook", {}):
        from dashboard.discovery_notebook import render_record_editor

        st.markdown("### Shared research notebook")
        st.caption(
            "Edit your existing source-linked research record. "
            "Save your changes before downloading the updated export."
        )
        render_record_editor(symbol)

    st.markdown("## Continue your investigation")
    st.caption(
        "Build and export your source-linked research record "
        "in Opportunity Discovery, or explore a theoretical "
        "options scenario using your own assumptions."
    )
    st.button("Model manual assumptions in Options Lab", on_click=_open_options_lab, args=(symbol,), key="qi_stock_risk_lab")
    if enabled:
        st.caption("Missing panel? Availability depends on the symbol, provider and browser. Missing data is never replaced with fictional values.")
    st.link_button("Open this stock on TradingView ↗", symbol_url)


def _apply_panel_consent(key: str = "qi_explorer_consent") -> None:
    """Apply the disclosed visitor choice before Settings is rebuilt."""
    st.session_state["qi_external_charts"] = st.session_state[key]
    record_external_panel_choice()
