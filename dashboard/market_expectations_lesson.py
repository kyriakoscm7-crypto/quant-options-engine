"""Market expectations lab with fictional EPS and valuation inputs."""

import streamlit as st

from app.education.market_expectations import (
    BASELINE_FUTURE_EPS,
    BASELINE_MULTIPLE,
    SCENARIOS,
    valuation_case,
)


def render_market_expectations() -> None:
    st.markdown("### 01 · Why good news isn't always enough")
    st.write(
        "Stocks respond to what investors learn relative to what "
        "they already expected. A profitable, growing company can "
        "still disappoint investors if its future looks less "
        "promising than previously assumed."
    )
    st.write(
        "Imagine a fictional company whose shares were valued "
        "using expected annual earnings of **CAD 5 per share** "
        "and an illustrative price-to-earnings multiple of **20**. "
        "That produces an implied value of **CAD 100 per share**."
    )

    st.markdown("### 02 · Investigate an earnings announcement")
    scenario = st.radio(
        "What does the company announce?",
        list(SCENARIOS),
        key="qi_expectations_scenario_v1",
    )
    selected = SCENARIOS[scenario]
    st.info(selected["explanation"])

    old_future_eps = BASELINE_FUTURE_EPS
    old_multiple = BASELINE_MULTIPLE
    new_future_eps = selected["future_eps"]
    new_multiple = selected["new_multiple"]
    expected_quarter_eps = selected["expected_quarter_eps"]
    reported_eps = selected["reported_eps"]

    with st.expander("Customize valuation assumptions (optional)"):
        st.write(
            "Forward EPS means estimated earnings per share over "
            "a future period. A P/E multiple describes how much "
            "investors are assumed to pay for each dollar of earnings."
        )
        custom = st.checkbox(
            "Change the fictional assumptions",
            key="qi_expectations_custom_v1",
        )
        if custom:
            a, b = st.columns(2)
            with a:
                new_future_eps = st.slider(
                    "New estimated annual EPS (CAD)",
                    1.0, 10.0, float(new_future_eps), 0.25,
                    key=f"qi_expectations_eps_{scenario}",
                )
            with b:
                new_multiple = st.slider(
                    "New hypothetical P/E multiple",
                    5.0, 35.0, float(new_multiple), 1.0,
                    key=f"qi_expectations_pe_{scenario}",
                )

    result = valuation_case(
        expected_quarter_eps,
        reported_eps,
        old_future_eps,
        old_multiple,
        new_future_eps,
        new_multiple,
    )

    st.markdown("### 03 · Compare the headline and the valuation")
    a, b, c = st.columns(3)
    a.metric(
        "Quarterly EPS surprise",
        f"{result['quarter_surprise_pct']:+.1f}%",
    )
    b.metric(
        "Before: implied value",
        f"CAD {result['before']:,.2f}",
    )
    c.metric(
        "After: implied value",
        f"CAD {result['after']:,.2f}",
        f"{result['implied_change_pct']:+.1f}%",
    )

    st.bar_chart(
        {
            "Before announcement": result["before"],
            "After announcement": result["after"],
        },
        horizontal=True,
    )

    st.write(
        f"**Before:** CAD {old_future_eps:.2f} estimated annual EPS "
        f"× {old_multiple:.0f} assumed P/E "
        f"= CAD {result['before']:.2f}."
    )
    st.write(
        f"**After:** CAD {new_future_eps:.2f} estimated annual EPS "
        f"× {new_multiple:.0f} assumed P/E "
        f"= CAD {result['after']:.2f}."
    )

    if result["implied_change_pct"] < -0.01:
        st.warning(
            "Despite the reported earnings result, the new "
            "assumptions imply a lower valuation. This illustrates "
            "why an earnings beat doesn't guarantee a price increase."
        )
    elif result["implied_change_pct"] > 0.01:
        st.success(
            "The revised assumptions imply a higher valuation. "
            "That doesn't guarantee shares will trade there."
        )
    else:
        st.info(
            "The implied valuation is unchanged. Good reported "
            "results may already be reflected in expectations."
        )

    st.markdown("### 04 · Interpret what changed")
    st.write(
        f"Estimated future EPS changed by "
        f"**{result['earnings_effect_pct']:+.1f}%**, "
        f"while the assumed P/E multiple changed by "
        f"**{result['multiple_effect_pct']:+.1f}%**."
    )
    st.write(
        "Both affect the implied value. The combined percentage "
        "change is not simply their sum because the two factors "
        "are multiplied together."
    )

    with st.expander("Why this isn't a stock-price prediction"):
        st.write(
            "The model uses one forward earnings estimate and one "
            "assumed P/E multiple, with no dividends, debt, share "
            "dilution or explicit cash-flow valuation. It excludes "
            "investor positioning, liquidity and other news. "
            "Actual market prices are determined by trading and "
            "may behave differently from the illustrated values."
        )
        st.write(
            "Quarterly reported EPS and forward annual EPS refer to "
            "different periods. A quarterly beat doesn't determine "
            "future annual profitability on its own."
        )

    st.markdown("### 05 · Apply what you learned")
    answer = st.radio(
        "A company beats quarterly EPS estimates but lowers its "
        "future profit forecast. What is the strongest conclusion?",
        [
            "Its share price must rise because EPS beat expectations.",
            "Its valuation could fall if future expectations worsen.",
            "Its share price must fall by exactly the EPS surprise.",
        ],
        index=None,
        key="qi_expectations_question_v1",
    )
    if answer:
        if answer.startswith("Its valuation could"):
            st.success(
                "Correct. Forward expectations can matter more "
                "than a single backward-looking earnings result."
            )
        else:
            st.info(
                "Reconsider how future profitability and valuation "
                "assumptions interact. No single EPS result "
                "determines a market price."
            )

    st.caption(
        "All company figures, earnings announcements and valuation "
        "multiples are fictional. Educational analysis only; "
        "not investment advice or a return forecast."
    )
