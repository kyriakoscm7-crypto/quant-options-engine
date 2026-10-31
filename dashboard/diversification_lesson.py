"""Guided portfolio stress test using fictional holdings."""

import pandas as pd
import streamlit as st

from app.education.diversification_models import EVENTS, PORTFOLIOS, stress_test


def render_diversification() -> None:
    st.markdown("### 01 · Why the holdings matter")
    st.write(
        "Diversification means spreading your money across investments "
        "instead of relying heavily on one. The goal is not to prevent "
        "every loss: it is to reduce dependence on individual outcomes."
    )
    st.write(
        "Consider two investors with the same CAD 1,000. One puts "
        "70% into Company A. Another spreads the money across "
        "several holdings. What happens when Company A struggles?"
    )

    st.markdown("### 02 · Investigate a market event")
    st.write(
        "Choose a fictional portfolio and a market event. "
        "We'll apply the same event to each portfolio so the "
        "comparison is fair."
    )

    descriptions = {
        "Concentrated": "Most of the money depends on one company.",
        "Evenly spread": "Four companies each receive an equal share.",
        "Broader mix": "Five holdings, with less money in Company A.",
    }
    portfolio = st.radio(
        "Your portfolio",
        list(PORTFOLIOS),
        horizontal=True,
        key="qi_diversification_portfolio_v2",
    )
    st.caption(descriptions[portfolio])

    events = {
        "One company disappoints":
            "Company A declines 30%; the others stay unchanged.",
        "A sector faces pressure":
            "Companies A and B decline together while the others stay flat.",
        "A broad market sell-off":
            "All five holdings decline by different amounts.",
    }
    event = st.radio(
        "What happens in the market?",
        list(EVENTS),
        key="qi_diversification_event_v2",
    )
    st.info(events[event])

    weights = PORTFOLIOS[portfolio]
    shocks = EVENTS[event]
    result = stress_test(weights, shocks)

    st.markdown("### 03 · Examine the results")
    a, b, c = st.columns(3)
    a.metric("Starting value", "CAD 1,000")
    b.metric("After the event", f"CAD {result['end']:,.0f}")
    c.metric("Portfolio change", f"{result['return_pct']:+.1f}%")

    st.markdown("#### What happened to each holding?")
    rows = [
        {
            "Holding": d["holding"],
            "Portfolio weight": f"{d['weight']:.0f}%",
            "Holding return": f"{d['return']:+.0f}%",
            "Impact on portfolio": f"CAD {d['change']:+,.2f}",
        }
        for d in result["details"] if d["weight"] > 0
    ]
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("#### Compare all three portfolios")
    comparisons = {
        name: stress_test(w, shocks)["end"]
        for name, w in PORTFOLIOS.items()
    }
    chart_data = pd.DataFrame(
        {
            "Portfolio": list(comparisons),
            "Value after event (CAD)": list(comparisons.values()),
        }
    ).set_index("Portfolio")
    st.bar_chart(chart_data, y="Value after event (CAD)")

    if event == "One company disappoints":
        st.write(
            "Notice how exposure to Company A determines the loss. "
            "Holding less of one company reduces the impact of that "
            "company's isolated decline."
        )
    elif event == "A sector faces pressure":
        st.write(
            "Two holdings fall together. Spreading money across "
            "companies in the same vulnerable sector may provide "
            "less protection than expected."
        )
    else:
        st.write(
            "Every holding declines in this scenario. Even a broadly "
            "spread portfolio loses value. Diversification does not "
            "eliminate exposure to market-wide events."
        )

    st.markdown("### 04 · Interpret the trade-off")
    st.write(
        "The portfolio's percentage change is the **weighted average** "
        "of its holdings' returns. A holding with a large portfolio "
        "weight contributes more to the total outcome."
    )
    if st.checkbox(
        "Show the calculation for my portfolio",
        key="qi_diversification_math_v2",
    ):
        terms = [
            f"({d['weight']:.0f}% × {d['return']:+.0f}%)"
            for d in result["details"] if d["weight"] > 0
        ]
        st.write(" + ".join(terms))
        st.write(
            f"Weighted portfolio return: **{result['return_pct']:+.2f}%**"
        )

    with st.expander("What this stress test cannot tell you"):
        st.write(
            "These are deliberately invented, one-period returns. "
            "The model assumes holdings start at fixed weights and "
            "ignores trading costs, taxes and rebalancing. "
            "It does not estimate future losses, volatility, "
            "correlations, or an optimal portfolio."
        )
        st.write(
            "Different company names do not automatically mean "
            "independent risks. Companies can respond to the same "
            "economic event, and even diversified portfolios can "
            "experience substantial losses."
        )

    st.markdown("### 05 · Apply what you learned")
    answer = st.radio(
        "Your portfolio owns shares in 20 banks. Which statement is best?",
        [
            "Owning 20 stocks eliminates the risk of loss.",
            "The portfolio may still be concentrated in banking risks.",
            "The portfolio must outperform one bank stock.",
        ],
        index=None,
        key="qi_diversification_question_v2",
    )
    if answer is not None:
        if answer.startswith("The portfolio may"):
            st.success(
                "Correct. More holdings can reduce dependence on "
                "individual companies, but sector-wide risks remain."
            )
        else:
            st.info(
                "Think about the risks those companies share. "
                "Many holdings in one sector can still be vulnerable "
                "to the same economic event."
            )

    st.caption(
        "Every company, portfolio and market event here is fictional. "
        "This is an educational stress test, not financial advice "
        "or a prediction of market performance."
    )
