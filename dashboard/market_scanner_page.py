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
from app.market_data.market_signal_labels import classify_market_signal
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
    # --------------------------------------------------------
    # BEGINNER-FRIENDLY STOCK DISCOVERY
    # --------------------------------------------------------

    st.subheader("🧭 Beginner-Friendly Stock Discovery")

    st.caption(
        "Quickly understand historical price momentum. "
        "Green and red describe observed trends, "
        "not buy or sell recommendations."
    )

    discovery = ranked.copy()

    signal_results = discovery.apply(
        lambda row: classify_market_signal(
            row["1M Momentum (%)"],
            row["3M Momentum (%)"],
            row["Ranking Status"],
        ),
        axis=1,
    )

    discovery["Market Signal"] = signal_results.map(
        lambda result: result[0]
    )

    discovery["Explanation"] = signal_results.map(
        lambda result: result[1]
    )

    discovery_columns = [
        "Ticker",
        "Market Signal",
        "Explanation",
    ]

    st.dataframe(
        discovery[discovery_columns],
        hide_index=True,
        use_container_width=True,
    )

    st.divider()

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
    # GAP & VOLUME OPPORTUNITY DISCOVERY
    # --------------------------------------------------------

    st.divider()

    st.subheader("🔎 Gap & Volume Opportunity Discovery")

    st.caption(
        "Find unusual opening gaps and trading-volume activity "
        "among the stocks in your selected scan. "
        "These are descriptive signals, not forecasts."
    )

    gap_columns = [
        "Ticker",
        "Quant Score",
        "Opening Gap (%)",
        "Relative Volume",
        "Gap Z-Score",
        "Gap Signal Date",
        "Gap Status",
    ]

    missing_columns = [
        column
        for column in gap_columns
        if column not in ranked.columns
    ]

    if missing_columns:
        st.warning(
            "Gap Intelligence results are not available in "
            "this scan. Run a new scan to refresh the data."
        )

    else:
        gap_results = ranked[gap_columns].copy()

        available = gap_results[
            gap_results["Gap Status"] == "OK"
        ].copy()

        filter_a, filter_b, filter_c = st.columns(3)

        with filter_a:
            gap_direction = st.selectbox(
                "Gap Direction",
                ["All", "Gap Up", "Gap Down"],
                key="gap_filter_direction",
            )

        with filter_b:
            minimum_gap = st.number_input(
                "Minimum Absolute Gap (%)",
                min_value=0.0,
                value=0.0,
                step=0.5,
                key="gap_filter_minimum",
            )

        with filter_c:
            minimum_volume = st.number_input(
                "Minimum Relative Volume (×)",
                min_value=0.0,
                value=0.0,
                step=0.5,
                key="gap_filter_volume",
            )

        filter_d, filter_e = st.columns(2)

        with filter_d:
            minimum_z_score = st.number_input(
                "Minimum Absolute Gap Z-Score",
                min_value=0.0,
                value=0.0,
                step=0.5,
                key="gap_filter_z_score",
            )

        with filter_e:
            sort_method = st.selectbox(
                "Sort Opportunities By",
                [
                    "Largest Absolute Gap",
                    "Highest Relative Volume",
                    "Most Unusual Gap",
                    "Highest Quant Score",
                ],
                key="gap_sort_method",
            )

        numeric_columns = [
            "Opening Gap (%)",
            "Relative Volume",
            "Gap Z-Score",
            "Quant Score",
        ]

        for column in numeric_columns:
            available[column] = pd.to_numeric(
                available[column],
                errors="coerce",
            )

        available = available.dropna(
            subset=[
                "Opening Gap (%)",
                "Relative Volume",
            ]
        )

        if gap_direction == "Gap Up":
            available = available[
                available["Opening Gap (%)"] > 0
            ]

        elif gap_direction == "Gap Down":
            available = available[
                available["Opening Gap (%)"] < 0
            ]

        available = available[
            available["Opening Gap (%)"].abs()
            >= minimum_gap
        ]

        available = available[
            available["Relative Volume"]
            >= minimum_volume
        ]

        if minimum_z_score > 0:
            available = available[
                available["Gap Z-Score"].abs()
                >= minimum_z_score
            ]

        if sort_method == "Largest Absolute Gap":
            available["_Sort"] = (
                available["Opening Gap (%)"].abs()
            )

        elif sort_method == "Highest Relative Volume":
            available["_Sort"] = available["Relative Volume"]

        elif sort_method == "Most Unusual Gap":
            available["_Sort"] = (
                available["Gap Z-Score"].abs()
            )

        else:
            available["_Sort"] = available["Quant Score"]

        available = available.sort_values(
            "_Sort",
            ascending=False,
            na_position="last",
        ).drop(columns="_Sort")

        st.metric(
            "Matching Opportunities",
            len(available),
        )

        if available.empty:
            st.info(
                "No stocks match the selected gap and "
                "volume filters. Try reducing the thresholds."
            )

        else:
            st.dataframe(
                available,
                hide_index=True,
                width="stretch",
                column_config={
                    "Quant Score": st.column_config.NumberColumn(
                        "Quant Score",
                        format="%.2f",
                    ),
                    "Opening Gap (%)": st.column_config.NumberColumn(
                        "Opening Gap (%)",
                        format="%+.2f%%",
                    ),
                    "Relative Volume": st.column_config.NumberColumn(
                        "Relative Volume",
                        format="%.2f×",
                    ),
                    "Gap Z-Score": st.column_config.NumberColumn(
                        "Gap Z-Score",
                        format="%+.2f",
                    ),
                },
            )

        unavailable_count = int(
            (gap_results["Gap Status"] != "OK").sum()
        )

        if unavailable_count:
            st.warning(
                f"Gap analysis was unavailable for "
                f"{unavailable_count} stock(s). "
                "These stocks were excluded from the "
                "opportunity filters."
            )

        st.caption(
            "Gap statistics currently exclude the newest "
            "downloaded session as a precaution against "
            "incomplete daily data. Check Gap Signal Date "
            "before interpreting results. Quant Scores are "
            "unchanged and are not probabilities."
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