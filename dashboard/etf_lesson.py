"""Guided ETF lesson with fictional holdings and tested analysis models."""

import streamlit as st

from app.education.etf_models import (
    EXAMPLE_FUNDS,
    annual_fee_cost,
    concentration_index,
    fund_overlap,
    portfolio_exposure,
)


def render_etf_lesson() -> None:
    st.markdown("### 01 · What are you actually buying?")
    st.write(
        "An **exchange-traded fund (ETF)** is an investment fund whose shares "
        "trade on an exchange. A single ETF can hold many stocks, bonds, or "
        "other assets. Buying one ETF share gives you an interest in the fund, "
        "not direct ownership of each underlying company's shares."
    )

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("#### Individual stock")
        st.write(
            "Your investment is directly tied to one company's shares. "
            "Company-specific news can have a large impact."
        )
    with right, st.container(border=True):
        st.markdown("#### ETF")
        st.write(
            "Your investment is in a fund holding a basket of assets. "
            "The risks depend on what the fund actually owns."
        )

    st.info(
        "An ETF is a type of fund structure, not a guarantee of diversification. "
        "Some funds hold hundreds of assets; others concentrate on one industry."
    )

    st.markdown("### 02 · Look inside an example ETF")
    st.write(
        "These three portfolios are **completely fictional**. "
        "They demonstrate how fund holdings can differ."
    )

    fund_name = st.selectbox(
        "Choose an example fund",
        list(EXAMPLE_FUNDS),
        key="qi_etf_fund",
    )
    holdings = EXAMPLE_FUNDS[fund_name]

    with st.container(border=True):
        st.markdown(f"**{fund_name} — underlying holdings**")
        for name, weight in sorted(
            holdings.items(), key=lambda item: -item[1]
        ):
            a, b = st.columns([3, 1])
            a.write(name)
            b.write(f"{weight:.0f}%")
            st.progress(weight / 100)

    st.write(
        "The percentage beside each holding is its share of the fund. "
        "If a company represents 25% of a fund, a change in that company's "
        "value can have a relatively large effect on the fund."
    )

    st.markdown("### 03 · Build a fictional two-fund portfolio")
    st.write(
        "Now combine two ETFs. The model looks through each fund to show "
        "your total exposure to the underlying holdings."
    )

    # QI ETF BEGINNER EXPERIENCE V2
    st.markdown("#### Choose an investing situation")
    st.write(
        "You don't need to know which funds to pick or what allocation "
        "percentage to use. Choose a situation and we'll build a "
        "fictional example for you."
    )

    examples = {
        "I bought one ETF": (
            "Broad Market", "Broad Market", 100,
            "Owning one ETF does not necessarily mean owning just one "
            "company. This example fund contains several holdings. "
            "Its concentration still depends on what it owns."
        ),
        "I bought two different types of ETFs": (
            "Technology Focus", "Balanced Mix", 50,
            "These fictional funds have no identical named holdings. "
            "That reduces holdings overlap, but does not guarantee "
            "lower risk or that their values move independently."
        ),
        "I bought two ETFs with similar companies": (
            "Broad Market", "Technology Focus", 50,
            "These funds both own Company A and Company B. "
            "Owning both can increase your exposure to those "
            "companies instead of spreading your money as widely "
            "as you might expect."
        ),
    }

    situation = st.radio(
        "Which situation would you like to explore?",
        list(examples),
        key="qi_etf_beginner_situation_v2",
    )

    first, second, allocation, explanation = examples[situation]
    st.info(explanation)

    with st.expander("Customize the portfolio (optional)"):
        customize = st.checkbox(
            "Choose my own funds and percentages",
            key="qi_etf_custom_portfolio_v2",
        )

        if customize:
            fund_names = list(EXAMPLE_FUNDS)
            a, b = st.columns(2)

            with a:
                first = st.selectbox(
                    "First fictional fund",
                    fund_names,
                    index=fund_names.index(first),
                    key=f"qi_etf_first_v2_{situation}",
                )

            with b:
                second = st.selectbox(
                    "Second fictional fund",
                    fund_names,
                    index=fund_names.index(second),
                    key=f"qi_etf_second_v2_{situation}",
                )

            allocation = st.slider(
                f"Share of your money in {first} (%)",
                0, 100, allocation, 5,
                key=f"qi_etf_allocation_v2_{situation}",
            )

    st.caption(
        f"Your example: {allocation}% in {first} and "
        f"{100 - allocation}% in {second}. "
        "All funds and holdings are fictional."
    )

    first_holdings = EXAMPLE_FUNDS[first]
    second_holdings = EXAMPLE_FUNDS[second]

    if first == second:
        exposure = portfolio_exposure(
            {first: first_holdings}, {first: 100}
        )
    else:
        exposure = portfolio_exposure(
            {"First": first_holdings, "Second": second_holdings},
            {"First": allocation, "Second": 100 - allocation},
        )

    overlap = fund_overlap(first_holdings, second_holdings)
    concentration = concentration_index(exposure)

    x, y, z = st.columns(3)
    x.metric("Fund overlap", f"{overlap:.0f}%")
    y.metric("Largest holding", f"{max(exposure.values()):.1f}%")
    z.metric("Concentration index", f"{concentration:.3f}")

    st.caption(
        "Overlap = sum of the smaller shared holding weights. "
        "The concentration index is the sum of squared fractional holdings "
        "weights. Neither measure predicts volatility or investment returns."
    )

    with st.container(border=True):
        st.markdown("#### Your combined underlying exposure")
        for name, weight in exposure.items():
            st.write(f"**{name}** — {weight:.1f}%")
            st.progress(min(1.0, weight / 100))

    if first == second:
        st.warning(
            "You've selected the same ETF twice. "
            "Owning two copies of an identical fund does not provide "
            "additional underlying diversification."
        )
    elif overlap >= 40:
        st.info(
            "These example funds share substantial underlying exposure. "
            "Combining them doesn't necessarily spread your investments "
            "across many independent holdings."
        )
    else:
        st.info(
            "These funds have less overlap in their named holdings, "
            "but low holdings overlap does not guarantee low correlation "
            "or lower market risk."
        )

    st.markdown("### 04 · Understand ETF fees")
    st.write(
        "Most ETFs charge ongoing fund expenses. A fund's Management Expense "
        "Ratio (MER) is usually stated as a percentage of assets per year "
        "and is reflected in fund performance rather than billed as a "
        "separate annual invoice."
    )

    st.markdown("#### Choose a fee example")
    st.write(
        "You don't need to know what an ETF fee percentage should be. "
        "Pick a simple example to see how an annual fund expense works."
    )

    fee_examples = {
        "Getting started with CAD 5,000": (
            5000, 0.25,
            "A small example investment with a hypothetical "
            "annual fund fee."
        ),
        "Growing my investments to CAD 25,000": (
            25000, 0.25,
            "The same percentage fee produces a larger dollar "
            "cost when your balance is larger."
        ),
        "Comparing a higher-fee example": (
            10000, 1.0,
            "A higher percentage fee increases the dollar cost "
            "on the same balance. This does not imply that "
            "a particular ETF charges this amount."
        ),
    }

    fee_situation = st.radio(
        "Which example would you like to see?",
        list(fee_examples),
        key="qi_etf_fee_situation_v2",
    )

    value, fee_pct, fee_explanation = fee_examples[fee_situation]
    st.caption(fee_explanation)

    with st.expander("Customize the fee example (optional)"):
        if st.checkbox(
            "Change the investment amount or fee",
            key="qi_etf_custom_fee_v2",
        ):
            value = st.slider(
                "Illustrative portfolio value (CAD)",
                1000, 100000, value, 1000,
                key=f"qi_etf_value_v2_{fee_situation}",
            )
            fee_pct = st.slider(
                "Hypothetical annual fund fee (%)",
                0.0, 2.0, fee_pct, 0.05,
                key=f"qi_etf_fee_v2_{fee_situation}",
            )

    st.caption(
        f"Example assumptions: CAD {value:,} invested and "
        f"a hypothetical {fee_pct:.2f}% annual fee."
    )

    cost = annual_fee_cost(value, fee_pct)
    st.metric("Approximate fee on a constant balance over one year", f"CAD {cost:,.2f}")

    st.write(
        "Fees reduce the investment return you keep. Over many years, "
        "even modest differences in fees can matter. Trading commissions, "
        "bid-ask spreads, taxes and currency conversion may also create costs."
    )
    st.caption(
        "Simplified one-year example using a constant balance. "
        "Not a forecast of actual fund charges or investment returns."
    )

    st.markdown("### 05 · Common misconceptions")
    with st.expander("Does owning several ETFs always mean I'm diversified?"):
        st.write(
            "No. The funds may hold many of the same companies or expose "
            "you to similar industries and economic risks. Look at the "
            "underlying holdings and asset types."
        )
    with st.expander("Does an ETF protect me from a market crash?"):
        st.write(
            "No. Diversification can reduce some company-specific risk, "
            "but broad stock markets can decline together."
        )
    with st.expander("Are all ETFs passive index funds?"):
        st.write(
            "No. Many track indexes, while others are actively managed. "
            "Some use specialized strategies that involve additional risks."
        )

    st.markdown("### 06 · Check your understanding")
    questions = (
        (
            "What do you generally buy when purchasing an ETF share?",
            ("A share of an investment fund", "A guaranteed return", "A savings account"),
            "A share of an investment fund",
            "An ETF share represents an interest in a fund that may hold underlying assets.",
        ),
        (
            "Can two different ETFs hold the same companies?",
            ("Yes", "No"),
            "Yes",
            "Overlapping holdings can create more concentration than expected.",
        ),
        (
            "Does a low holdings-overlap score guarantee low investment risk?",
            ("Yes", "No"),
            "No",
            "Different holdings can still react similarly to economic events.",
        ),
    )

    for i, (question, choices, correct, explanation) in enumerate(questions):
        answer = st.radio(
            question, choices, index=None,
            key=f"qi_etf_question_{i}",
        )
        if st.button("Check answer", key=f"qi_etf_check_{i}"):
            if answer is None:
                st.info("Choose an answer.")
            elif answer == correct:
                st.success("Correct! " + explanation)
            else:
                st.info("Not quite. " + explanation)

    st.caption(
        "All example funds and holdings are fictional. "
        "This lesson is for education, not investment recommendations."
    )
