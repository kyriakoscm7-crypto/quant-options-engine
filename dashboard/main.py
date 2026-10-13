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

# Resolve the repository root so the dashboard can import
# existing modules from the project's app/ package.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.market_data.stock_history import (  # noqa: E402
    calculate_normalized_performance,
    calculate_stock_statistics,
    fetch_stock_history,
    validate_ticker,
)
from app.pricing.black_scholes import BlackScholes  # noqa: E402

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

    # Normalize to calendar dates so timezone representations
    # do not prevent matching daily observations.
    stock["Date"] = pd.to_datetime(
        stock["Date"],
        utc=True,
    ).dt.date

    benchmark["Date"] = pd.to_datetime(
        benchmark["Date"],
        utc=True,
    ).dt.date

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

    st.divider()

    page = st.radio(
        "Navigation",
        [
            "🏠 Overview",
            "🔎 Stock Explorer",
            "💰 Options Lab",
            "📊 Greeks Analysis",
            "📈 Scenario Explorer",
            "🔍 Market Scanner",
            "💼 Portfolio Manager",
            "🧠 Strategy Research",
        ],
        label_visibility="collapsed",
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

    st.title("Quant Intelligence")

    st.markdown(
        '<p class="section-caption">'
        "Quantitative research, derivatives analytics, "
        "and portfolio intelligence."
        "</p>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.subheader("Platform Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Pricing Models", "1", "Black-Scholes")

    with col2:
        st.metric("API Endpoints", "10")

    with col3:
        st.metric("Automated Tests", "638")

    with col4:
        st.metric("Test Coverage", "93%")

    st.markdown("### Research Modules")

    left, middle, right = st.columns(3)

    with left:
        st.markdown(
            """
            <div class="dashboard-card">
                <h3>🔎 Stock Explorer</h3>
                <p>
                    Research historical stock prices,
                    returns, volatility, and performance.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with middle:
        st.markdown(
            """
            <div class="dashboard-card">
                <h3>💰 Options Lab</h3>
                <p>
                    Price European call and put options
                    and explore analytical Greeks.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            """
            <div class="dashboard-card">
                <h3>📈 Scenario Explorer</h3>
                <p>
                    Explore theoretical option values
                    under hypothetical market changes.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Development Roadmap")

    st.info(
        "Upcoming: Market Scanner, Portfolio Manager, "
        "Historical Backtesting, Machine Learning, "
        "and Quantitative Strategy Research."
    )

    st.markdown("### Current Capabilities")

    st.write(
        "The platform supports historical stock research, "
        "European option pricing, analytical Greeks, "
        "implied volatility, vectorized calculations, "
        "portfolio risk aggregation, and scenario analysis."
    )


# ============================================================
# STOCK EXPLORER
# ============================================================

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
                "1mo",
                "3mo",
                "6mo",
                "1y",
                "2y",
                "5y",
                "10y",
                "max",
            ],
            index=3,
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
            "Latest Daily Change",
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
            "Annualized Volatility",
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
            "Daily Observations",
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

    st.caption(
        "Adjusted historical daily prices. "
        "The latest observation may be incomplete."
    )

    display_history = history.copy()

    display_history["Date"] = pd.to_datetime(
        display_history["Date"],
        utc=True,
    ).dt.strftime("%Y-%m-%d")

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

    st.title("💰 Options Pricing Lab")

    st.caption(
        "European option pricing using the "
        "Black-Scholes-Merton model."
    )

    st.info(
        "Adjust the parameters in the sidebar. "
        "Results update automatically."
    )

    call_col, put_col = st.columns(2)

    with call_col:

        st.metric(
            "European Call Price",
            f"${results['call_price']:,.4f}",
        )

    with put_col:

        st.metric(
            "European Put Price",
            f"${results['put_price']:,.4f}",
        )

    st.divider()

    st.subheader("Option Greeks")

    greek_data = pd.DataFrame(
        {
            "Greek": [
                "Delta",
                "Gamma",
                "Vega",
                "Theta",
                "Rho",
            ],
            "Call": [
                results["call_delta"],
                results["gamma"],
                results["vega"],
                results["call_theta"],
                results["call_rho"],
            ],
            "Put": [
                results["put_delta"],
                results["gamma"],
                results["vega"],
                results["put_theta"],
                results["put_rho"],
            ],
        }
    )

    st.dataframe(
        greek_data,
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### Understanding the Greeks")

    with st.expander("Delta — Stock Price Sensitivity"):

        st.write(
            "Estimates how much the option price changes "
            "when the underlying stock moves by $1."
        )

    with st.expander("Gamma — Delta Sensitivity"):

        st.write(
            "Measures how quickly Delta changes "
            "as the stock price moves."
        )

    with st.expander("Vega — Volatility Sensitivity"):

        st.write(
            "Estimates the option price change for a "
            "1 percentage-point increase in volatility."
        )

    with st.expander("Theta — Time Decay"):

        st.write(
            "Measures the approximate option price change "
            "from one calendar day passing."
        )

    with st.expander("Rho — Interest Rate Sensitivity"):

        st.write(
            "Estimates the option price change for a "
            "1 percentage-point increase in interest rates."
        )

    st.warning(
        "Black-Scholes assumes European-style exercise "
        "and simplified market conditions. Theoretical "
        "prices are not guaranteed market prices."
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

    st.title("🔍 Market Scanner")

    st.info(
        "Coming soon: Search supported stocks for "
        "momentum, volatility, and other quantitative "
        "research signals."
    )

    st.write(
        "Signals will require historical validation "
        "before being treated as actionable research."
    )


elif page == "💼 Portfolio Manager":

    st.title("💼 Portfolio Manager")

    st.info(
        "Coming soon: Track stock holdings and "
        "analyze portfolio performance and risk."
    )

    st.write(
        "Our existing backend already supports "
        "option portfolio valuation and scenario analysis."
    )


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