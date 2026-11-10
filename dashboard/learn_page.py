
"""Quant Learn: approachable, interactive financial education.

No user financial data is collected. Examples are illustrative, not personal advice.
"""

from __future__ import annotations

import streamlit as st

# Catalog and presentation are kept separate from the existing research routes.
from app.education.catalog import (
    LESSON_SUMMARIES,
    PATHWAYS,
    READY_LESSONS,
)
from dashboard.diversification_lesson import render_diversification
from dashboard.etf_lesson import render_etf_lesson
from dashboard.financial_labs import render_compound_growth, render_credit_card
from dashboard.inflation_lesson import render_inflation_lesson
from dashboard.learn_design import enable_learn_style, featured_lesson, hero
from dashboard.market_expectations_lesson import render_market_expectations
from dashboard.options_premium_lesson import render_options_premium_lesson
from dashboard.paycheque_lesson import render_paycheque
from dashboard.rrsp_lesson import render_rrsp_comparison
from dashboard.visual_icons import icon_svg

# Unified vector headings for the Learn pathway and catalog cards.
_LEARN_ICON_STYLE = """
<style>
.qi-learn-path-head {
    display: flex;
    align-items: center;
    gap: clamp(12px, 2vw, 18px);
    margin: 5px 0 15px;
    min-width: 0;
}
.qi-learn-path-head .qi-learn-path-icon {
    display: inline-flex;
    justify-content: center;
    align-items: center;
    flex: 0 0 auto;
    width: 48px;
    height: 48px;
    border-radius: 14px;
    color: #ff8fc5;
    background: linear-gradient(145deg, rgba(255, 120, 183, .13), rgba(101, 125, 211, .09));
    border: 1px solid rgba(255, 120, 183, .28);
}
.qi-learn-path-head h3,
.qi-learn-path-head h1 {
    color: #fff;
    letter-spacing: -.028em;
    margin: 0 !important;
    line-height: 1.18;
}
.qi-learn-path-head h3 {font-size: clamp(1.1rem, 1.6vw, 1.3rem) !important;}
.qi-learn-path-head h1 {font-size: clamp(1.85rem, 3.6vw, 2.9rem) !important;}
.qi-learn-path-head.is-card .qi-learn-path-icon {height: 43px; width: 43px; border-radius: 12px;}
.qi-learn-path-head.is-card {margin-bottom: 15px;}
@media (max-width: 640px) {
    .qi-learn-path-head .qi-learn-path-icon {width: 42px;height: 42px;border-radius: 12px;}
}
</style>
"""


def _pathway_heading(pathway: dict, *, card: bool = False) -> None:
    """Vector icon and accessible text heading with no emoji font dependency."""
    from html import escape

    tag = "h3" if card else "h1"
    variant = " is-card" if card else ""
    st.html(
        f'<div class="qi-learn-path-head{variant}">'
        f'<span class="qi-learn-path-icon">{icon_svg(pathway["icon"], 24)}</span>'
        f'<{tag}>{escape(pathway["title"])}</{tag}>'
        f'</div>'
    )

def _navigate(pathway: str | None = None, lesson: str | None = None) -> None:
    st.session_state["qi_learn_pathway"] = pathway
    st.session_state["qi_learn_lesson"] = lesson
    st.rerun()


def _check(question_id: str, question: str, options: list[str], correct: str, explanation: str) -> None:
    st.markdown("#### Check your understanding")
    answer = st.radio(question, options, index=None, key=f"qi_learn_answer_{question_id}")
    if st.button("Check answer", key=f"qi_learn_check_{question_id}"):
        if answer is None:
            st.info("Choose an answer first.")
        elif answer == correct:
            st.success(f"That's right. {explanation}")
        else:
            st.info(f"Not quite. {explanation}")


def _tax_brackets() -> None:
    """A browser-side model updates continuously while the user drags."""
    from dashboard.learn_live import render_tax_lab

    st.write(
        "A higher tax bracket applies only to the portion of taxable "
        "income within that bracket. Explore what happens to a raise "
        "using a simplified, fictional tax system."
    )
    render_tax_lab()
    st.link_button(
        "See the actual Canadian income tax brackets",
        "https://www.canada.ca/en/revenue-agency/services/tax/"
        "individuals/tax-rates-brackets/current-year.html",
    )
    _check(
        "brackets",
        "In our example, the higher bracket starts above 50,000 dollars. "
        "What happens to the first 50,000 dollars after you receive a raise?",
        [
            "All income moves into the higher bracket",
            "The first 50,000 dollars stays in the lower bracket",
            "The first 50,000 dollars stops being taxable",
        ],
        "The first 50,000 dollars stays in the lower bracket",
        "Only the portion of income in the higher bracket gets that higher rate.",
    )


