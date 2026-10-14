"""Quant Discovery — simplified research rankings dashboard."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.discovery.database import (  # noqa: E402
    database_summary,
    initialize_database,
    search_companies,
)
from app.discovery.ranking_engine import (  # noqa: E402
    rank_companies,
)


@st.cache_data(ttl=1800, show_spinner=False)
def cached_rankings(tickers, horizon):
    return rank_companies(list(tickers), horizon)


initialize_database()

st.title("💎 Quant Discovery")

st.caption(
    "Find technically strong stocks across different investment horizons."
)

summary = database_summary()

st.markdown(
    f"**{summary['companies']} companies tracked**"
    " · Rankings use daily market data"
)

st.divider()

horizon = st.segmented_control(
    "Investment Horizon",
    options=["5 Days", "1 Month", "1 Year"],
    default="5 Days",
    selection_mode="single",
)

if horizon is None:
    horizon = "5 Days"

filter_col1, filter_col2, filter_col3 = st.columns(
    [1.2, 1, 1.5]
)

with filter_col1:
    company_size = st.selectbox(
        "Company Size",
        [
            "All Companies",
            "Mega Cap",
            "Large Cap",
            "Mid Cap",
            "Small Cap",
            "Micro Cap",
            "Nano Cap",
            "Unknown",
        ],
    )

with filter_col2:
    stock_type = st.selectbox(
        "Stock Type",
        ["All Stocks", "Penny Stocks"],
    )

with filter_col3:
    search = st.text_input(
        "Search",
        placeholder="Ticker or company name",
    )

companies = search_companies(
    market_cap_category=(
        None
        if company_size == "All Companies"
        else company_size
    ),
    penny_stocks_only=stock_type == "Penny Stocks",
    limit=1000,
)

if search.strip():
    term = search.strip().lower()

    companies = [
        company
        for company in companies
        if term in (company["ticker"] or "").lower()
        or term in (company["name"] or "").lower()
    ]

st.subheader(f"Top Ranked · {horizon}")

if not companies:
    st.info("No companies match your filters.")

else:
    tickers = tuple(
        company["ticker"]
        for company in companies
    )

    with st.spinner("Analyzing historical market data..."):
        rankings = cached_rankings(tickers, horizon)

    company_lookup = {
        company["ticker"]: company
        for company in companies
    }

    if not rankings:
        st.warning(
            "No rankings available. Market data may be "
            "temporarily unavailable or insufficient."
        )

    else:
        leaderboard = []

        for item in rankings:
            company = company_lookup[item["ticker"]]

            if item["score"] >= 70:
                signal = "Strong"
            elif item["score"] >= 55:
                signal = "Positive"
            elif item["score"] >= 40:
                signal = "Mixed"
            else:
                signal = "Weak"

            leaderboard.append(
                {
                    "Rank": item["rank"],
                    "Ticker": item["ticker"],
                    "Company": company["name"],
                    "Research Score": item["score"],
                    "Signal": signal,
                    "Recent Return (%)": item[
                        "momentum_return"
                    ],
                    "Price ($)": item["price"],
                }
            )

        frame = pd.DataFrame(leaderboard)

        st.dataframe(
            frame,
            hide_index=True,
            width="stretch",
            column_config={
                "Research Score": st.column_config.ProgressColumn(
                    "Research Score",
                    min_value=0,
                    max_value=100,
                    format="%.1f",
                ),
                "Recent Return (%)": (
                    st.column_config.NumberColumn(
                        "Recent Return (%)",
                        format="%+.2f%%",
                    )
                ),
                "Price ($)": st.column_config.NumberColumn(
                    "Price ($)",
                    format="$%.2f",
                ),
            },
        )

        st.caption(
            f"Ranked {len(rankings)} of {len(companies)} "
            "matching companies. Recent Return is historical "
            "performance, not a future return forecast."
        )

        with st.expander("Advanced Analysis"):
            selected_ticker = st.selectbox(
                "Inspect Company",
                [item["ticker"] for item in rankings],
            )

            selected = next(
                item
                for item in rankings
                if item["ticker"] == selected_ticker
            )

            a, b, c = st.columns(3)

            a.metric(
                "Momentum Score",
                selected["momentum_score"],
            )

            b.metric(
                "Trend Score",
                selected["trend_score"],
            )

            c.metric(
                "Risk Score",
                selected["risk_score"],
            )

            st.write(
                f"**Historical momentum:** "
                f"{selected['momentum_return']:+.2f}%"
            )

            st.write(
                f"**Distance from moving average:** "
                f"{selected['trend_distance']:+.2f}%"
            )

            st.write(
                f"**Annualized volatility:** "
                f"{selected['volatility']:.2f}%"
            )

            st.write(
                f"**Average daily volume:** "
                f"{selected['average_volume']:,}"
            )

            st.write(
                f"**Latest market data:** "
                f"{selected['data_as_of']}"
            )

            st.info(
                "Research scores use momentum, trend, and "
                "historical volatility. They are not validated "
                "predictions of future returns."
            )

st.divider()

st.caption(
    "Technical research rankings are experimental. "
    "A higher score does not guarantee a higher future return. "
    "Financial fundamentals, news catalysts, liquidity checks, "
    "and historical validation will be added in later phases."
)
