"""Guided TFSA versus RRSP lesson using the tested comparison model."""
import streamlit as st

from app.education.account_comparison import compare_accounts


def render_rrsp_comparison() -> None:
    st.markdown("### 01 · Two accounts, two different tax treatments")
    st.write(
        "A TFSA and an RRSP can both hold eligible investments. "
        "The important difference is **when taxes apply**."
    )

    left, right = st.columns(2)
    with left, st.container(border=True):
        st.markdown("#### TFSA")
        st.markdown(
            "**Contributions:** Made with after-tax money.\n\n"
            "**Tax deduction:** None.\n\n"
            "**Growth:** Generally tax-free.\n\n"
            "**Withdrawals:** Generally tax-free."
        )
    with right, st.container(border=True):
        st.markdown("#### RRSP")
        st.markdown(
            "**Contributions:** Generally deductible, subject to the rules.\n\n"
            "**Tax deduction:** May reduce taxable income.\n\n"
            "**Growth:** Generally tax-deferred.\n\n"
            "**Withdrawals:** Generally included in taxable income."
        )

    st.info(
        "Think of a TFSA as using money after income tax. "
        "An RRSP generally lets you defer income tax until withdrawal."
    )

    st.markdown("### 02 · Follow a fair comparison")
    st.write(
        "Suppose you have **CAD 7,000 of after-tax savings** and an illustrative "
        "current marginal tax rate of 30%."
    )
    st.markdown(
        "You could contribute CAD 7,000 to a TFSA. "
        "Under our simplified RRSP example, contributing CAD 10,000 to an RRSP "
        "produces a CAD 3,000 tax benefit. Your net cost is therefore CAD 7,000."
    )
    st.write(
        "Both strategies use the same net savings budget. "
        "This avoids comparing two accounts funded at different personal costs."
    )

    st.markdown("### 03 · Experiment with your own example")
    # QI RRSP BEGINNER SCENARIOS V2
    st.write(
        "You do not need to know your future tax rate or choose an "
        "investment return to begin. Pick an everyday situation and "
        "we'll show you an example."
    )

    scenarios = {
        "I'm starting my career": (
            3000, 20, 30, 5, 25,
            "Imagine you pay a relatively low tax rate today, but "
            "might pay a higher rate when you eventually withdraw "
            "money. In this example, that can favour a TFSA."
        ),
        "I'm in my higher-earning years": (
            7000, 35, 20, 5, 20,
            "Imagine you pay a higher tax rate today than you "
            "expect when you withdraw the money. In this example, "
            "that can favour an RRSP."
        ),
        "My tax rate stays about the same": (
            5000, 30, 30, 5, 20,
            "When the tax rate today and at withdrawal is equal, "
            "a TFSA and RRSP can produce the same after-tax result "
            "under the simplified model's assumptions."
        ),
        "I might pay more tax later": (
            5000, 25, 40, 5, 20,
            "If the tax rate at withdrawal is higher than today, "
            "the TFSA can have an advantage in this simplified model."
        ),
    }

    scenario = st.radio(
        "Which situation would you like to explore?",
        list(scenarios),
        horizontal=True,
        key="qi_rrsp_scenario_beginner_v2",
    )

    budget, tax_now, tax_later, annual_return, years, explanation = (
        scenarios[scenario]
    )

    st.info(explanation)
    st.caption(
        "These are illustrative tax rates and a hypothetical investment "
        "return, not personal recommendations or predictions."
    )

    with st.expander("Customize the assumptions (optional)"):
        customize = st.checkbox(
            "I'd like to change the example numbers",
            key="qi_rrsp_customize_v2",
        )

        if customize:
            st.write(
                "Your savings budget is the money you can afford to "
                "set aside after tax. The model adjusts the RRSP "
                "contribution to make the comparison fair."
            )
            a, b = st.columns(2)

            with a:
                budget = st.slider(
                    "Money available to save (CAD)",
                    1000, 20000, budget, 500,
                    key=f"qi_rrsp_budget_v2_{scenario}",
                )
                tax_now = st.slider(
                    "Example tax rate while working (%)",
                    0, 60, tax_now,
                    key=f"qi_rrsp_now_v2_{scenario}",
                )
                years = st.slider(
                    "How many years will it grow?",
                    0, 50, years,
                    key=f"qi_rrsp_years_v2_{scenario}",
                )

            with b:
                tax_later = st.slider(
                    "Example tax rate when withdrawing (%)",
                    0, 60, tax_later,
                    key=f"qi_rrsp_later_v2_{scenario}",
                )
                annual_return = st.slider(
                    "Hypothetical annual investment return (%)",
                    -10, 15, annual_return,
                    key=f"qi_rrsp_return_v2_{scenario}",
                )

    st.caption(
        f"Example assumptions: CAD {budget:,} available to save, "
        f"{tax_now}% tax rate today, {tax_later}% at withdrawal, "
        f"{annual_return}% yearly investment return, over {years} years."
    )

    result = compare_accounts(
        budget, tax_now, tax_later, annual_return, years
    )

    st.markdown("#### Compare the amounts you could keep")
    left, right = st.columns(2)
    with left:
        st.metric(
            "TFSA after-tax value",
            f"CAD {result.tfsa_future_value:,.0f}",
        )
        st.caption("Withdrawals are assumed tax-free.")
    with right:
        st.metric(
            "RRSP after-tax value",
            f"CAD {result.rrsp_after_tax_value:,.0f}",
        )
        st.caption("Illustrative withdrawal tax already deducted.")

    max_value = max(
        result.tfsa_future_value, result.rrsp_after_tax_value, 1
    )
    with st.container(border=True):
        st.write("**After-tax comparison**")
        st.write("TFSA")
        st.progress(result.tfsa_future_value / max_value)
        st.write("RRSP")
        st.progress(result.rrsp_after_tax_value / max_value)

    st.markdown("#### Why the amounts differ")
    st.write(
        f"Your TFSA contribution is **CAD {result.tfsa_contribution:,.0f}**. "
        f"Your illustrative RRSP contribution is "
        f"**CAD {result.rrsp_contribution:,.0f}**."
    )
    st.write(
        f"The example RRSP tax benefit is "
        f"**CAD {result.rrsp_deduction_value:,.0f}**. "
        f"Before withdrawal tax, the modeled RRSP grows to "
        f"**CAD {result.rrsp_future_value:,.0f}**."
    )

    if abs(result.difference) < 0.01:
        st.success(
            "The two after-tax outcomes are equal in this simplified model. "
            "With equal tax rates and consistent treatment of the RRSP "
            "deduction, neither account has an automatic mathematical advantage."
        )
    elif result.difference > 0:
        st.info(
            f"The RRSP finishes about CAD {result.difference:,.0f} higher "
            "in this example because its assumed withdrawal tax rate is lower."
        )
    else:
        st.info(
            f"The TFSA finishes about CAD {-result.difference:,.0f} higher "
            "in this example because the assumed RRSP withdrawal tax rate "
            "is higher."
        )

    st.caption(
        "Simplified lump-sum model. Assumes sufficient contribution room, "
        "full realization and reinvestment of the RRSP deduction benefit, "
        "one constant annual return and one withdrawal tax rate. "
        "Excludes fees, inflation, benefits interactions, withholding "
        "timing and actual progressive income tax calculations."
    )

    st.markdown("### 04 · Rules that matter in real life")
    with st.expander("What happens if I withdraw from a TFSA?"):
        st.write(
            "Eligible TFSA withdrawals are generally tax-free. "
            "The withdrawn amount normally becomes new contribution room "
            "on January 1 of the next calendar year, not immediately. "
            "Re-contributing too early without enough unused room "
            "can create an overcontribution."
        )
    with st.expander("What happens if I withdraw from an RRSP?"):
        st.write(
            "Ordinary RRSP withdrawals generally count as taxable income. "
            "The institution may withhold tax, but the final tax liability "
            "can differ. An ordinary withdrawal does not restore "
            "the RRSP contribution room used."
        )
    with st.expander("Is my RRSP tax refund free money?"):
        st.write(
            "No. An RRSP deduction can reduce tax today, but withdrawals "
            "are generally taxable later. The comparison changes if you "
            "spend the tax savings rather than invest them."
        )
    with st.expander("What else could change the decision?"):
        st.write(
            "Contribution room, retirement income, pension arrangements, "
            "government benefits, withdrawal timing and other financial goals "
            "can matter. A TFSA or RRSP is an account structure, not "
            "a guarantee of investment returns."
        )

    st.markdown("### 05 · Check your understanding")
    questions = (
        (
            "Which account generally allows tax-free eligible withdrawals?",
            ("RRSP", "TFSA", "Both always"),
            "TFSA",
            "Eligible TFSA withdrawals are generally tax-free.",
        ),
        (
            "Does an ordinary RRSP withdrawal restore contribution room?",
            ("Yes", "No"),
            "No",
            "Ordinary RRSP withdrawals generally do not restore used room.",
        ),
        (
            "When current and future tax rates are equal in our fair model, "
            "which account necessarily wins?",
            ("TFSA", "RRSP", "Neither"),
            "Neither",
            "With the same net cost, return and tax rate, the modeled "
            "after-tax outcomes are equal.",
        ),
    )
    for i, (question, choices, correct, explanation) in enumerate(questions):
        answer = st.radio(
            question, choices, index=None,
            key=f"qi_rrsp_question_{i}",
        )
        if st.button("Check answer", key=f"qi_rrsp_check_{i}"):
            if answer is None:
                st.info("Choose an answer.")
            elif answer == correct:
                st.success("Correct! " + explanation)
            else:
                st.info("Not quite. " + explanation)

    st.markdown("### 06 · Learn from the CRA")
    st.link_button(
        "CRA — Understanding TFSAs",
        "https://www.canada.ca/en/revenue-agency/services/tax/"
        "individuals/topics/tax-free-savings-account/what.html",
    )
    st.link_button(
        "CRA — RRSP information",
        "https://www.canada.ca/en/revenue-agency/services/tax/"
        "individuals/topics/rrsps-related-plans.html",
    )
    st.caption(
        "General Canadian financial education only. "
        "Not a personalized recommendation or actual tax estimate."
    )
