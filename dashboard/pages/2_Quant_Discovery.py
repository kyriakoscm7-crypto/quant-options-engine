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

        st.caption(
            "Select a row to investigate its technical ranking. "
            "The highest-ranked company is shown by default."
        )

        display_frame = frame[
            [
                "Rank",
                "Ticker",
                "Company",
                "Research Score",
                "Signal",
            ]
        ].rename(
            columns={"Signal": "Technical Rating"}
        )

        selected_event = st.dataframe(
            display_frame,
            hide_index=True,
            width="stretch",
            height=425,
            on_select="rerun",
            selection_mode="single-row",
            key="qi_discover_interactive_rankings",
            column_config={
                "Rank": st.column_config.NumberColumn(
                    "Rank",
                    width="small",
                ),
                "Ticker": st.column_config.TextColumn(
                    "Ticker",
                    width="small",
                ),
                "Company": st.column_config.TextColumn(
                    "Company",
                    width="medium",
                ),
                "Research Score": st.column_config.ProgressColumn(
                    "Research Score",
                    min_value=0,
                    max_value=100,
                    format="%.1f",
                    help="Descriptive technical research score.",
                ),
                "Technical Rating": st.column_config.TextColumn(
                    "Technical Rating",
                    help="A classification of the technical score, "
                    "not a prediction of future returns.",
                ),
            },
        )

        st.caption(
            f"Ranked {len(rankings)} of {len(companies)} "
            "matching companies. Rankings use historical "
            "market data and are not future-return forecasts."
        )

        selected_rows = selected_event.selection.rows

        selected_index = (
            selected_rows[0]
            if selected_rows
            and 0 <= selected_rows[0] < len(leaderboard)
            else 0
        )

        selected_ticker = leaderboard[selected_index]["Ticker"]

        selected = next(
            item
            for item in rankings
            if item["ticker"] == selected_ticker
        )

        selected_company = company_lookup[selected_ticker]

        st.divider()

        st.markdown(
            "### :primary[:material/analytics:] Research Breakdown"
        )

        st.caption(
            f"{selected_company['name']} ({selected_ticker}) "
            f"| {horizon} research horizon"
        )

        if st.button(
            "Open Full Stock Research",
            icon=":material/open_in_new:",
            type="primary",
            key="qi_discover_open_full_research",
        ):
            st.session_state["_research_ticker_request"] = selected_ticker
            st.session_state["_navigation_request"] = "\U0001F50E Stock Explorer"
            st.rerun()

        with st.container(border=True):
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

            st.markdown("**Underlying Market Measurements**")

            left, right = st.columns(2)

            with left:
                st.metric(
                    "Recent Historical Return",
                    f"{selected['momentum_return']:+.2f}%",
                )

                st.metric(
                    "Moving Average Distance",
                    f"{selected['trend_distance']:+.2f}%",
                )

                st.metric(
                    "Latest Recorded Price",
                    f"${selected['price']:,.2f}",
                )

            with right:
                st.metric(
                    "Annualized Volatility",
                    f"{selected['volatility']:.2f}%",
                )

                st.metric(
                    "Average Daily Volume",
                    f"{selected['average_volume']:,.0f}",
                )

                st.metric(
                    "Overall Research Score",
                    f"{selected['score']:.1f}/100",
                )

            st.caption(
                f"Latest market data: {selected['data_as_of']}"
            )

            st.markdown(
                "#### :primary[:material/query_stats:] "
                "Why This Stock Ranks Here"
            )

            weights = {
                "5 Days": (0.55, 0.30, 0.15),
                "1 Month": (0.45, 0.40, 0.15),
                "1 Year": (0.35, 0.45, 0.20),
            }[horizon]

            factors = [
                ("Momentum", selected["momentum_score"]),
                ("Trend", selected["trend_score"]),
                ("Lower-volatility component", selected["risk_score"]),
            ]

            breakdown = pd.DataFrame(
                [
                    {
                        "Factor": name,
                        "Factor Score": score,
                        "Weight": f"{weight:.0%}",
                        "Contribution": round(score * weight, 2),
                    }
                    for (name, score), weight in zip(
                        factors,
                        weights,
                        strict=True,
                    )
                ]
            )

            st.dataframe(
                breakdown,
                hide_index=True,
                width="stretch",
                column_config={
                    "Factor Score": st.column_config.NumberColumn(
                        "Factor Score",
                        format="%.1f",
                    ),
                    "Contribution": st.column_config.NumberColumn(
                        "Points Added",
                        format="%.2f",
                    ),
                },
            )

            calculated = sum(
                score * weight
                for (_, score), weight in zip(
                    factors,
                    weights,
                    strict=True,
                )
            )

            st.caption(
                f"Weighted contribution: {calculated:.2f}/100. "
                f"Published research score: "
                f"{selected['score']:.1f}/100. "
                "Small differences may reflect rounding."
            )

            st.markdown(
                "#### :primary[:material/shield:] "
                "Research Cautions"
            )

            cautions = []

            if selected["volatility"] >= 100:
                cautions.append(
                    "Annualized historical volatility is at "
                    "least 100%, indicating substantial "
                    "observed price variability."
                )

            if selected["price"] < 5:
                cautions.append(
                    "The latest recorded share price is below "
                    "$5. Investigate price and trading risks."
                )

            approximate_dollar_volume = (
                selected["price"]
                * selected["average_volume"]
            )

            if approximate_dollar_volume < 1_000_000:
                cautions.append(
                    "Approximate daily dollar trading volume "
                    f"is ${approximate_dollar_volume:,.0f}. "
                    "This is a rough liquidity screening proxy, "
                    "not an observed daily dollar-volume series."
                )

            if cautions:
                st.warning(
                    "Screening considerations based on "
                    "illustrative thresholds:\n\n"
                    + "\n\n".join(
                        f"{index}. {note}"
                        for index, note in enumerate(
                            cautions,
                            start=1,
                        )
                    )
                )
            else:
                st.caption(
                    "No caution thresholds triggered by "
                    "this limited screen. Other material "
                    "investment risks may still exist."
                )

            st.caption(
                "A high technical score is not a buy signal "
                "or a validated forecast. The risk component "
                "measures volatility only."
            )

            st.info(
                "These scores summarize historical momentum, "
                "trend, and volatility characteristics. "
                "They have not yet been validated as signals "
                "that predict future returns."
            )


st.divider()

st.caption(
    "Technical research rankings are experimental. "
    "A higher score does not guarantee a higher future return. "
    "Financial fundamentals, news catalysts, liquidity checks, "
    "and historical validation will be added in later phases."
)