def _tfsa() -> None:
    """A client-side TFSA room example, with clear limits on its accuracy."""
    from dashboard.learn_live import render_tfsa_lab

    st.write(
        "A **Tax-Free Savings Account (TFSA)** is an account that can hold "
        "eligible savings or investments. It is not a single type of investment."
    )
    choice = st.radio(
        "What can you hold inside a TFSA?",
        ["Cash savings", "GIC", "ETF"],
        horizontal=True,
        key="qi_learn_tfsa_assets_v3",
    )
    details = {
        "Cash savings": "A savings product may pay interest; rates and withdrawal rules depend on the product.",
        "GIC": "A guaranteed investment certificate generally has defined terms. Check whether early withdrawal is allowed.",
        "ETF": "An exchange-traded fund may hold stocks or bonds. Its market value can rise or fall.",
    }
    st.caption(details[choice])
    render_tfsa_lab()
    st.link_button(
        "Read the official CRA contribution-room guidance",
        "https://www.canada.ca/en/revenue-agency/services/tax/individuals/"
        "topics/tax-free-savings-account/contributing/calculate-room.html",
    )
    st.caption(
        "Your actual room depends on eligibility, residency, past years, "
        "all TFSA accounts and transactions. CRA records may lag, so "
        "verify with your own records before making contributions."
    )
    _check(
        "tfsa",
        "When does a normal TFSA withdrawal generally restore contribution room?",
        [
            "As soon as you withdraw",
            "January 1 of the following calendar year",
            "Only when the TFSA is closed",
        ],
        "January 1 of the following calendar year",
        "A TFSA withdrawal generally becomes additional contribution room "
        "on January 1 of the next calendar year.",
    )


def _interest() -> None:
    st.write("Interest rates affect borrowing and saving. When rates change, some household and business decisions can change too.")
    rate = st.slider("Annual interest rate on a hypothetical $10,000 loan", 1.0, 10.0, 5.0, 0.5, format="%.1f%%")
    st.metric("One year of simple interest", f"${10_000 * rate / 100:,.0f}")
    st.caption("Illustrative interest only, not an amortized loan or mortgage payment calculation. Fees, compounding and repayment schedules are excluded.")
    st.markdown("**Possible chain of effects:** Higher borrowing rates → more expensive financing → changes in spending and investment → possible changes in company earnings and asset prices.")
    _check("interest", "When borrowing becomes more expensive, which outcome is plausible?", ["Some purchases may be delayed", "Every company's profit must rise", "All stock prices must go down"], "Some purchases may be delayed", "Financing costs can influence borrowing decisions, though the wider market impact varies.")


def _earnings() -> None:
    st.write("An earnings report describes a company's results. An earnings call gives management an opportunity to discuss the period and its outlook.")
    a, b = st.columns(2)
    a.metric("Fictional expected EPS", "$1.00")
    b.metric("Fictional reported EPS", "$1.20", "+20% vs estimate")
    outlook = st.radio("What did management say about next quarter?", ["Guidance was raised", "Guidance was lowered"], horizontal=True)
    if outlook == "Guidance was lowered":
        st.info("The reported quarter beat expectations, but weaker forward guidance may make investors less optimistic. A decline is possible.")
    else:
        st.info("A beat plus raised guidance can improve sentiment, but price movement still depends on what was already expected and other information.")
    st.caption("Fictional scenario. EPS and guidance are only two of many factors investors examine.")
    _check("earnings", "Can a stock fall after reporting better-than-expected EPS?", ["Yes, future expectations may become less optimistic", "No, the stock must rise", "Only if the company pays a dividend"], "Yes, future expectations may become less optimistic", "Future guidance and what the market already expected can outweigh a backward-looking earnings surprise.")







LESSON_RENDERERS = {
    "inflation": render_inflation_lesson,
    "etfs": render_etf_lesson,
    "rrsp": render_rrsp_comparison,
    "paycheque": render_paycheque,
    "growth": render_compound_growth,
    "credit": render_credit_card,
    "tax_brackets": _tax_brackets,
    "tfsa": _tfsa,
    "diversification": render_diversification,
    "prices": render_market_expectations,
    "interest": _interest,
    "earnings": _earnings,
}


