"""
Interactive Market Scanner page for Quant Intelligence.

Features:
- Scan up to 20 stocks.
- Calculate historical momentum and risk metrics.
- Rank stocks using transparent quantitative factors.
- Display an interactive leaderboard.
- Visualize quantitative scores.
- Export results to CSV.

Historical results are descriptive, not predictive.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.market_data.market_scanner import (
    MAX_SCAN_TICKERS,
    normalize_tickers,
    scan_market,
)
from app.market_data.stock_ranking import (
    DEFAULT_RANKING_FACTORS,
    rank_stocks,
)

DEFAULT_TICKERS = (
    "AAPL, MSFT, NVDA, AMZN, GOOGL, META, TSLA"
)

AVAILABLE_PERIODS = [
    "3mo",
    "6mo",
    "1y",
    "2y",
    "5y",
]


@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def cached_market_scan(
    tickers: tuple[str, ...],
    period: str,
) -> pd.DataFrame:
    """
    Cache market scans for 15 minutes.

    Reduces repeated requests to Yahoo Finance when
    users interact with the dashboard.
    """

    return scan_market(
        tickers=tickers,
        period=period,
    )


def create_score_chart(
    ranked: pd.DataFrame,
) -> go.Figure:
    """
    Create a horizontal chart of quantitative scores.
    """

    chart_data = ranked.dropna(
        subset=["Quant Score"]
    ).copy()

    chart_data = chart_data.sort_values(
        "Quant Score",
        ascending=True,
    )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=chart_data["Quant Score"],
            y=chart_data["Ticker"],
            orientation="h",
            marker=dict(
                color=chart_data["Quant Score"],
                colorscale="Blues",
                cmin=0,
                cmax=100,
            ),
            text=chart_data["Quant Score"].round(1),
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Quant Score: %{x:.2f}"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title="Quantitative Stock Rankings",
        template="plotly_dark",
        paper_bgcolor="#080d18",
        plot_bgcolor="#080d18",
        font=dict(
            color="#e5e7eb",
        ),
        xaxis=dict(
            title="Quant Score",
            range=[0, 110],
            gridcolor="#243247",
        ),
        yaxis=dict(
            title="",
        ),
        height=max(
            350,
            len(chart_data) * 48 + 120,
        ),
        margin=dict(
            l=40,
            r=40,
            t=60,
            b=40,
        ),
    )

    return figure


def render_market_scanner() -> None:
    """
    Render the complete interactive Market Scanner page.
    """

    st.title("🔍 Market Scanner")

    st.markdown(
        "Analyze multiple stocks using historical momentum, "
        "risk metrics, benchmark-relative performance, "
        "and transparent quantitative rankings."
    )

    st.info(
        "Quant Scores compare historical characteristics "
        "within your selected stocks. They are not "
        "predictions or investment recommendations."
    )

    st.divider()

    # --------------------------------------------------------
    # SCANNER INPUTS
    # --------------------------------------------------------

    st.subheader("Scanner Configuration")

    left, right = st.columns(
        [3, 1]
    )

    with left:

        ticker_input = st.text_area(
            "Stock Tickers",
            value=DEFAULT_TICKERS,
            height=100,
            help=(
                "Enter comma-separated stock symbols. "
                f"Maximum: {MAX_SCAN_TICKERS} unique tickers."
            ),
        )

    with right:

        period = st.selectbox(
            "Historical Period",
            AVAILABLE_PERIODS,
            index=2,
        )

        st.caption(
            "Benchmark: SPY"
        )

    run_scan = st.button(
        "🚀 Run Market Scan",
        type="primary",
        use_container_width=True,
    )

    # --------------------------------------------------------
    # EXECUTE SCAN
    # --------------------------------------------------------

    if run_scan:

        try:

            symbols = normalize_tickers(
                ticker_input
            )

        except ValueError as exc:

            st.error(
                f"Invalid ticker input: {exc}"
            )

            return

        with st.spinner(
            f"Analyzing {len(symbols)} stocks..."
        ):

            try:

                scan_results = cached_market_scan(
                    tuple(symbols),
                    period,
                )

                ranked_results = rank_stocks(
                    scan_results
                )

            except (ValueError, RuntimeError) as exc:

                st.error(
                    f"Market scan failed: {exc}"
                )

                return

        st.session_state[
            "market_scanner_results"
        ] = ranked_results

        st.session_state[
            "market_scanner_period"
        ] = period

        st.session_state[
            "market_scanner_symbols"
        ] = symbols

    # --------------------------------------------------------
    # DISPLAY RESULTS
    # --------------------------------------------------------

    if "market_scanner_results" not in st.session_state:

        st.info(
            "Enter your stock symbols and click "
            "'Run Market Scan' to generate a leaderboard."
        )

        return

    ranked = st.session_state[
        "market_scanner_results"
    ]

    selected_period = st.session_state.get(
        "market_scanner_period",
        period,
    )

    selected_symbols = st.session_state.get(
        "market_scanner_symbols",
        [],
    )

    st.divider()

    st.subheader(
        "Quantitative Market Overview"
    )

    ranked_stocks = ranked[
        ranked["Ranking Status"] == "Ranked"
    ]

    successful_scans = ranked[
        ranked["Status"].str.startswith("OK")
    ]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Stocks Requested",
        len(selected_symbols),
    )

    col2.metric(
        "Successful Scans",
        len(successful_scans),
    )

    col3.metric(
        "Stocks Ranked",
        len(ranked_stocks),
    )

    col4.metric(
        "Analysis Period",
        selected_period,
    )

    # --------------------------------------------------------
    # LEADERBOARD
    # --------------------------------------------------------

    st.subheader(
        "🏆 Quantitative Stock Leaderboard"
    )

    leaderboard_columns = [
        "Quant Rank",
        "Ticker",
        "Quant Score",
        "Latest Close",
        "Total Return (%)",
        "1M Momentum (%)",
        "3M Momentum (%)",
        "Relative to SPY (%)",
        "Annualized Volatility (%)",
        "Maximum Drawdown (%)",
        "Ranking Status",
    ]

    leaderboard = ranked[
        leaderboard_columns
    ].copy()

    st.dataframe(
        leaderboard,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Quant Score": st.column_config.NumberColumn(
                "Quant Score",
                format="%.2f",
            ),
            "Total Return (%)": st.column_config.NumberColumn(
                "Total Return (%)",
                format="%.2f%%",
            ),
            "1M Momentum (%)": st.column_config.NumberColumn(
                "1M Momentum (%)",
                format="%.2f%%",
            ),
            "3M Momentum (%)": st.column_config.NumberColumn(
                "3M Momentum (%)",
                format="%.2f%%",
            ),
            "Relative to SPY (%)": st.column_config.NumberColumn(
                "Relative to SPY (%)",
                format="%.2f pp",
            ),
            "Annualized Volatility (%)": st.column_config.NumberColumn(
                "Annualized Volatility (%)",
                format="%.2f%%",
            ),
            "Maximum Drawdown (%)": st.column_config.NumberColumn(
                "Maximum Drawdown (%)",
                format="%.2f%%",
            ),
        },
    )

    # --------------------------------------------------------
    # QUANT SCORE CHART
    # --------------------------------------------------------

    if not ranked_stocks.empty:

        st.subheader(
            "📊 Quant Score Comparison"
        )

        figure = create_score_chart(
            ranked
        )

        st.plotly_chart(
            figure,
            use_container_width=True,
        )

        best_stock = ranked_stocks.iloc[0]

        st.success(
            f"Highest-ranked stock in this scan: "
            f"{best_stock['Ticker']} "
            f"(Quant Score: "
            f"{best_stock['Quant Score']:.2f}/100)."
        )

    else:

        st.warning(
            "No stocks had sufficient valid data "
            "to receive a quantitative ranking."
        )

    # --------------------------------------------------------
    # ERRORS AND WARNINGS
    # --------------------------------------------------------

    unsuccessful = ranked[
        ranked["Status"] != "OK"
    ]

    if not unsuccessful.empty:

        with st.expander(
            "⚠️ Scanner Warnings and Data Issues"
        ):

            st.dataframe(
                unsuccessful[
                    [
                        "Ticker",
                        "Status",
                        "Ranking Status",
                    ]
                ],
                hide_index=True,
                use_container_width=True,
            )

    # --------------------------------------------------------
    # RANKING METHODOLOGY
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "🧮 Ranking Methodology"
    )

    st.markdown(
        "Each eligible stock receives a percentile-based "
        "score for five historical factors. "
        "These scores are combined using fixed weights."
    )

    methodology_rows = []

    for factor in DEFAULT_RANKING_FACTORS:

        methodology_rows.append(
            {
                "Factor": factor.column,
                "Weight (%)": factor.weight * 100,
                "Preferred Direction": (
                    "Higher"
                    if factor.higher_is_better
                    else "Lower"
                ),
            }
        )

    st.dataframe(
        pd.DataFrame(
            methodology_rows
        ),
        hide_index=True,
        use_container_width=True,
    )

    st.caption(
        "Rankings are relative to the selected stock universe. "
        "A different group of stocks can produce different scores. "
        "The factor weights are research assumptions and "
        "have not been optimized or validated for forecasting."
    )

    # --------------------------------------------------------
    # CSV EXPORT
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "📥 Export Scanner Results"
    )

    csv_data = ranked.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="Download Market Scanner CSV",
        data=csv_data,
        file_name=(
            f"quant_intelligence_market_scan_"
            f"{selected_period}.csv"
        ),
        mime="text/csv",
        use_container_width=True,
    )

    st.caption(
        "Data is sourced from Yahoo Finance through yfinance. "
        "Historical statistics describe past observations "
        "and do not guarantee future performance."
    )