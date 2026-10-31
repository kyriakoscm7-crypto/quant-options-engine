"""Guided inflation lesson backed by tested financial models."""

import streamlit as st

from app.education.inflation_models import (
    purchasing_power,
    real_return_pct,
)


def render_inflation_lesson() -> None:
    st.markdown("### 01 · Why does your money buy less?")
    st.write(
        "**Inflation** means the overall price level of goods and services "
        "is increasing. When prices rise faster than your income or savings, "
        "the same amount of money buys fewer things."
    )

    with st.container(border=True):
        st.markdown("#### Three ideas worth understanding")
        st.markdown("**Price level**")
        st.write(
            "The average level of prices across the economy. "
            "Not every product changes price at the same rate."
        )
        st.markdown("**Inflation rate**")
        st.write(
            "The percentage change in a price index over a period. "
            "For example, 3% annual inflation means the measured "
            "price level is about 3% higher than a year earlier."
        )
        st.markdown("**Purchasing power**")
        st.write(
            "How much your money can buy. A balance can stay "
            "unchanged in dollars while losing purchasing power."
        )

    st.info(
        "Slower inflation does not usually mean prices are falling. "
        "If inflation falls from 6% to 2%, prices are generally "
        "still rising, just more slowly."
    )

    st.markdown("### 02 · A grocery-shopping example")
    st.write(
        "Imagine a basket of groceries costs **CAD 100 today**. "
        "If its price rises by a hypothetical 3% each year, "
        "the cost compounds over time."
    )

    example = purchasing_power(100, 1000, 3, 0, 10)

    a, b, c = st.columns(3)
    a.metric("Groceries today", "CAD 100")
    b.metric("Groceries after 10 years", f"CAD {example.future_price:,.2f}")
    c.metric(
        "Purchasing power of CAD 1,000",
        f"CAD {example.savings_in_today_dollars:,.0f}",
    )

    st.write(
        "After ten years, that same basket costs approximately "
        f"CAD {example.future_price:,.2f}. "
        "If you kept CAD 1,000 without earning interest, "
        "you would still have CAD 1,000 in your account, "
        "but it would buy less."
    )

    st.markdown("### 03 · Experiment with inflation")
    st.write(
        "Now create your own hypothetical scenario. "
        "The figures below are not inflation forecasts."
    )

    # QI INFLATION BEGINNER UX V2
    st.markdown("#### First, choose an everyday situation")
    st.write(
        "You don't need to know interest rates or economic statistics. "
        "Choose what sounds familiar, and we'll supply example numbers."
    )

    scenarios = {
        "Cash at home": (
            3.0, 0.0,
            "Your money stays the same in dollars, but rising prices "
            "mean it gradually buys less."
        ),
        "Basic savings account": (
            3.0, 1.0,
            "Your savings earn some interest, but not enough to keep up "
            "with the assumed increase in prices."
        ),
        "Savings keep up with prices": (
            3.0, 3.0,
            "Your savings grow at the same rate as prices. "
            "That preserves purchasing power in this simplified example."
        ),
        "Savings grow faster than prices": (
            3.0, 5.0,
            "Your savings grow faster than prices, so their purchasing "
            "power increases in this hypothetical example."
        ),
    }

    scenario = st.radio(
        "Which situation would you like to explore?",
        list(scenarios),
        index=1,
        key="qi_inflation_scenario",
    )

    inflation_default, return_default, explanation = scenarios[scenario]
    st.info(explanation)

    st.markdown("#### Next, choose how much and how long")

    left, right = st.columns(2)
    with left:
        starting_savings = st.slider(
            "Money you start with (CAD)",
            1000, 100000, 10000, 1000,
            key="qi_inflation_savings",
        )
    with right:
        years = st.select_slider(
            "Look ahead",
            options=[1, 5, 10, 20, 30, 40, 50],
            value=20,
            key="qi_inflation_years_v2",
        )

    inflation_rate = inflation_default
    savings_return = return_default

    with st.expander("Customize the numbers (optional)"):
        st.write(
            "These are assumed yearly percentages, not predictions. "
            "The inflation rate measures how quickly prices increase. "
            "The savings return measures how quickly your balance grows."
        )

        custom = st.checkbox(
            "Use my own assumptions",
            value=False,
            key="qi_inflation_custom_v2",
        )

        if custom:
            a, b = st.columns(2)
            with a:
                inflation_rate = st.slider(
                    "How quickly are prices rising each year? (%)",
                    0.0, 12.0, inflation_default, 0.5,
                    key=f"qi_inflation_rate_{scenario}",
                )
            with b:
                savings_return = st.slider(
                    "How much does your savings balance grow each year? (%)",
                    0.0, 12.0, return_default, 0.5,
                    key=f"qi_inflation_return_{scenario}",
                )
            st.caption(
                "These are simplified constant annual rates. "
                "Actual inflation and returns change over time."
            )
        else:
            st.caption(
                f"This example assumes prices rise {inflation_rate:.1f}% "
                f"per year and savings grow {savings_return:.1f}% per year."
            )

    result = purchasing_power(
        100,
        starting_savings,
        inflation_rate,
        savings_return,
        years,
    )

    st.markdown("#### What happens to your money?")

    a, b, c = st.columns(3)

    a.metric(
        "Future account balance",
        f"CAD {result.future_savings:,.0f}",
    )
    b.metric(
        "Value in today's dollars",
        f"CAD {result.savings_in_today_dollars:,.0f}",
    )
    c.metric(
        "Purchasing-power change",
        f"{result.purchasing_power_change_pct:+.1f}%",
    )

    with st.container(border=True):
        st.markdown("#### Future dollars versus purchasing power")

        maximum = max(
            result.future_savings,
            result.savings_in_today_dollars,
            1,
        )

        st.write("**Nominal future balance**")
        st.progress(
            min(1.0, result.future_savings / maximum)
        )

        st.write("**Inflation-adjusted value**")
        st.progress(
            min(1.0, result.savings_in_today_dollars / maximum)
        )

        st.caption(
            "Both bars use the same scale. The nominal balance "
            "is measured in future dollars; the inflation-adjusted "
            "value is measured in today's purchasing power."
        )

    if result.purchasing_power_change_pct < -0.01:
        st.warning(
            "Your modeled savings balance may increase, "
            "but your purchasing power decreases because "
            "inflation exceeds the savings return."
        )
    elif result.purchasing_power_change_pct > 0.01:
        st.success(
            "In this illustration, your savings return exceeds "
            "inflation, so purchasing power increases."
        )
    else:
        st.info(
            "In this illustration, your savings preserve "
            "approximately the same purchasing power."
        )

    st.caption(
        "Simplified constant-rate model. Annual compounding, "
        "no deposits, withdrawals, taxes, fees or changing inflation. "
        "Actual inflation and investment returns vary."
    )

    st.markdown("### 04 · Nominal returns versus real returns")
    st.write(
        "A **nominal return** tells you how many more dollars "
        "you have. A **real return** adjusts that growth for "
        "changes in the overall price level."
    )

    st.markdown(
        "For a quick estimate, people often subtract inflation "
        "from their investment return. The exact calculation "
        "accounts for compounding."
    )

    real_rate = real_return_pct(
        savings_return,
        inflation_rate,
    )

    with st.container(border=True):
        st.markdown("#### Your scenario")
        st.write(
            f"Nominal annual return: **{savings_return:.1f}%**"
        )
        st.write(
            f"Annual inflation: **{inflation_rate:.1f}%**"
        )
        st.write(
            f"Exact inflation-adjusted annual return: "
            f"**{real_rate:+.2f}%**"
        )

    st.write(
        "For example, earning 3% while prices rise 4% "
        "gives a negative real return. You have more dollars, "
        "but they buy slightly less than before."
    )

    st.markdown("### 05 · Connect inflation to the economy")

    with st.expander("Why can prices rise?"):
        st.write(
            "Inflation can reflect increased spending demand, "
            "higher production costs, supply disruptions, "
            "changes in energy prices, and other economic forces. "
            "Different causes can require different responses."
        )

    with st.expander("How does the Bank of Canada respond?"):
        st.write(
            "The Bank of Canada uses monetary policy, including "
            "its policy interest rate, to influence demand and "
            "inflation over time. Higher interest rates generally "
            "make borrowing more expensive and saving more "
            "attractive, but their effects are not immediate."
        )

    with st.expander("What is the Consumer Price Index (CPI)?"):
        st.write(
            "CPI measures price changes for a representative "
            "basket of consumer goods and services. Your personal "
            "experience may differ because everyone spends "
            "money on a different mix of products and services."
        )

    with st.expander("How does inflation affect investors?"):
        st.write(
            "Investors care about the purchasing power of future "
            "cash flows, interest rates, business costs and "
            "consumer spending. Inflation can affect different "
            "investments in different ways."
        )

    st.markdown("### 06 · Check what you learned")

    questions = (
        (
            "Inflation falls from 6% to 2%. What does that usually mean?",
            (
                "Prices are falling by 4%",
                "Prices are still rising, but more slowly",
                "Every price stays unchanged",
            ),
            "Prices are still rising, but more slowly",
            "A positive inflation rate still indicates rising "
            "prices overall, even if the rate decreases.",
        ),
        (
            "Your savings earn 2% while inflation is 4%. "
            "What happens to purchasing power?",
            (
                "It increases",
                "It stays exactly the same",
                "It decreases",
            ),
            "It decreases",
            "The savings grow more slowly than the price level, "
            "so their inflation-adjusted value falls.",
        ),
        (
            "Why might your personal inflation feel different "
            "from the published CPI rate?",
            (
                "Everyone buys exactly the same products",
                "Households have different spending patterns",
                "The CPI measures only stock prices",
            ),
            "Households have different spending patterns",
            "Your expenses may differ from the representative "
            "basket used to calculate CPI.",
        ),
    )

    for i, (question, choices, correct, explanation) in enumerate(questions):
        answer = st.radio(
            question,
            choices,
            index=None,
            key=f"qi_inflation_question_{i}",
        )

        if st.button(
            "Check answer",
            key=f"qi_inflation_check_{i}",
        ):
            if answer is None:
                st.info("Choose an answer first.")
            elif answer == correct:
                st.success("Correct! " + explanation)
            else:
                st.info("Not quite. " + explanation)

    st.markdown("### Continue learning")
    st.link_button(
        "Bank of Canada — Inflation",
        "https://www.bankofcanada.ca/core-functions/monetary-policy/inflation/",
    )
    st.link_button(
        "Statistics Canada — Consumer Price Index",
        "https://www.statcan.gc.ca/en/subjects-start/prices_and_price_indexes/consumer_price_indexes",
    )

    st.caption(
        "Educational illustrations only. "
        "Not a prediction of inflation, investment performance "
        "or personalized financial advice."
    )
