"""Guided Canadian paycheque lesson with an explicitly fictional deduction model."""
import streamlit as st


def render_paycheque() -> None:
    st.markdown("### 01 · Learn how a paycheque works")
    st.write(
        "Your **gross pay** is what you earn before deductions. Your **net pay** "
        "is what arrives in your bank account after taxes, payroll contributions "
        "and any other applicable deductions."
    )
    st.info(
        "An annual salary of CAD 60,000 does not mean receiving "
        "CAD 5,000 in your bank account each month. "
        "Employers generally withhold several amounts first."
    )

    # QI PAYCHEQUE PRESENTATION V3
    with st.container(border=True):
        st.markdown("#### Four things to recognize on a Canadian payslip")

        definitions = (
            (
                "Income tax",
                "Money withheld toward federal and provincial or territorial "
                "income taxes. Your final annual tax can differ from the amount withheld.",
            ),
            (
                "Canada Pension Plan (CPP)",
                "Contributions that help fund pension benefits. "
                "Quebec generally uses the Quebec Pension Plan instead.",
            ),
            (
                "Employment Insurance (EI)",
                "Premiums that support eligible Employment Insurance benefits. "
                "Quebec has separate parental insurance arrangements.",
            ),
            (
                "Other deductions",
                "Some employees also have workplace pension, union, "
                "insurance, or other authorized deductions.",
            ),
        )

        for title, explanation in definitions:
            st.markdown(f"**{title}**")
            st.write(explanation)

    st.markdown("### 02 · Follow a sample payslip")
    st.write(
        "The following is a **fictional payroll example**, designed to explain "
        "how deductions affect take-home pay. Its percentages are not CRA rates "
        "and must not be used for financial planning."
    )

    # QI PAYCHEQUE BEGINNER SCENARIOS V4
    st.markdown("#### Choose an everyday situation")
    st.write(
        "You don't need to understand payroll deductions to begin. "
        "Choose a situation and we'll provide example numbers."
    )

    scenarios = {
        "My first full-time job": (45000, "Biweekly (26)"),
        "I received a raise": (65000, "Biweekly (26)"),
        "Comparing pay schedules": (60000, "Monthly (12)"),
    }

    scenario = st.radio(
        "What would you like to explore?",
        list(scenarios),
        horizontal=True,
        key="qi_pay_scenario_v4",
    )

    salary_default, frequency_default = scenarios[scenario]

    explanations = {
        "My first full-time job":
            "Your employer offers an annual salary, but your paycheque "
            "shows one pay period after deductions.",
        "I received a raise":
            "A raise increases your gross salary. Some deductions also "
            "increase, so your take-home pay may rise by a smaller amount.",
        "Comparing pay schedules":
            "The same annual salary can arrive in different-sized "
            "paycheques depending on how frequently you're paid.",
    }

    st.info(explanations[scenario])

    salary = salary_default
    frequency = frequency_default

    with st.expander("Customize your example (optional)"):
        customize = st.checkbox(
            "Change the example numbers",
            key="qi_pay_customize_v4",
        )

        if customize:
            left, right = st.columns(2)

            with left:
                salary = st.slider(
                    "Annual salary before deductions (CAD)",
                    20000, 200000, salary_default, 1000,
                    key=f"qi_pay_salary_{scenario}",
                )

            with right:
                choices = ["Biweekly (26)", "Monthly (12)", "Weekly (52)"]
                frequency = st.selectbox(
                    "How often are you paid?",
                    choices,
                    index=choices.index(frequency_default),
                    key=f"qi_pay_frequency_{scenario}",
                )

    st.caption(
        f"Example: CAD {salary:,} annual salary, {frequency.lower()} payments."
    )

    periods = {
        "Biweekly (26)": 26,
        "Monthly (12)": 12,
        "Weekly (52)": 52,
    }[frequency]

    # Fictional rates only: intentionally not a Canadian payroll tax calculator.
    rates = {
        "Illustrative federal tax": 0.12,
        "Illustrative provincial tax": 0.06,
        "Illustrative pension deduction": 0.04,
        "Illustrative insurance deduction": 0.01,
    }
    gross = salary / periods
    amounts = {name: gross * rate for name, rate in rates.items()}
    net = gross - sum(amounts.values())

    st.markdown("#### Your example payslip")
    a, b, c = st.columns(3)
    a.metric("Gross per pay", f"${gross:,.2f}")
    b.metric("Total deductions", f"${sum(amounts.values()):,.2f}")
    c.metric("Net per pay", f"${net:,.2f}")

    st.progress(net / gross, text="Share of gross pay remaining after example deductions")

    with st.container(border=True):
        st.markdown("**Payslip breakdown**")
        st.write(f"Gross earnings: **${gross:,.2f}**")
        for name, amount in amounts.items():
            st.write(f"{name}: −${amount:,.2f}")
        st.divider()
        st.markdown(f"**Example take-home pay: ${net:,.2f}**")

    st.caption(
        "Fictional flat-rate deductions of 12%, 6%, 4% and 1%, applied to all "
        "earnings without credits, exemptions, annual contribution limits or "
        "special payroll rules. NOT an estimate of actual Canadian net pay."
    )

    st.markdown("### 03 · Connect it to real life")
    with st.expander("Why can my paycheque change even when my salary stays the same?"):
        st.write(
            "Overtime, bonuses, taxable benefits, unpaid leave, changed withholding, "
            "benefit deductions and annual CPP/EI limits can affect the amount."
        )
    with st.expander("Why does a raise not necessarily increase take-home pay by the full amount?"):
        st.write(
            "Some additional earnings may be withheld for income tax or other "
            "contributions. However, entering a higher marginal tax bracket does "
            "not mean your entire income is taxed at that higher rate."
        )
    with st.expander("Is tax withheld from my paycheque always my final tax bill?"):
        st.write(
            "No. Your final income tax depends on your full tax-year circumstances, "
            "including eligible deductions and credits. Filing a return may result "
            "in a refund or a balance owing."
        )

    st.markdown("### 04 · Check what you learned")
    questions = [
        (
            "What is net pay?",
            ["Salary before deductions", "Money remaining after deductions", "Only income tax"],
            "Money remaining after deductions",
            "Net pay is what remains after applicable deductions."
        ),
        (
            "Does CPP mean the same thing as income tax?",
            ["Yes", "No"],
            "No",
            "CPP is a pension contribution, not the same as income tax."
        ),
        (
            "Can your final annual tax differ from payroll withholding?",
            ["Yes", "No"],
            "Yes",
            "Withholding is not always equal to your final tax liability."
        ),
    ]
    for i, (question, options, correct, explanation) in enumerate(questions):
        answer = st.radio(
            question, options, index=None,
            key=f"qi_pay_question_{i}",
        )
        if st.button("Check answer", key=f"qi_pay_check_{i}"):
            if answer is None:
                st.info("Choose an answer first.")
            elif answer == correct:
                st.success(f"Correct! {explanation}")
            else:
                st.info(f"Not quite. {explanation}")

    st.markdown("### 05 · Calculate a real paycheque")
    st.write(
        "When you need actual payroll figures, use the CRA calculator with "
        "your province of employment, pay date, pay frequency and applicable details."
    )
    st.link_button(
        "Open the CRA Payroll Deductions Calculator",
        "https://www.canada.ca/en/revenue-agency/services/e-services/"
        "digital-services-businesses/payroll-deductions-online-calculator.html",
    )
    st.caption(
        "Educational content only; not personalized tax, employment or financial advice."
    )