def _render_lesson(pathway: dict, lesson_id: str, lesson_title: str) -> None:
    if st.button("← Back to pathway", key="qi_learn_lesson_back"):
        _navigate(pathway["id"])
    if lesson_id == "options_premium":
        render_options_premium_lesson()
    else:
        hero(
            f"QUANT LEARN · {pathway['title'].upper()} · INTERACTIVE LESSON",
            lesson_title, LESSON_SUMMARIES[lesson_id], icon=pathway["icon"],
        )
        with st.container(key="qi_learn_existing_lesson"):
            LESSON_RENDERERS[lesson_id]()
    st.divider()
    st.caption("Educational information only. Not personalized financial, tax, or investment advice.")


def _render_pathway(pathway: dict) -> None:
    if st.button("← All learning paths", key="qi_learn_path_back"):
        _navigate()
    hero(
        "QUANT LEARN · LEARNING PATH",
        pathway["title"], pathway["description"], icon=pathway["icon"],
    )
    st.markdown("### Lessons")
    for number, (lesson_id, title) in enumerate(pathway["lessons"], start=1):
        with st.container(border=True):
            st.markdown(f"**{number:02d}. {title}**")
            if lesson_id in READY_LESSONS:
                st.caption(LESSON_SUMMARIES[lesson_id])
                if st.button("Start interactive lesson", key=f"qi_learn_open_{lesson_id}"):
                    _navigate(pathway["id"], lesson_id)
            else:
                st.caption("Planned lesson · Coming in a later update")


def render_learn_page() -> None:
    """Render the Learn homepage, pathways, or one interactive lesson."""
    st.html(_LEARN_ICON_STYLE)
    enable_learn_style()
    st.session_state.setdefault("qi_learn_pathway", None)
    st.session_state.setdefault("qi_learn_lesson", None)
    chosen_path = st.session_state["qi_learn_pathway"]
    chosen_lesson = st.session_state["qi_learn_lesson"]
    pathway = next((p for p in PATHWAYS if p["id"] == chosen_path), None)

    if pathway is not None and chosen_lesson in READY_LESSONS:
        lesson = next(((lid, title) for lid, title in pathway["lessons"] if lid == chosen_lesson), None)
        if lesson:
            _render_lesson(pathway, *lesson)
            return

    if pathway is not None:
        _render_pathway(pathway)
        return

    hero(
        "QUANT INTELLIGENCE · LEARN",
        "Understand money. Think like an analyst.",
        "Build lasting financial understanding with clear explanations, "
        "beautiful visual examples and interactive lessons. Start from the "
        "basics, then explore how real financial relationships work.",
        icon="book-open",
    )
    featured_lesson()
    if st.button(
        "Start featured options masterclass →",
        key="qi_learn_featured_masterclass_v2", type="primary",
    ):
        _navigate("advanced", "options_premium")
    st.caption(
        "Learn the concepts first; independent recall and deeper challenges "
        "come afterward. Educational examples are clearly identified."
    )
    search = st.text_input(
        "Search learning topics",
        placeholder="Try option premiums, TFSA, earnings, inflation, ETFs...",
    ).strip().lower()
    if search:
        matches = [
            (pathway, lesson_id, title)
            for pathway in PATHWAYS
            for lesson_id, title in pathway["lessons"]
            if search in f"{pathway['title']} {pathway['description']} {title}".lower()
        ]
        st.markdown(f"### Search results ({len(matches)})")
        if not matches:
            st.caption("No matching lessons yet. Try a broader term.")
        for pathway, lesson_id, title in matches:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.caption(pathway["title"])
                if lesson_id in READY_LESSONS:
                    if st.button("Start lesson", key=f"qi_learn_search_{lesson_id}"):
                        _navigate(pathway["id"], lesson_id)
                else:
                    st.caption("Coming soon")
        return

    st.markdown("### Explore learning paths")
    for i in range(0, len(PATHWAYS), 2):
        columns = st.columns(2, gap="medium")
        for col, pathway in zip(columns, PATHWAYS[i:i + 2]):
            with col, st.container(border=True):
                _pathway_heading(pathway, card=True)
                st.write(pathway["description"])
                available = sum(lesson_id in READY_LESSONS for lesson_id, _ in pathway["lessons"])
                st.caption(f"{available} interactive lessons ready" if available else "More lessons coming soon")
                if st.button("Explore path", key=f"qi_learn_path_{pathway['id']}", use_container_width=True):
                    _navigate(pathway["id"])

    st.caption("Built to educate, not to recommend specific investments or financial products.")
