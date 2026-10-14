"""
Interactive stock portfolio dashboard.

Phase A:
    - Portfolio holdings editor.
    - Portfolio valuation using user-supplied prices.
    - Allocation visualization.
    - Concentration analysis.
    - Holdings CSV export.

Financial calculations are delegated to the existing
app.portfolio.portfolio_manager module.

Historical portfolio performance analysis is available.
Additional risk analytics remain under development.
"""

import io

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.market_data.stock_history import fetch_stock_history
from app.portfolio.portfolio_analytics import calculate_portfolio_values
from app.portfolio.portfolio_manager import (
    StockHolding,
    StockPortfolio,
)

DEFAULT_HOLDINGS = pd.DataFrame(
    {
        "Ticker": ["AAPL", "MSFT", "NVDA"],
        "Shares": [10.0, 5.0, 8.0],
        "Price": [200.0, 400.0, 120.0],
    }
)


def build_portfolio_from_dataframe(
    holdings_data: pd.DataFrame,
) -> StockPortfolio:
    """
    Convert editable holdings data into a validated portfolio.

    The StockHolding and StockPortfolio classes enforce
    the project's existing financial input requirements.
    """

    if not isinstance(holdings_data, pd.DataFrame):
        raise TypeError(
            "Holdings data must be a pandas DataFrame."
        )

    required_columns = {
        "Ticker",
        "Shares",
        "Price",
    }

    if not required_columns.issubset(holdings_data.columns):
        raise ValueError(
            "Holdings must include Ticker, Shares, and Price."
        )

    if holdings_data.empty:
        raise ValueError(
            "Add at least one stock holding."
        )

    holdings = []

    for row_number, (_, row) in enumerate(
        holdings_data.iterrows(),
        start=1,
    ):
        ticker = row["Ticker"]

        if not isinstance(ticker, str):
            raise ValueError(
                f"Row {row_number}: enter a valid ticker."
            )

        ticker = ticker.strip().upper()

        if not ticker:
            raise ValueError(
                f"Row {row_number}: ticker cannot be empty."
            )

        try:
            shares = float(row["Shares"])
            price = float(row["Price"])

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Row {row_number}: shares and price "
                "must be numeric."
            ) from exc

        try:
            holding = StockHolding(
                ticker=ticker,
                shares=shares,
                price=price,
            )

        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Row {row_number}: {exc}"
            ) from exc

        holdings.append(holding)

    return StockPortfolio(holdings)


