
"""
Quant Options Engine — Quant Intelligence Dashboard.

Interactive research dashboard providing:
- Platform overview.
- Historical stock research.
- European option pricing.
- Analytical Greeks.
- Hypothetical option price scenarios.

Run from the project root:

    python -m streamlit run dashboard/main.py

Historical market data is for research and education.
It is not a prediction or investment recommendation.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# PROJECT IMPORT CONFIGURATION
# ============================================================

# Add the repository root before importing project modules.
# This supports both local runs and Streamlit Cloud.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.intelligence.catalyst_engine import analyze_headline  # noqa: E402
from app.intelligence.news_engine import fetch_company_news  # noqa: E402
from app.intelligence.risk_engine import calculate_risk_metrics  # noqa: E402
from app.intelligence.risk_interpreter import interpret_risk_metrics  # noqa: E402
from app.market_data.stock_history import (  # noqa: E402
    calculate_normalized_performance,
    calculate_stock_statistics,
    fetch_stock_history,
    validate_ticker,
)
from app.pricing.black_scholes import BlackScholes  # noqa: E402
from dashboard.forecast_intelligence_page import render_forecast_intelligence  # noqa: E402
from dashboard.market_scanner_page import render_market_scanner  # noqa: E402
from dashboard.portfolio_page import render_portfolio_manager  # noqa: E402

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Quant Intelligence | Quant Options Engine",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #080d18;
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] {
        background-color: #0d1424;
        border-right: 1px solid #1e293b;
    }

    h1, h2, h3 {
        color: #f8fafc;
    }

    [data-testid="stMetric"] {
        background: #111c2e;
        border: 1px solid #243247;
        border-radius: 12px;
        padding: 18px;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8;
    }

    [data-testid="stMetricValue"] {
        color: #f8fafc;
    }

    div.stButton > button {
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background-color: #1d4ed8;
        color: white;
    }

    .section-caption {
        color: #94a3b8;
        font-size: 0.95rem;
    }

    .dashboard-card {
        background: #111c2e;
        border: 1px solid #243247;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
    }

    .dashboard-card h3 {
        margin-top: 0;
    }

    .dashboard-card p {
        color: #94a3b8;
        margin-bottom: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CACHE MARKET DATA
# ============================================================

@st.cache_data(ttl=900, show_spinner=False)
def load_stock_history(
    ticker: str,
    period: str,
) -> pd.DataFrame:
    """
    Retrieve and cache historical stock prices.

    The cache expires after 15 minutes.

    This reduces repeated Yahoo Finance requests when
    users interact with charts and dashboard controls.

    A cache lifetime does not guarantee that Yahoo's
    underlying market data is current.
    """

    return fetch_stock_history(
        ticker=ticker,
        period=period,
    )


# ============================================================
# OPTION PRICING HELPERS
# ============================================================

def create_engine(
    stock_price: float,
    strike_price: float,
    days: int,
    interest_rate: float,
    volatility: float,
    dividend_yield: float,
) -> BlackScholes:
    """Build the existing Black-Scholes pricing engine."""

    return BlackScholes(
        S=stock_price,
        K=strike_price,
        T=days / 365.0,
        r=interest_rate / 100.0,
        sigma=volatility / 100.0,
        q=dividend_yield / 100.0,
    )


def display_number(
    value: float | None,
    decimals: int = 4,
) -> str:
    """Format a numerical value or show N/A."""

    if value is None:
        return "N/A"

    return f"{value:,.{decimals}f}"


# ============================================================
# GENERAL CHART HELPER
# ============================================================

def make_chart(
    x_values,
    y_values,
    title: str,
    x_title: str,
    y_title: str,
    color: str = "#38bdf8",
) -> go.Figure:
    """Create a consistently styled interactive line chart."""

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=x_values,
            y=y_values,
            mode="lines",
            line={
                "color": color,
                "width": 3,
            },
            fill="tozeroy",
            fillcolor="rgba(56, 189, 248, 0.08)",
            hovertemplate="%{x}<br>%{y:.4f}<extra></extra>",
        )
    )

    figure.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor="#111c2e",
        plot_bgcolor="#111c2e",
        font={"color": "#cbd5e1"},
        xaxis_title=x_title,
        yaxis_title=y_title,
        margin={
            "l": 20,
            "r": 20,
            "t": 55,
            "b": 20,
        },
        height=390,
        hovermode="x unified",
    )

    figure.update_xaxes(gridcolor="#243247")
    figure.update_yaxes(gridcolor="#243247")

    return figure


# ============================================================
# STOCK PRICE CHART
# ============================================================

def make_stock_price_chart(
    history: pd.DataFrame,
    ticker: str,
    chart_type: str,
) -> go.Figure:
    """
    Display historical stock prices as a line or candlestick chart.

    Uses the adjusted OHLC data returned by stock_history.py.
    """

    figure = go.Figure()

    if chart_type == "Candlestick":

        figure.add_trace(
            go.Candlestick(
                x=history["Date"],
                open=history["Open"],
                high=history["High"],
                low=history["Low"],
                close=history["Close"],
                name=ticker,
                increasing_line_color="#22c55e",
                decreasing_line_color="#ef4444",
            )
        )

    else:

        figure.add_trace(
            go.Scatter(
                x=history["Date"],
                y=history["Close"],
                mode="lines",
                name=ticker,
                line={
                    "color": "#38bdf8",
                    "width": 3,
                },
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "$%{y:,.2f}<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title=f"{ticker} — Historical Price",
        template="plotly_dark",
        paper_bgcolor="#111c2e",
        plot_bgcolor="#111c2e",
        font={"color": "#cbd5e1"},
        xaxis_title="Date",
        yaxis_title="Adjusted Price ($)",
        height=480,
        margin={
            "l": 20,
            "r": 20,
            "t": 55,
            "b": 20,
        },
        xaxis_rangeslider_visible=False,
        hovermode=(
            "x"
            if chart_type == "Candlestick"
            else "x unified"
        ),
    )

    figure.update_xaxes(gridcolor="#243247")
    figure.update_yaxes(gridcolor="#243247")

    return figure


# ============================================================
# NORMALIZED PERFORMANCE COMPARISON
# ============================================================

def make_comparison_chart(
    stock_history: pd.DataFrame,
    benchmark_history: pd.DataFrame,
    ticker: str,
) -> tuple[go.Figure, float, float]:
    """
    Compare stock and SPY performance over matching dates.

    Both assets start at 100 on their first common date.

    Returns:
        comparison chart
        stock return percentage
        benchmark return percentage
    """

    stock = calculate_normalized_performance(
        stock_history
    )

    benchmark = calculate_normalized_performance(
        benchmark_history
    )

    # Keep raw closing prices for proper common-date alignment.
    stock = stock_history[
        ["Date", "Close"]
    ].copy()

    benchmark = benchmark_history[
        ["Date", "Close"]
    ].copy()

    # Preserve intraday timestamps when comparing short periods.
    # Daily observations are matched by trading date.
    stock["Date"] = pd.to_datetime(
        stock["Date"],
        utc=True,
    )

    benchmark["Date"] = pd.to_datetime(
        benchmark["Date"],
        utc=True,
    )

    def is_intraday(frame: pd.DataFrame) -> bool:
        timestamps = frame["Date"].sort_values().dropna()
        differences = timestamps.diff().dropna()
        return bool(
            not differences.empty
            and differences.min() < pd.Timedelta(hours=12)
        )

    intraday = is_intraday(stock) or is_intraday(benchmark)

    if not intraday:
        stock["Date"] = stock["Date"].dt.date
        benchmark["Date"] = benchmark["Date"].dt.date

    stock = stock.rename(
        columns={"Close": "Stock"}
    )

    benchmark = benchmark.rename(
        columns={"Close": "Benchmark"}
    )

    aligned = pd.merge(
        stock,
        benchmark,
        on="Date",
        how="inner",
    )

    aligned = aligned.sort_values(
        "Date"
    ).reset_index(drop=True)

    if len(aligned) < 2:
        raise ValueError(
            "Not enough matching trading dates "
            "to compare performance."
        )

    # Rebase only AFTER aligning dates.
    #
    # This avoids comparing different start dates.
    aligned["StockNormalized"] = (
        aligned["Stock"]
        / aligned["Stock"].iloc[0]
        * 100.0
    )

    aligned["BenchmarkNormalized"] = (
        aligned["Benchmark"]
        / aligned["Benchmark"].iloc[0]
        * 100.0
    )

    stock_return = (
        aligned["StockNormalized"].iloc[-1] - 100.0
    )

    benchmark_return = (
        aligned["BenchmarkNormalized"].iloc[-1] - 100.0
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=aligned["Date"],
            y=aligned["StockNormalized"],
            name=ticker,
            mode="lines",
            line={
                "color": "#38bdf8",
                "width": 3,
            },
        )
    )

    figure.add_trace(
        go.Scatter(
            x=aligned["Date"],
            y=aligned["BenchmarkNormalized"],
            name="SPY",
            mode="lines",
            line={
                "color": "#f59e0b",
                "width": 3,
            },
        )
    )

    figure.update_layout(
        title=f"{ticker} vs SPY — Normalized Performance",
        template="plotly_dark",
        paper_bgcolor="#111c2e",
        plot_bgcolor="#111c2e",
        font={"color": "#cbd5e1"},
        xaxis_title="Date",
        yaxis_title="Growth of 100",
        height=430,
        margin={
            "l": 20,
            "r": 20,
            "t": 55,
            "b": 20,
        },
        hovermode="x unified",
    )

    figure.update_xaxes(gridcolor="#243247")
    figure.update_yaxes(gridcolor="#243247")

    return (
        figure,
        float(stock_return),
        float(benchmark_return),
    )


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    st.markdown("## 📈 QUANT INTELLIGENCE")

    st.caption("Quant Options Engine")

    st.markdown(
        "<div style='color: #94a3b8; font-size: 13px; "
        "font-weight: 500; margin-top: -8px;'>"
        "Developed by <span style='color: #60a5fa; "
        "font-weight: 600;'>Kyriakos Margaritis</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "🏠 Overview"

    # Apply navigation requests BEFORE creating the sidebar widget.
    requested_page = st.session_state.pop(
        "_navigation_request", None
    )

    if requested_page is not None:
        st.session_state["selected_page"] = requested_page

    page = st.radio(
        "Navigation",
        [
            "🏠 Overview",
            "🔎 Stock Explorer",
            "💰 Options Lab",
            "📊 Greeks Analysis",
            "📈 Scenario Explorer",
            "🔍 Market Scanner",
            "💎 Quant Discovery",
            "💼 Portfolio Manager",
            "🧠 Forecast Intelligence",
            "🧠 Strategy Research",
        ],
        label_visibility="collapsed",        key="selected_page",
    )

    st.divider()

    st.caption("PLATFORM STATUS")

    st.success("● Pricing Engine Online")

    st.caption("Research platform — development build")

    st.divider()

    st.caption(
        "Educational and research software. "
        "Not investment advice."
    )


# ============================================================
# SHARED OPTION INPUTS
# ============================================================

if page in [
    "💰 Options Lab",
    "📊 Greeks Analysis",
    "📈 Scenario Explorer",
]:

    st.sidebar.markdown("### ⚙️ Option Parameters")

    stock_price = st.sidebar.number_input(
        "Stock Price ($)",
        min_value=0.01,
        value=100.0,
        step=1.0,
    )

    strike_price = st.sidebar.number_input(
        "Strike Price ($)",
        min_value=0.01,
        value=105.0,
        step=1.0,
    )

    days = st.sidebar.number_input(
        "Days Until Expiration",
        min_value=0,
        max_value=3650,
        value=30,
        step=1,
    )

    volatility = st.sidebar.number_input(
        "Annual Volatility (%)",
        min_value=0.0,
        max_value=500.0,
        value=25.0,
        step=1.0,
    )

    interest_rate = st.sidebar.number_input(
        "Risk-Free Interest Rate (%)",
        min_value=-20.0,
        max_value=100.0,
        value=4.0,
        step=0.25,
    )

    dividend_yield = st.sidebar.number_input(
        "Dividend Yield (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=0.25,
    )

    engine = create_engine(
        stock_price=stock_price,
        strike_price=strike_price,
        days=days,
        interest_rate=interest_rate,
        volatility=volatility,
        dividend_yield=dividend_yield,
    )

    results = engine.greeks()


# ============================================================
# OVERVIEW
# ============================================================

if page == "🏠 Overview":

    st.title("🧠 Quant Intelligence")

    st.markdown(
        "### Understand the market without needing to be a financial expert."
    )

    st.write(
        "Explore stocks, understand options, and learn about "
        "investment risk using powerful financial analysis "
        "tools explained in everyday language."
    )

    st.info(
        "💡 **New to investing?** Start with Explore Stocks. "
        "You can learn about a company's price history and "
        "how much its stock tends to move."
    )

    st.divider()

    st.header("What would you like to explore?")

    st.caption(
        "Choose a tool below. Advanced calculations are still "
        "available whenever you want to explore further."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 Explore Stocks")
        st.write(
            "Look up a company and understand its historical "
            "performance, price movements, and trends."
        )

        if st.button(
            "Explore Stocks →",
            use_container_width=True,
            key="home_stocks",
        ):
            st.session_state["_navigation_request"] = "🔎 Stock Explorer"
            st.rerun()

        st.markdown("### 💰 Options Calculator")
        st.write(
            "Estimate what an option might be worth and learn "
            "how stock prices and time affect its value."
        )

        if st.button(
            "Explore Options →",
            use_container_width=True,
            key="home_options",
        ):
            st.session_state["_navigation_request"] = "💰 Options Lab"
            st.rerun()

        st.markdown("### 🔍 Discover Stocks")
        st.write(
            "Explore stocks using market characteristics "
            "such as momentum and historical volatility."
        )

        if st.button(
            "Discover Stocks →",
            use_container_width=True,
            key="home_scanner",
        ):
            st.session_state["_navigation_request"] = "🔍 Market Scanner"
            st.rerun()

    with col2:
        st.markdown("### 🛡️ Understand Option Risk")
        st.write(
            "See how an option's value may change when "
            "stock prices, time, or volatility change."
        )

        if st.button(
            "Understand Risk →",
            use_container_width=True,
            key="home_risk",
        ):
            st.session_state["_navigation_request"] = "📊 Greeks Analysis"
            st.rerun()

        st.markdown("### 💼 My Portfolio")
        st.write(
            "Explore your investments together and "
            "understand their combined performance and risk."
        )

        if st.button(
            "Explore Portfolio →",
            use_container_width=True,
            key="home_portfolio",
        ):
            st.session_state["_navigation_request"] = "💼 Portfolio Manager"
            st.rerun()

        st.markdown("### 🧠 AI Forecast Research")
        st.write(
            "Discover whether machine learning actually "
            "improved predictions in our historical experiments."
        )

        if st.button(
            "Explore Forecast Research →",
            use_container_width=True,
            key="home_forecasts",
        ):
            st.session_state["_navigation_request"] = "🧠 Forecast Intelligence"
            st.rerun()

    st.divider()

    st.subheader("How Quant Intelligence Works")

    st.markdown(
        "**1. Explore:** Choose a stock or financial question.\n\n"
        "**2. Understand:** View results explained in plain English.\n\n"
        "**3. Go Deeper:** Explore advanced calculations and charts "
        "when you're ready."
    )

    st.caption(
        "Quant Intelligence provides financial analysis and "
        "educational research, not personalized investment advice."
    )


elif page == "🔎 Stock Explorer":

    st.title("🔎 Stock Explorer")

    st.caption(
        "Research historical stock and ETF performance "
        "using Yahoo Finance market data."
    )

    # --------------------------------------------------------
    # SEARCH CONTROLS
    # --------------------------------------------------------

    ticker_col, period_col, chart_col = st.columns(
        [2, 1, 1]
    )

    with ticker_col:

        ticker_input = st.text_input(
            "Ticker Symbol",
            value="AAPL",
            placeholder="Enter AAPL, MSFT, NVDA, SPY...",
        )

    with period_col:

        selected_period = st.selectbox(
            "Historical Period",
            [
                "1d",
                "5d",
                "1mo",
                "3mo",
                "6mo",
                "1y",
                "5y",
                "max",
            ],
            index=5,
        )

    with chart_col:

        chart_type = st.selectbox(
            "Chart Type",
            [
                "Line",
                "Candlestick",
            ],
        )

    # --------------------------------------------------------
    # VALIDATE TICKER
    # --------------------------------------------------------

    try:

        ticker = validate_ticker(
            ticker_input
        )

    except ValueError as exc:

        st.error(str(exc))
        st.stop()

    # --------------------------------------------------------
    # DOWNLOAD HISTORICAL DATA
    # --------------------------------------------------------

    with st.spinner(
        f"Loading historical market data for {ticker}..."
    ):

        try:

            history = load_stock_history(
                ticker,
                selected_period,
            )

            statistics = calculate_stock_statistics(
                history
            )

            # QUANT_RISK_INTELLIGENCE_V1
            # Use independent daily history for consistent risk statistics.
            st.markdown("### Risk Intelligence")
            st.caption(
                "Historical risk calculated from approximately one year "
                "of daily prices, independent of the chart timeframe."
            )

            try:
                risk_stock_history = fetch_stock_history(
                    ticker, period="1y"
                )
                risk_spy_history = fetch_stock_history(
                    "SPY", period="1y"
                )

                risk_metrics = calculate_risk_metrics(
                    risk_stock_history,
                    risk_spy_history,
                )

                # QUANT_PERSONALIZED_RISK_V2
                risk_explanations = interpret_risk_metrics(risk_metrics)

                def format_risk(value, suffix="", decimals=2):
                    if value is None:
                        return "N/A"
                    return f"{value:.{decimals}f}{suffix}"

                risk_cols = st.columns(5)

                risk_items = [
                    (
                        "1Y Volatility",
                        format_risk(
                            risk_metrics["annualized_volatility_pct"], "%"
                        ),
                        risk_explanations["annualized_volatility_pct"],
                    ),
                    (
                        "1Y Max Drawdown",
                        format_risk(
                            risk_metrics["maximum_drawdown_pct"], "%"
                        ),
                        risk_explanations["maximum_drawdown_pct"],
                    ),
                    (
                        "Sharpe Ratio",
                        format_risk(risk_metrics["sharpe_ratio"]),
                        risk_explanations["sharpe_ratio"],
                    ),
                    (
                        "Market Sensitivity (Beta)",
                        format_risk(risk_metrics["beta_vs_spy"]),
                        risk_explanations["beta_vs_spy"],
                    ),
                    (
                        "Market Correlation",
                        format_risk(risk_metrics["correlation_vs_spy"]),
                        risk_explanations["correlation_vs_spy"],
                    ),
                ]

                for column, (label, value, explanation) in zip(
                    risk_cols, risk_items
                ):
                    with column:
                        st.metric(label, value)
                        st.caption(explanation)

                st.caption(
                    f"Daily price observations: "
                    f"{risk_metrics['daily_observations']} | "
                    f"SPY overlapping dates: "
                    f"{risk_metrics['benchmark_overlap_days']}"
                )

            except (ValueError, KeyError, TypeError, OSError) as exc:
                st.info(f"Risk Intelligence unavailable: {exc}")

            # QUANT_INTRADAY_STATISTICS_V1
            # Intraday returns must not be annualized as daily returns.
            is_intraday_period = selected_period in ("1d", "5d")

            if is_intraday_period:
                statistics["annualized_volatility_pct"] = None

        except (ValueError, RuntimeError) as exc:

            st.error(
                f"Unable to load {ticker}: {exc}"
            )

            st.stop()

    # --------------------------------------------------------
    # DATA INFORMATION
    # --------------------------------------------------------

    latest_observation = pd.to_datetime(
        history["Date"].iloc[-1],
        utc=True,
    )

    st.caption(
        f"Ticker: {ticker} | "
        f"Latest available daily observation: "
        f"{latest_observation.strftime('%Y-%m-%d')} | "
        f"Data may be delayed or incomplete."
    )

    # --------------------------------------------------------
    # STOCK INTELLIGENCE — BEGINNER SUMMARY
    # --------------------------------------------------------

    # --------------------------------------------------------
    # INVESTMENT RECOMMENDATION ENGINE
    # --------------------------------------------------------

    from app.intelligence.recommendation_engine import assess_stock

    # Always use a dedicated five-year history for research scoring.
    # Chart selections must not change the investment assessment.
    # The scoring engine evaluates its most recent 252 observations.
    try:
        assessment_history = fetch_stock_history(
            ticker,
            period="5y",
        )
    except (ValueError, RuntimeError, KeyError) as exc:
        st.warning(
            f"Unable to retrieve investment rating history: {exc}"
        )
        assessment_history = history

    try:
        assessment = assess_stock(assessment_history)
    except (ValueError, TypeError, KeyError) as exc:
        st.warning(f"Investment assessment unavailable: {exc}")
        assessment = None

    if assessment is not None:

        st.markdown("### ⭐ Investment Rating")

        rating_col1, rating_col2, rating_col3 = st.columns(3)

        with rating_col1:
            if assessment.score is None:
                st.metric("Investment Score", "N/A")
            else:
                st.metric(
                    "Investment Score",
                    f"{assessment.score}/100",
                )

        with rating_col2:
            recommendation_labels = {
                "STRONG TECHNICAL SIGNAL": "STRONG",
                "FAVORABLE TECHNICAL SIGNAL": "FAVORABLE",
                "NEUTRAL / MIXED": "NEUTRAL",
                "CAUTION": "CAUTION",
                "UNFAVORABLE TECHNICAL SIGNAL": "UNFAVORABLE",
                "INSUFFICIENT EVIDENCE": "N/A",
            }

            short_recommendation = recommendation_labels.get(
                assessment.recommendation,
                "UNKNOWN",
            )

            st.metric(
                "Technical Recommendation",
                short_recommendation,
            )

        with rating_col3:
            st.metric(
                "Historical Risk",
                assessment.risk.replace(
                    "Lower Historical Volatility",
                    "Low",
                ),
            )

        st.write(
            f"**Market Outlook:** {assessment.outlook}"
        )

        st.caption(
            f"Prediction reliability: {assessment.reliability}"
        )

        with st.expander("🔍 Why did this stock receive this rating?"):
            for reason in assessment.reasons:
                st.write(f"• {reason}")

            st.info(
                "This score summarizes historical technical "
                "signals. It is not a probability of profit "
                "or a validated BUY/SELL recommendation."
            )

        st.divider()


    # QUANT_INTELLIGENCE_NEWS_PANEL_V1
    st.markdown("---")
    st.markdown("### 📰 News Intelligence")
    st.caption(
        "Recent company headlines from Google News. "
        "News does not currently affect investment scores."
    )

    @st.cache_data(ttl=900, show_spinner=False)
    def _cached_company_news(symbol: str):
        return fetch_company_news(symbol, days=7, limit=12)

    try:
        with st.spinner("Retrieving recent company news..."):
            news_articles = _cached_company_news(ticker)

        if not news_articles:
            st.info("No recent articles found for this ticker.")
        else:
            st.caption(f"{len(news_articles)} recent articles")

            for article in news_articles:
                title = article.get("title") or "Untitled article"
                publisher = article.get("publisher") or "Unknown publisher"
                published = str(article.get("published") or "")
                article_url = article.get("url")

                st.markdown(f"**{title}**")

                catalysts = analyze_headline(title)

                if catalysts:
                    for catalyst in catalysts:
                        st.caption(
                            f"🔵 {catalyst.label}: "
                            f"{catalyst.explanation}"
                        )
                else:
                    st.caption("⚪ No recognized catalyst")

                publication_date = published[:10] if published else "Date unavailable"
                st.caption(f"{publisher} · {publication_date}")

                if article_url and str(article_url).startswith(
                    ("https://", "http://")
                ):
                    st.link_button(
                        "Read article ↗",
                        article_url,
                    )
                else:
                    st.caption("Article link unavailable")

                st.divider()

    except Exception as exc:
        st.warning(f"News temporarily unavailable: {exc}")

    st.markdown("## 🧠 Stock Intelligence")

    st.caption(
        "A simple explanation of the asset's historical "
        "performance and risk. These measurements describe "
        "the past and do not guarantee future returns."
    )

    latest_price = float(statistics["latest_close"])
    historical_return = float(statistics["total_return_pct"])
    annual_volatility = statistics["annualized_volatility_pct"]

    # Describe historical direction without claiming to predict prices.
    if historical_return > 3:
        trend_label = "📈 Positive historical trend"
        trend_explanation = (
            "The asset increased in price over the selected period."
        )
    elif historical_return < -3:
        trend_label = "📉 Negative historical trend"
        trend_explanation = (
            "The asset decreased in price over the selected period."
        )
    else:
        trend_label = "➡️ Relatively flat historical trend"
        trend_explanation = (
            "The asset's overall price change was relatively small "
            "over the selected period."
        )

    # These are descriptive volatility bands, not validated risk scores.
    if annual_volatility is None:
        risk_label = "Unknown"
        risk_explanation = "Not enough data to estimate volatility."
    elif annual_volatility < 20:
        risk_label = "Lower historical volatility"
        risk_explanation = (
            "Price fluctuations were relatively small "
            "on an annualized basis."
        )
    elif annual_volatility < 40:
        risk_label = "Moderate historical volatility"
        risk_explanation = (
            "The asset experienced meaningful price fluctuations."
        )
    else:
        risk_label = "Higher historical volatility"
        risk_explanation = (
            "The asset experienced substantial price fluctuations."
        )

    summary_col1, summary_col2, summary_col3 = st.columns(3)

    with summary_col1:
        st.metric("💵 Latest Available Price", f"${latest_price:,.2f}")

    with summary_col2:
        st.metric("📈 Historical Return", f"{historical_return:+.2f}%")

    with summary_col3:
        short_risk_label = {
            "Lower historical volatility": "Low",
            "Moderate historical volatility": "Moderate",
            "Higher historical volatility": "High",
            "Unknown": "Unknown",
        }.get(risk_label, "Unknown")

        st.metric(
            "⚠️ Historical Risk",
            short_risk_label,
        )

    st.markdown("### 📋 What Does This Mean?")

    st.write(f"**Price trend:** {trend_label}")
    st.write(trend_explanation)

    st.write(f"**Risk:** {risk_label}")
    st.write(risk_explanation)

    st.info(
        "🎯 Prediction confidence: Not yet validated. "
        "We will only display confidence ratings after "
        "testing forecast reliability on unseen historical data."
    )

    with st.expander("🔬 How These Measurements Work"):
        st.write(
            "**Historical return:** The percentage change in price "
            "over the selected historical period."
        )
        st.write(
            "**Annualized volatility:** A statistical measure of "
            "how much daily returns have fluctuated, expressed "
            "on an annualized basis."
        )
        st.write(
            "**Historical trend:** A simple description based on "
            "the total return over the selected period. "
            "It is not a forecast."
        )
        st.write(
            "**Risk labels:** Descriptive volatility categories, "
            "not personalized investment risk assessments."
        )

    st.divider()

    # --------------------------------------------------------
    # MAIN STATISTICS
    # --------------------------------------------------------

    st.markdown("### Market Overview")

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:

        st.metric(
            "Latest Adjusted Close",
            f"${statistics['latest_close']:,.2f}",
        )

    with metric2:

        daily_change = statistics[
            "latest_change_pct"
        ]

        st.metric(
            (
                "Latest Bar Change"
                if selected_period in ("1d", "5d")
                else "Latest Daily Change"
            ),
            (
                f"{daily_change:+.2f}%"
                if daily_change is not None
                else "N/A"
            ),
        )

    with metric3:

        st.metric(
            "Historical Return",
            f"{statistics['total_return_pct']:+.2f}%",
        )

    with metric4:

        volatility_value = statistics[
            "annualized_volatility_pct"
        ]

        st.metric(
            (
                "Annualized Volatility"
                if selected_period not in ("1d", "5d")
                else "Annualized Volatility (Daily)"
            ),
            (
                f"{volatility_value:.2f}%"
                if volatility_value is not None
                else "N/A"
            ),
        )

    st.divider()

    # --------------------------------------------------------
    # HISTORICAL PRICE CHART
    # --------------------------------------------------------

    st.subheader("Historical Price Chart")

    price_figure = make_stock_price_chart(
        history=history,
        ticker=ticker,
        chart_type=chart_type,
    )

    st.plotly_chart(
        price_figure,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # ADDITIONAL RISK STATISTICS
    # --------------------------------------------------------

    st.subheader("Historical Risk Statistics")

    risk1, risk2, risk3 = st.columns(3)

    with risk1:

        st.metric(
            "Maximum Drawdown",
            f"{statistics['maximum_drawdown_pct']:.2f}%",
        )

    with risk2:

        st.metric(
            (
                "Intraday Observations"
                if selected_period in ("1d", "5d")
                else "Daily Observations"
            ),
            str(statistics["trading_days"]),
        )

    with risk3:

        st.metric(
            "Selected Period",
            selected_period,
        )

    st.divider()

    # --------------------------------------------------------
    # SPY PERFORMANCE COMPARISON
    # --------------------------------------------------------

    st.subheader("Performance vs S&P 500 ETF (SPY)")

    st.caption(
        "Both series are rebased to 100 using their "
        "first matching trading date."
    )

    try:

        if ticker == "SPY":

            st.info(
                "SPY is already the selected asset. "
                "Choose another ticker to compare it "
                "against the SPY benchmark."
            )

        else:

            with st.spinner(
                "Loading SPY benchmark data..."
            ):

                benchmark_history = load_stock_history(
                    "SPY",
                    selected_period,
                )

            (
                comparison_figure,
                stock_return,
                benchmark_return,
            ) = make_comparison_chart(
                stock_history=history,
                benchmark_history=benchmark_history,
                ticker=ticker,
            )

            st.plotly_chart(
                comparison_figure,
                use_container_width=True,
            )

            comparison1, comparison2, comparison3 = (
                st.columns(3)
            )

            with comparison1:

                st.metric(
                    f"{ticker} Return",
                    f"{stock_return:+.2f}%",
                )

            with comparison2:

                st.metric(
                    "SPY Return",
                    f"{benchmark_return:+.2f}%",
                )

            with comparison3:

                st.metric(
                    "Relative Performance",
                    f"{stock_return - benchmark_return:+.2f} pp",
                )

    except (ValueError, RuntimeError) as exc:

        st.warning(
            f"Benchmark comparison unavailable: {exc}"
        )

    # --------------------------------------------------------
    # HISTORICAL DATA TABLE
    # --------------------------------------------------------

    st.divider()

    st.subheader("Historical Market Data")

    is_intraday = selected_period in ("1d", "5d")

    st.caption(
        (
            "Adjusted historical intraday prices. "
            "Timestamps are shown in UTC. "
            "The latest observation may be incomplete."
        )
        if is_intraday
        else (
            "Adjusted historical daily prices. "
            "The latest observation may be incomplete."
        )
    )

    display_history = history.copy()

    timestamps = pd.to_datetime(
        display_history["Date"],
        utc=True,
    )

    display_history["Date"] = timestamps.dt.strftime(
        "%Y-%m-%dT%H:%M:%S%z"
        if is_intraday
        else "%Y-%m-%d"
    )

    st.dataframe(
        display_history.sort_values(
            "Date",
            ascending=False,
        ),
        hide_index=True,
        use_container_width=True,
    )

    # --------------------------------------------------------
    # DOWNLOAD DATA
    # --------------------------------------------------------

    st.download_button(
        label="Download Historical Data (CSV)",
        data=display_history.to_csv(
            index=False
        ).encode("utf-8"),
        file_name=(
            f"{ticker}_{selected_period}_history.csv"
        ),
        mime="text/csv",
    )

    st.warning(
        "Historical performance does not predict future "
        "returns. Yahoo Finance data may be delayed, "
        "revised, or incomplete. Adjusted prices are "
        "not guaranteed executable trading prices."
    )


# ============================================================
# OPTIONS LAB
# ============================================================

elif page == "💰 Options Lab":

    st.title("💰 Options Calculator")

    st.write(
        "Enter your own values to estimate what a stock option "
        "might be worth."
    )

    st.subheader("Step 1 — Find an Asset")

    st.caption(
        "Search by ticker symbol. Supports stocks, ETFs, and "
        "supported cryptocurrencies."
    )

    ticker_input = st.text_input(
        "Stock, ETF, or cryptocurrency ticker",
        value="AAPL",
        placeholder="Examples: AAPL, SPY, NVDA, BTC-USD",
        key="options_ticker_search",
    )

    st.caption(
        "Examples: AAPL · MSFT · NVDA · TSLA · SPY · QQQ · "
        "BTC-USD · ETH-USD"
    )

    selected_stock_price = 100.0
    ticker = ticker_input.strip().upper()

    if ticker:
        try:
            history = fetch_stock_history(ticker, period="1mo")

            if history is None or history.empty:
                st.error(
                    f"No market data found for {ticker}. "
                    "Check the ticker symbol and try again."
                )
            else:
                close_data = history["Close"].dropna()

                if close_data.empty:
                    st.error(
                        f"No valid closing prices were found for {ticker}."
                    )
                else:
                    latest_close = float(close_data.iloc[-1])

                    if latest_close <= 0:
                        st.error(
                            f"The latest price for {ticker} is invalid."
                        )
                    else:
                        selected_stock_price = latest_close

                        latest_index = close_data.index[-1]

                        if hasattr(latest_index, "strftime"):
                            latest_date = latest_index.strftime(
                                "%B %d, %Y"
                            )
                        else:
                            latest_date = "date unavailable"

                        st.success(
                            f"{ticker} — Latest available closing price: "
                            f"${latest_close:,.2f} ({latest_date})"
                        )

        except Exception as exc:
            st.error(
                f"Unable to retrieve market data for {ticker}. "
                f"Details: {exc}"
            )
    else:
        st.info(
            "Enter a ticker symbol above, or use the manual "
            "stock price below."
        )

    st.subheader("Step 2 — What Do You Want to Explore?")

    direction = st.radio(
        "Which direction do you want to explore?",
        ["📈 Price going UP (Call)", "📉 Price going DOWN (Put)"],
        horizontal=True,
        key="options_direction",
        help=(
            "A call gives the holder the right to buy at the strike price. "
            "A put gives the holder the right to sell at the strike price."
        ),
    )

    is_call = "Call" in direction

    st.subheader("Step 3 — Set Up Your Option")

    st.caption(
        "We've provided starting values. You can change any of them."
    )

    with st.form("options_calculator_form"):

        calc_stock = st.number_input(
            "💵 Current price of the asset ($)",
            min_value=0.01,
            value=float(selected_stock_price),
            step=1.0,
            help="The latest available price, or your own estimate.",
        )

        col1, col2 = st.columns(2)

        with col1:
            calc_strike = st.number_input(
                "🎯 At what price would you buy or sell?",
                min_value=0.01,
                value=round(float(selected_stock_price), 2),
                step=1.0,
                help=(
                    "This is called the strike price. "
                    "It determines the price at which the option "
                    "gives you the right to buy (call) or sell (put). "
                    "Actual contracts offer specific strike prices."
                ),
            )

        with col2:
            calc_days = st.selectbox(
                "📅 How long should the option last?",
                [7, 14, 30, 60, 90, 180, 365],
                index=2,
                format_func=lambda days: f"{days} days",
                help=(
                    "This represents the number of days until expiration. "
                    "More time generally makes options more valuable."
                ),
            )

        calc_volatility = st.slider(
            "📊 How much might the price fluctuate?",
            min_value=5,
            max_value=150,
            value=25,
            step=5,
            format="%d%%",
            help=(
                "This is annualized volatility. Higher volatility "
                "generally increases option prices. The default "
                "is illustrative, not calculated from market data."
            ),
        )

        st.caption(
            "💡 Not sure? Leave volatility at 25% for an "
            "illustrative calculation. This is not a measured "
            "volatility estimate for your selected asset."
        )

        with st.expander("⚙️ Advanced Settings — Optional"):
            calc_rate = st.number_input(
                "Annual risk-free interest rate (%)",
                min_value=-20.0,
                max_value=100.0,
                value=4.0,
                step=0.25,
            )

            calc_dividend = st.number_input(
                "Annual dividend yield (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=0.25,
            )

        submitted = st.form_submit_button(
            "💰 Calculate My Option Estimate",
            use_container_width=True,
        )

    if submitted:

        calculator = BlackScholes(
            S=calc_stock,
            K=calc_strike,
            T=calc_days / 365.0,
            r=calc_rate / 100.0,
            sigma=calc_volatility / 100.0,
            q=calc_dividend / 100.0,
        )

        calculated = calculator.greeks()

        call_price = float(calculated["call_price"])
        put_price = float(calculated["put_price"])

        selected_price = call_price if is_call else put_price
        option_name = "Call" if is_call else "Put"
        contract_estimate = selected_price * 100

        break_even = (
            calc_strike + selected_price
            if is_call
            else calc_strike - selected_price
        )

        st.divider()
        st.subheader("Step 4 — Your Estimated Result")

        st.metric(
            f"💰 Estimated {option_name} Option Value",
            f"${contract_estimate:,.2f} per standard contract",
        )

        st.caption(
            f"Approximately ${selected_price:,.2f} per share × "
            "100 shares. This is a theoretical estimate, "
            "not a live market quote."
        )

        st.markdown("### What Does This Mean?")

        if is_call:
            st.write(
                f"You are exploring a **call option**, which gives "
                f"you the right to buy the asset at "
                f"**${calc_strike:,.2f} per share**."
            )
            st.write(
                f"Your estimated **break-even price at expiration** "
                f"is **${break_even:,.2f}**."
            )
        else:
            st.write(
                f"You are exploring a **put option**, which gives "
                f"you the right to sell the asset at "
                f"**${calc_strike:,.2f} per share**."
            )
            st.write(
                f"Your estimated **break-even price at expiration** "
                f"is **${break_even:,.2f}**."
            )

        st.warning(
            "⚠️ Options involve risk. If you purchase an option, "
            "you can lose the entire premium paid. "
            "These estimates do not include trading fees."
        )

        with st.expander("🔬 Advanced Analytics"):

            st.subheader("Option Greeks")

            greek_data = pd.DataFrame(
                {
                    "Greek": [
                        "Delta", "Gamma", "Vega", "Theta", "Rho"
                    ],
                    "Call": [
                        calculated["call_delta"],
                        calculated["gamma"],
                        calculated["vega"],
                        calculated["call_theta"],
                        calculated["call_rho"],
                    ],
                    "Put": [
                        calculated["put_delta"],
                        calculated["gamma"],
                        calculated["vega"],
                        calculated["put_theta"],
                        calculated["put_rho"],
                    ],
                }
            )

            st.dataframe(
                greek_data,
                hide_index=True,
                use_container_width=True,
            )

            st.markdown("### What Do These Numbers Mean?")

            st.write(
                "**Delta:** Estimated option price change "
                "for a $1 stock price movement."
            )

            st.write(
                "**Gamma:** How quickly Delta changes."
            )

            st.write(
                "**Vega:** Sensitivity to changes in volatility."
            )

            st.write(
                "**Theta:** Sensitivity to the passage of time."
            )

            st.write(
                "**Rho:** Sensitivity to interest rate changes."
            )

    else:
        st.info(
            "👆 Enter your values and click "
            "**💰 Calculate My Option Estimate** to see your results."
        )

    st.caption(
        "Educational Black–Scholes estimates. "
        "Not personalized investment advice."
    )


# ============================================================
# GREEKS ANALYSIS
# ============================================================

elif page == "📊 Greeks Analysis":

    st.title("📊 Greeks Analysis")

    st.caption(
        "Explore how option risk changes "
        "as the underlying stock price moves."
    )

    option_type = st.selectbox(
        "Option Type",
        ["Call", "Put"],
    )

    lower_price = max(
        stock_price * 0.5,
        0.01,
    )

    upper_price = stock_price * 1.5

    stock_prices = np.linspace(
        lower_price,
        upper_price,
        100,
    )

    deltas = []
    gammas = []
    vegas = []
    thetas = []

    for simulated_price in stock_prices:

        simulated_engine = create_engine(
            stock_price=float(simulated_price),
            strike_price=strike_price,
            days=days,
            interest_rate=interest_rate,
            volatility=volatility,
            dividend_yield=dividend_yield,
        )

        simulated_results = simulated_engine.greeks()

        if option_type == "Call":

            deltas.append(
                simulated_results["call_delta"]
            )

            thetas.append(
                simulated_results["call_theta"]
            )

        else:

            deltas.append(
                simulated_results["put_delta"]
            )

            thetas.append(
                simulated_results["put_theta"]
            )

        gammas.append(
            simulated_results["gamma"]
        )

        vegas.append(
            simulated_results["vega"]
        )

    if days == 0 or volatility == 0:

        st.warning(
            "Analytical Greeks are undefined at expiration "
            "or when volatility is zero."
        )

    else:

        left, right = st.columns(2)

        with left:

            st.plotly_chart(
                make_chart(
                    list(stock_prices),
                    deltas,
                    "Delta vs Stock Price",
                    "Stock Price ($)",
                    "Delta",
                ),
                use_container_width=True,
            )

        with right:

            st.plotly_chart(
                make_chart(
                    list(stock_prices),
                    gammas,
                    "Gamma vs Stock Price",
                    "Stock Price ($)",
                    "Gamma",
                    "#a78bfa",
                ),
                use_container_width=True,
            )

        left, right = st.columns(2)

        with left:

            st.plotly_chart(
                make_chart(
                    list(stock_prices),
                    vegas,
                    "Vega vs Stock Price",
                    "Stock Price ($)",
                    "Vega",
                    "#22c55e",
                ),
                use_container_width=True,
            )

        with right:

            st.plotly_chart(
                make_chart(
                    list(stock_prices),
                    thetas,
                    "Theta vs Stock Price",
                    "Stock Price ($)",
                    "Theta",
                    "#f97316",
                ),
                use_container_width=True,
            )

    st.info(
        "These charts show theoretical sensitivities "
        "while holding the other model inputs constant."
    )


# ============================================================
# SCENARIO EXPLORER
# ============================================================

elif page == "📈 Scenario Explorer":

    st.title("📈 Scenario Explorer")

    st.caption(
        "Explore theoretical option prices "
        "under hypothetical stock price movements."
    )

    option_type = st.selectbox(
        "Option Type",
        ["Call", "Put"],
    )

    movement_range = st.slider(
        "Stock Price Movement Range (%)",
        min_value=5,
        max_value=80,
        value=30,
        step=5,
    )

    price_changes = np.linspace(
        -movement_range,
        movement_range,
        101,
    )

    simulated_prices = []
    option_values = []

    for change in price_changes:

        shocked_price = stock_price * (
            1.0 + change / 100.0
        )

        simulated_engine = create_engine(
            stock_price=shocked_price,
            strike_price=strike_price,
            days=days,
            interest_rate=interest_rate,
            volatility=volatility,
            dividend_yield=dividend_yield,
        )

        simulated_prices.append(
            shocked_price
        )

        if option_type == "Call":

            option_values.append(
                simulated_engine.call_price()
            )

        else:

            option_values.append(
                simulated_engine.put_price()
            )

    st.plotly_chart(
        make_chart(
            simulated_prices,
            option_values,
            f"{option_type} Price vs Stock Price",
            "Simulated Stock Price ($)",
            "Theoretical Option Price ($)",
            "#22c55e",
        ),
        use_container_width=True,
    )

    st.subheader("Selected Market Scenarios")

    scenario_rows = []

    for change in [
        -20,
        -10,
        -5,
        0,
        5,
        10,
        20,
    ]:

        shocked_price = stock_price * (
            1.0 + change / 100.0
        )

        simulated_engine = create_engine(
            stock_price=shocked_price,
            strike_price=strike_price,
            days=days,
            interest_rate=interest_rate,
            volatility=volatility,
            dividend_yield=dividend_yield,
        )

        if option_type == "Call":

            option_value = (
                simulated_engine.call_price()
            )

        else:

            option_value = (
                simulated_engine.put_price()
            )

        scenario_rows.append(
            {
                "Stock Movement": f"{change:+d}%",
                "Stock Price ($)": round(
                    shocked_price,
                    2,
                ),
                "Option Price ($)": round(
                    option_value,
                    4,
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            scenario_rows
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.info(
        "These scenarios change only the stock price. "
        "Volatility, interest rates, dividends, and "
        "time to expiration remain unchanged."
    )


# ============================================================
# FUTURE MODULE PLACEHOLDERS
# ============================================================

elif page == "🔍 Market Scanner":

    render_market_scanner()


elif page == "💎 Quant Discovery":
    import runpy

    discovery_page = (
        Path(__file__).resolve().parent
        / "pages"
        / "2_Quant_Discovery.py"
    )

    runpy.run_path(str(discovery_page), run_name="__main__")

elif page == "💼 Portfolio Manager":

    render_portfolio_manager()


elif page == "🧠 Forecast Intelligence":

    render_forecast_intelligence()


elif page == "🧠 Strategy Research":

    st.title("🧠 Strategy Research")

    st.info(
        "Coming soon: Historical backtesting, "
        "statistical research, and quantitative models."
    )

    st.write(
        "We will evaluate strategies using "
        "out-of-sample testing and realistic "
        "transaction-cost assumptions."
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Quant Intelligence | Quant Options Engine "
    "— Research and educational use only."
)