"""Quant Discovery | simplified research rankings dashboard."""

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

st.html("""
<style>
.qi-discover-hero {
    background: #101B30;
    border: 1px solid #2A3954;
    border-radius: 16px;
    padding: 1.45rem 1.7rem;
    margin-bottom: 1.1rem;
    font-family: inherit;
}

.qi-discover-label {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    color: #FF78B7;
    font-size: 0.76rem;
    font-weight: 750;
    letter-spacing: 0.13em;
}

.qi-discover-label svg {
    width: 27px;
    height: 27px;
    flex-shrink: 0;
}

.qi-discover-hero h1 {
    color: #FFFFFF;
    font-size: clamp(1.8rem, 3.2vw, 2.7rem);
    line-height: 1.16;
    letter-spacing: -0.035em;
    margin: 1rem 0 0.65rem;
    font-weight: 750;
}

.qi-discover-hero p {
    color: #B5C3DB;
    font-size: 0.96rem;
    line-height: 1.65;
    margin: 0;
    max-width: 680px;
}

.qi-discover-workflow {
    display: flex;
    flex-wrap: wrap;
    gap: 0.8rem 1.5rem;
    border-top: 1px solid #2A3954;
    padding-top: 1rem;
    margin-top: 1.3rem;
}

.qi-discover-step {
    display: flex;
    align-items: center;
    gap: 0.55rem;
    color: #DFE7F5;
    font-size: 0.81rem;
    line-height: 1.4;
}

.qi-discover-step svg {
    width: 19px;
    height: 19px;
    color: #FF78B7;
    flex-shrink: 0;
}

.qi-discover-upcoming {
    color: #8D9CB8;
    font-size: 0.72rem;
}

@media (max-width: 600px) {
    .qi-discover-hero {
        padding: 1.1rem;
    }

    .qi-discover-workflow {
        flex-direction: column;
        gap: 0.8rem;
    }
}
</style>

<section class="qi-discover-hero"
         aria-label="Quant Intelligence Discover">

    <div class="qi-discover-label">
        <svg viewBox="0 0 24 24" fill="none"
             stroke="currentColor" stroke-width="1.8"
             stroke-linecap="round" stroke-linejoin="round"
             aria-hidden="true">
            <circle cx="12" cy="12" r="2"/>
            <path d="M16.24 7.76a6 6 0 0 0-8.48 8.48"/>
            <path d="M19.07 4.93a10 10 0 0 0-14.14 14.14"/>
            <path d="M12 12l7.07-7.07"/>
        </svg>
        QUANT INTELLIGENCE / DISCOVER
    </div>

    <h1>Discover market opportunities.</h1>

    <p>
        Explore quantitative stock rankings and investigate
        what makes a company stand out.
    </p>

    <div class="qi-discover-workflow">

        <div class="qi-discover-step">
            <svg viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round"
                 aria-hidden="true">
                <path d="M4 7V4h3"/>
                <path d="M17 4h3v3"/>
                <path d="M20 17v3h-3"/>
                <path d="M7 20H4v-3"/>
                <circle cx="11" cy="11" r="3"/>
                <path d="m13.5 13.5 2.5 2.5"/>
            </svg>
            Find market activity
        </div>

        <div class="qi-discover-step">
            <svg viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round"
                 aria-hidden="true">
                <path d="M3 3v18h18"/>
                <path d="m7 16 4-5 4 3 5-8"/>
            </svg>
            Review quantitative rankings
        </div>

        <div class="qi-discover-step">
            <svg viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="1.8"
                 stroke-linecap="round" stroke-linejoin="round"
                 aria-hidden="true">
                <path d="M10 2v7.3"/>
                <path d="M14 9.3V2"/>
                <path d="M8.5 2h7"/>
                <path d="M10 9.3 3.2 20a1.5 1.5 0 0 0
                         1.3 2h15a1.5 1.5 0 0 0 1.3-2L14 9.3"/>
                <path d="M8 15h8"/>
            </svg>
            Validate signals
            <span class="qi-discover-upcoming">(Coming later)</span>
        </div>

    </div>
</section>
""")

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