def create_allocation_chart(
    portfolio: StockPortfolio,
) -> go.Figure:
    """
    Build a donut chart using the portfolio's
    existing allocation calculations.
    """

    allocations = portfolio.allocation_by_ticker()

    figure = go.Figure(
        data=[
            go.Pie(
                labels=list(allocations.keys()),
                values=list(allocations.values()),
                hole=0.62,
                textinfo="label+percent",
                hovertemplate=(
                    "%{label}<br>"
                    "Allocation: %{value:.2f}%"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figure.update_layout(
        title="Portfolio Allocation",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=430,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20,
        ),
        showlegend=True,
    )

    return figure


def render_portfolio_manager() -> None:
    """
    Render the interactive Portfolio Manager page.
    """

    st.title("💼 Portfolio Manager")

    st.markdown(
        "Construct and analyze a stock portfolio using "
        "Quant Intelligence's validated portfolio engine."
    )

    st.info(
        "Phase A — Portfolio Builder. Prices are entered "
        "manually and are not live market quotes. "
        "Historical portfolio performance analysis is available "
        "below. Additional risk analytics remain under development."
    )

    st.subheader("1. Build Your Portfolio")

    st.caption(
        "Enter stock tickers, share quantities, and "
        "prices per share. Add or remove rows as needed."
    )

    if "portfolio_saved_holdings" not in st.session_state:
        st.session_state["portfolio_saved_holdings"] = (
            DEFAULT_HOLDINGS.copy(deep=True)
        )

    edited_holdings = st.data_editor(
        st.session_state["portfolio_saved_holdings"],
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key="stock_portfolio_editor",
        column_config={
            "Ticker": st.column_config.TextColumn(
                "Ticker",
                help="Stock ticker symbol, such as AAPL.",
                required=True,
            ),
            "Shares": st.column_config.NumberColumn(
                "Shares",
                help="Number of shares held.",
                min_value=0.000001,
                format="%.4f",
                required=True,
            ),
            "Price": st.column_config.NumberColumn(
                "Price ($)",
                help="User-supplied price per share.",
                min_value=0.000001,
                format="$%.4f",
                required=True,
            ),
        },
    )

    st.session_state["portfolio_saved_holdings"] = (
        edited_holdings.copy(deep=True)
    )

    try:
        portfolio = build_portfolio_from_dataframe(
            edited_holdings
        )

    except (TypeError, ValueError) as exc:
        st.error(
            f"Unable to build portfolio: {exc}"
        )
        st.stop()

    summary = portfolio.summary()

    st.divider()

    st.subheader("2. Portfolio Overview")

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

    with metric_1:
        st.metric(
            "Portfolio Value",
            f"${summary['total_value']:,.2f}",
        )

    with metric_2:
        st.metric(
            "Holdings",
            f"{summary['holding_count']}",
        )

    with metric_3:
        st.metric(
            "Largest Position",
            str(summary["largest_holding"]),
        )

    with metric_4:
        st.metric(
            "Largest Allocation",
            f"{summary['concentration_pct']:.2f}%",
        )

    st.caption(
        "Portfolio value is calculated from the "
        "share quantities and user-supplied prices above."
    )

    st.divider()

    st.subheader("3. Holdings and Allocations")

    holdings_table = portfolio.to_dataframe()

    chart_column, table_column = st.columns(
        [1, 1],
        gap="large",
    )

    with chart_column:
        st.plotly_chart(
            create_allocation_chart(portfolio),
            use_container_width=True,
        )

    with table_column:
        st.markdown("#### Holdings Breakdown")

        st.dataframe(
            holdings_table,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Price": st.column_config.NumberColumn(
                    "Price ($)",
                    format="$%.2f",
                ),
                "Market Value": st.column_config.NumberColumn(
                    "Market Value ($)",
                    format="$%.2f",
                ),
                "Allocation (%)": st.column_config.NumberColumn(
                    "Allocation (%)",
                    format="%.2f%%",
                ),
            },
        )

        st.markdown(
            f"**Total Portfolio Value:** "
            f"${portfolio.total_value:,.2f}"
        )

        st.markdown(
            f"**Largest Position Weight:** "
            f"{portfolio.concentration():.2f}%"
        )

    st.divider()

    st.subheader("4. Export Portfolio")

    csv_buffer = io.StringIO()

    holdings_table.to_csv(
        csv_buffer,
        index=False,
    )

    st.download_button(
        label="⬇️ Download Holdings CSV",
        data=csv_buffer.getvalue(),
        file_name="quant_intelligence_portfolio.csv",
        mime="text/csv",
        use_container_width=False,
    )

    st.caption(
        "Export includes tickers, shares, "
        "user-supplied prices, market values, "
        "and portfolio allocations."
    )

    st.divider()

    render_historical_performance(portfolio)

    st.divider()

    st.subheader("6. Analysis Methodology")

    with st.expander(
        "How are these portfolio calculations performed?"
    ):
        st.markdown(
            """
            **Portfolio Market Value**

            Each holding's market value is:

            `Shares × Price`

            **Total Portfolio Value**

            The sum of all holding market values.

            **Portfolio Allocation**

            Each holding's percentage of total value:

            `Holding Market Value / Total Portfolio Value × 100`

            **Concentration**

            The largest holding's percentage allocation.

            **Important Limitations**

            - Prices are entered manually.
            - Values are not live brokerage valuations.
            - No trading costs, taxes, or cash balances are included.
            - All prices are assumed to be in USD.
            - Historical performance analysis is available below.
            - Additional portfolio risk analytics are not yet implemented.
            """
        )


@st.cache_data(ttl=900, show_spinner=False)
def load_historical_close(
    ticker: str,
    period: str,
) -> pd.Series:
    """
    Retrieve adjusted historical closing prices.

    Cache results for 15 minutes to reduce repeated
    market-data requests.
    """

    history = fetch_stock_history(ticker, period=period)

    required = {"Date", "Close"}

    if not required.issubset(history.columns):
        raise ValueError(
            f"Historical data for {ticker} is missing "
            "Date or Close."
        )

    dates = pd.to_datetime(
        history["Date"],
        utc=True,
        errors="raise",
    ).dt.tz_localize(None).dt.normalize()

    prices = pd.Series(
        pd.to_numeric(history["Close"], errors="raise").to_numpy(),
        index=pd.DatetimeIndex(dates),
        name=ticker,
        dtype=float,
    )

    if prices.index.has_duplicates:
        raise ValueError(
            f"Duplicate trading dates found for {ticker}."
        )

    return prices.sort_index()


def render_historical_performance(
    portfolio: StockPortfolio,
) -> None:
    """
    Display historical fixed-share portfolio performance
    against a normalized SPY benchmark.
    """

    st.divider()
    st.subheader("5. Historical Portfolio Performance")

    st.caption(
        "Historical results assume the entered share quantities "
        "were held unchanged throughout the selected period. "
        "Prices are adjusted historical closes, not live quotes."
    )

    period = st.selectbox(
        "Historical analysis period",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3,
        key="portfolio_history_period",
    )

    if st.button(
        "Analyze Historical Performance",
        type="primary",
        key="analyze_portfolio_history",
    ):
        st.session_state["portfolio_history_requested"] = True

    if not st.session_state.get(
        "portfolio_history_requested",
        False,
    ):
        st.info(
            "Choose a period and click Analyze Historical "
            "Performance to download market data."
        )
        return

    tickers = [
        holding.ticker
        for holding in portfolio.holdings
    ]

    try:
        with st.spinner("Loading historical market data..."):
            series = {
                ticker: load_historical_close(ticker, period)
                for ticker in tickers
            }

            benchmark = load_historical_close("SPY", period)

            price_frame = pd.concat(
                series.values(),
                axis=1,
            )

            price_frame.columns = list(series.keys())

            missing_rows = int(
                price_frame.isna().any(axis=1).sum()
            )

            values = calculate_portfolio_values(
                portfolio,
                price_frame,
            )

            aligned_benchmark = benchmark.reindex(
                values.index
            )

            # Require complete benchmark coverage for
            # a fair same-date comparison.
            common_dates = aligned_benchmark.dropna().index

            values = values.loc[common_dates]
            aligned_benchmark = aligned_benchmark.loc[common_dates]

            if len(values) < 3:
                raise ValueError(
                    "Insufficient common observations "
                    "between the portfolio and SPY."
                )

            portfolio_growth = (
                values / values.iloc[0] * 100
            )

            benchmark_growth = (
                aligned_benchmark
                / aligned_benchmark.iloc[0]
                * 100
            )

    except (ValueError, TypeError, RuntimeError) as exc:
        st.error(f"Historical analysis unavailable: {exc}")
        return

    portfolio_return = (
        values.iloc[-1] / values.iloc[0] - 1
    ) * 100

    benchmark_return = (
        aligned_benchmark.iloc[-1]
        / aligned_benchmark.iloc[0]
        - 1
    ) * 100

    relative_return = portfolio_return - benchmark_return

    metric_a, metric_b, metric_c = st.columns(3)

    metric_a.metric(
        "Portfolio Return",
        f"{portfolio_return:+.2f}%",
    )

    metric_b.metric(
        "SPY Return",
        f"{benchmark_return:+.2f}%",
    )

    metric_c.metric(
        "Relative Performance",
        f"{relative_return:+.2f} pp",
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=portfolio_growth.index,
            y=portfolio_growth,
            mode="lines",
            name="Your Portfolio",
            line=dict(width=3),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=benchmark_growth.index,
            y=benchmark_growth,
            mode="lines",
            name="SPY",
            line=dict(width=2, dash="dash"),
        )
    )

    figure.update_layout(
        title="Portfolio vs SPY — Growth of 100",
        xaxis_title="Date",
        yaxis_title="Indexed Value (Start = 100)",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=460,
        hovermode="x unified",
    )

    st.plotly_chart(
        figure,
        width="stretch",
    )

    st.caption(
        f"Comparison period: "
        f"{values.index[0].date()} to "
        f"{values.index[-1].date()} "
        f"({len(values)} common price observations)."
    )

    if missing_rows:
        st.warning(
            f"{missing_rows} trading-date rows had missing "
            "prices for one or more holdings and were "
            "excluded from the portfolio calculation."
        )

    if len(values) < 63:
        st.warning(
            "This analysis contains fewer than approximately "
            "three months of trading observations. "
            "Short samples can produce unstable conclusions."
        )

    st.info(
        "Methodology: fixed share quantities, adjusted "
        "historical closing prices, and common trading dates. "
        "This is a hypothetical historical valuation, not "
        "actual account performance. It excludes trading "
        "costs, taxes, cash flows, and execution assumptions."
    )
