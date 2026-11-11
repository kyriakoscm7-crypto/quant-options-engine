"""Eight-chapter guided options-premium lesson for Quant Intelligence Learn.

Teaching precedes recall. No quote API, live stock data, tracking, or calls to
external services. Every number is fictional or computed by the validated
zero-rate, zero-dividend European Black-Scholes reference model.
"""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.education.options_premium import (
    at_the_money_time_curve,
    expiration_profit,
    theoretical_option,
)
from dashboard.learn_design import (
    chapter,
    concept_grid,
    concept_pair,
    forces,
    hero,
    insight,
    lesson_journey,
    premium_bar,
)
from dashboard.learn_navigation import request_top

CHAPTER_TITLES = (
    "What are you buying?",
    "What makes up the premium?",
    "What moves an option premium?",
    "See the forces change an option price",
    "Why time decay speeds up",
    "How a call can fall when the stock rises",
    "Understanding the Greeks",
    "Payoff, premium and profit",
)
COUNT = len(CHAPTER_TITLES)
CHAPTER_KEY = "qi_options_premium_chapter_v2"
CHAPTER_DESCRIPTIONS = (
    "Calls, puts, strikes, premiums and the contract itself.",
    "Intrinsic versus time value, moneyness and two worked examples.",
    "Underlying prices, strike, time, expected volatility and more.",
    "Change one assumption at a time and observe the premium.",
    "Theta, remaining opportunity and expiration risk.",
    "See how implied volatility can overwhelm a favorable move.",
    "Delta, gamma, theta, vega and rho—without memorizing formulas.",
    "Separate the premium you paid from payoff and actual profit.",
)


def _prose(markdown_text: str) -> None:
    """Treat dollars as currency, never as Streamlit inline LaTeX delimiters.

    All inputs here are authored lesson text, not user-provided HTML.
    """
    st.markdown(markdown_text.replace("$", r"\$"))


def _caption(markdown_text: str) -> None:
    st.caption(markdown_text.replace("$", r"\$"))


def _set_chapter(value: int) -> None:
    st.session_state[CHAPTER_KEY] = min(COUNT, max(0, value))
    request_top()


def _chart_style(fig: go.Figure, *, x_title: str, y_title: str) -> None:
    fig.update_layout(
        template="plotly_dark",
        height=360,
        paper_bgcolor="#0C1425",
        plot_bgcolor="#0C1425",
        margin={"l": 20, "r": 18, "t": 26, "b": 35},
        font={"color": "#DAE2F1", "size": 12},
        showlegend=True,
        legend={"orientation": "h", "y": 1.17},
        xaxis_title=x_title,
        yaxis_title=y_title,
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#24344E", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#24344E", zeroline=False)


def _overview() -> None:
    hero(
        "QUANT LEARN · GUIDED MASTERCLASS",
        "Why do option premiums change?",
        "Start with a contract worth only a few dollars and discover why "
        "its price can change dramatically, even when the stock barely moves. "
        "Build your understanding through clear explanations and hands-on experiments.",
        icon="gem",
    )
    _caption("8 guided chapters · Beginner-friendly · Interactive models · No live quotes")
    st.button(
        "Start learning — Chapter 1 →",
        key="qi_opt_course_start_hero",
        on_click=_set_chapter, args=(1,),
        type="primary", use_container_width=True,
    )
    _prose("### What this lesson will help you understand")
    concept_grid((
        ("book-open", "Start from zero",
         "What calls and puts are, how contracts work, and what you pay.",
         "Plain-English explanations"),
        ("activity", "Understand the premium",
         "Discover intrinsic value, time value, and why options have different prices.",
         "Large worked examples"),
        ("layers", "See the forces interact",
         "Experiment with fictional inputs and watch theoretical values respond.",
         "Live calculations"),
        ("shield", "Understand real risks",
         "Find out why guessing the stock direction correctly isn't enough.",
         "Risk-aware education"),
    ))
    _prose("### Your learning journey")
    _prose(
        "Eight short, connected chapters build from first principles to "
        "practical option-price reasoning. No prior trading experience is required."
    )
    lesson_journey(CHAPTER_TITLES, CHAPTER_DESCRIPTIONS)
    insight(
        "How to get the most out of it.",
        "Read the worked example before experimenting with its controls. "
        "Later chapters build on the first ones. The separate independent "
        "practice stage follows the lesson; reading alone isn't proof of mastery.",
    )


def _chapter_one() -> None:
    chapter(1, COUNT, "FOUNDATIONS", CHAPTER_TITLES[0],
            "Before pricing an option, understand the right that the contract gives you.",
            icon="book-open")
    _prose(
        "Imagine a stock is currently worth **$100**. You think it might rise "
        "over the next month, but buying 100 shares would cost $10,000."
    )
    _prose(
        "A **call option** gives its holder the right, but not the obligation, "
        "to buy at an agreed price (the **strike**) before or at expiration, "
        "depending on the contract. A **put option** gives the right to sell."
    )
    concept_pair(
        ("chart-line", "Call = right to BUY",
         "A call becomes more attractive when the stock rises relative to its strike.",
         "The holder chooses whether to exercise"),
        ("shield", "Put = right to SELL",
         "A put becomes more attractive when the stock falls relative to its strike.",
         "The seller has a corresponding obligation"),
    )
    _prose("### The anatomy of your first call")
    with st.container(border=True):
        a, b, c = st.columns(3)
        a.metric("Stock price", "$100")
        b.metric("Strike price", "$100")
        c.metric("Days remaining", "30")
        _prose("**Suppose the call is offered at a $3.50 premium per share.**")
        premium_bar(3.50, 0.0)
        _prose(
            "A standard US equity option typically represents **100 shares**. "
            "Buying one contract at $3.50 per share therefore costs "
            "**$3.50 × 100 = $350**, before fees. Contract multipliers can vary."
        )
    insight(
        "One critical distinction.",
        "The $3.50 premium is the price of the option, not the price of the stock. "
        "Paying the premium does not guarantee any profit. A long option buyer "
        "can lose the entire premium.",
    )
    _prose("### What happens after you buy it?")
    _prose(
        "While the contract exists, its market premium can rise or fall. "
        "You may be able to sell the option instead of exercising it. "
        "At expiration, any exercise value depends on the stock price and the strike."
    )


def _chapter_two() -> None:
    chapter(2, COUNT, "UNDERSTAND VALUE", CHAPTER_TITLES[1],
            "An option's premium can be understood as exercise value plus value beyond exercise.",
            icon="gem")
    _prose("### Option premium = intrinsic value + time value")
    concept_pair(
        ("gem", "Intrinsic value",
         "How much the option is in the money. For a call, it is the stock price minus the strike, but never below zero.",
         "Value it already has"),
        ("hourglass", "Time value",
         "The part of the premium above intrinsic value. It reflects remaining possibilities and pricing conditions.",
         "Value of what might happen"),
    )
    _prose("### A big, simple example")
    _prose(
        "A call has a **$100 strike** and its stock trades at **$105**. "
        "Its intrinsic value is **$105 − $100 = $5 per share**."
    )
    _prose(
        "If the call trades for **$8 per share**, the remaining **$3** is "
        "time value. Here's the complete premium:"
    )
    premium_bar(8.0, 5.0)
    insight(
        "Why this matters.",
        "A call can have zero intrinsic value yet still be worth money before "
        "expiration. Someone may pay for the possibility that it becomes profitable "
        "to exercise later.",
    )
    _prose("### Three terms you'll see constantly")
    with st.container(border=True):
        _prose(
            "**In the money (ITM):** A $100-strike call when the stock is $110 "
            "already has $10 of intrinsic value."
        )
        st.divider()
        _prose(
            "**At the money (ATM):** A $100-strike call when the stock is $100 "
            "has zero intrinsic value."
        )
        st.divider()
        _prose(
            "**Out of the money (OTM):** A $100-strike call when the stock is $90 "
            "has zero intrinsic value."
        )
    _caption(
        "For puts, the direction reverses: a put has intrinsic value if the stock "
        "is below its strike. Intrinsic value is not the same as profit after premium."
    )


def _chapter_three() -> None:
    chapter(3, COUNT, "CONNECT THE IDEAS", CHAPTER_TITLES[2],
            "Four major forces explain much of why a premium can change from one moment to the next.",
            icon="activity")
    forces((
        ("chart-line", "The stock price changes",
         "All else equal, a higher stock price increases call value and decreases "
         "put value. The right to buy at a fixed strike becomes more attractive as the stock rises.",
         "Example: A $100-strike call has $10 intrinsic value if its stock reaches $110."),
        ("clock", "Time passes",
         "An option has an expiration date. Losing remaining time generally "
         "reduces its time value, with the other factors held constant.",
         "Example: An otherwise identical option expiring tomorrow usually has "
         "less time value than one expiring in six months."),
        ("waves", "Expected volatility changes",
         "When expected movement rises, both calls and puts generally gain "
         "theoretical value, all else equal. Greater volatility does not imply an upward direction.",
         "Example: Before a major announcement, option premiums may be elevated "
         "because the market expects a large move."),
        ("target", "The strike price differs",
         "A $90-strike call is a different contract from a $110-strike call. "
         "With the stock at $100, the first has intrinsic value and the second does not.",
         "Example: Compare call strikes of $90, $100 and $110 on the same hypothetical stock."),
    ))
    _prose("### Two additional influences")
    concept_pair(
        ("landmark", "Interest rates",
         "Risk-free rates affect the present value of an option's future exercise cost. "
         "They are part of standard option-pricing models.",
         "Often discussed using rho"),
        ("chart-pie", "Expected dividends",
         "A stock's expected dividend payments can affect forward prices and "
         "therefore call and put valuations.",
         "Important for dividend-paying stocks"),
    )
    insight(
        "An option premium is not controlled by one factor.",
        "Stock price, time, volatility, interest rates and dividends can change "
        "at the same time. The net outcome depends on which effects dominate.",
    )


def _chapter_four() -> None:
    chapter(4, COUNT, "SEE IT IN ACTION", CHAPTER_TITLES[3],
            "Watch three controlled demonstrations with all assumptions explained for you.",
            icon="calculator")
    _prose(
        "You shouldn't have to choose complicated model settings to learn. "
        "We will walk through **three ready-made comparisons**. "
        "Everything uses a fictional **$100 strike** and a simplified "
        "European-style theoretical model with zero interest and dividends."
    )
    _prose(
        "The volatility percentages below are **arbitrary teaching assumptions**—"
        "not normal, average, current or recommended values. "
        "We change one factor at a time to show why the numbers respond."
    )
    base = theoretical_option(100, 100, 30, 30, "call")
    higher_stock = theoretical_option(110, 100, 30, 30, "call")
    _prose("### 1. The stock rises")
    _prose(
        "Start with an at-the-money call. Now imagine its stock rises "
        "from $100 to $110 while the 30 days remaining and the assumed "
        "volatility stay exactly the same."
    )
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        st.caption("BEFORE · Stock $100")
        st.metric("Modeled call premium / share", f"${base.premium:.2f}")
        st.caption("Zero intrinsic value; premium is time value")
    with right, st.container(border=True):
        st.caption("AFTER · Stock $110")
        st.metric("Modeled call premium / share", f"${higher_stock.premium:.2f}")
        st.caption("At least $10 intrinsic value, plus remaining time value")
    premium_bar(higher_stock.premium, higher_stock.intrinsic)
    insight(
        "What changed?",
        "The right to buy at $100 became more useful because shares now cost "
        "$110. The model's premium increased. This does not tell us "
        "what a real option quote would be.",
    )
    _prose("### 2. Time passes")
    far = theoretical_option(100, 100, 90, 30, "call")
    near = theoretical_option(100, 100, 7, 30, "call")
    _prose(
        "Next, return the stock to $100. Keep the assumed volatility "
        "unchanged, and compare the same call with 90 days left versus "
        "only 7 days left."
    )
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        st.caption("MORE TIME · 90 days")
        st.metric("Modeled premium / share", f"${far.premium:.2f}")
    with right, st.container(border=True):
        st.caption("LESS TIME · 7 days")
        st.metric("Modeled premium / share", f"${near.premium:.2f}")
    _prose(
        "There are fewer opportunities for the stock to move before "
        "expiration. In this comparison the option has no intrinsic "
        "value, and its remaining time value becomes smaller."
    )
    _prose("### 3. Expected movement changes")
    calm = theoretical_option(100, 100, 30, 20, "call")
    uncertain = theoretical_option(100, 100, 30, 50, "call")
    _prose(
        "**Volatility** describes how widely prices may move. "
        "To isolate its effect, hold the stock at $100, strike at $100 "
        "and time remaining at 30 days. Compare two *illustrative* "
        "assumed volatility levels: 20% and 50% annually."
    )
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        st.caption("SCENARIO A · 20% assumed volatility")
        st.metric("Modeled premium / share", f"${calm.premium:.2f}")
    with right, st.container(border=True):
        st.caption("SCENARIO B · 50% assumed volatility")
        st.metric("Modeled premium / share", f"${uncertain.premium:.2f}")
    insight(
        "Higher expected movement, higher model premium.",
        "The buyer can benefit from a large favorable move but does "
        "not have to exercise after an unfavorable move. Increased "
        "uncertainty generally raises the theoretical values of both "
        "calls and puts, holding other assumptions fixed.",
    )
    _prose("### What about a put?")
    put_100 = theoretical_option(100, 100, 30, 30, "put")
    put_90 = theoretical_option(90, 100, 30, 30, "put")
    _prose(
        f"A put has the opposite stock-price sensitivity: with the "
        f"same $100 strike, 30 days and 30% illustrative volatility, "
        f"the model gives a premium of **${put_100.premium:.2f}** "
        f"when the stock is $100, versus **${put_90.premium:.2f}** "
        f"when the stock falls to $90."
    )
    _caption(
        "All examples are hypothetical model outputs, not option quotes. "
        "Actual equity options often allow early exercise, and prices "
        "can differ because of interest, dividends, spreads and supply/demand."
    )


def _chapter_five() -> None:
    chapter(5, COUNT, "UNDERSTANDING TIME", CHAPTER_TITLES[4],
            "Time value usually does not disappear in equal daily amounts.",
            icon="hourglass")
    _prose(
        "Time remaining represents opportunity for the stock to move. "
        "For an at-the-money option, theoretical time value often erodes faster "
        "as expiration gets close, if all other factors remain fixed."
    )
    days = list(range(0, 181, 5))
    premiums = at_the_money_time_curve(days)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=days, y=premiums, name="Call time value",
        mode="lines", line={"color": "#FF78B7", "width": 4},
        fill="tozeroy", fillcolor="rgba(255,120,183,0.09)",
        hovertemplate="%{x} days remaining<br>$%{y:.2f} per share<extra></extra>",
    ))
    _chart_style(
        fig, x_title="Days remaining until expiration",
        y_title="Theoretical time value per share ($)",
    )
    fig.update_xaxes(autorange="reversed")
    with st.container(border=True):
        _prose("**Watch an at-the-money call approach expiration**")
        st.plotly_chart(
            fig, width="stretch", key="qi_opt_course_decay_chart_v2",
            config={"displaylogo": False, "scrollZoom": False},
        )
        _caption(
            "Illustrative $100 stock / $100 strike, constant 30% assumed volatility, "
            "zero rates and dividends. The x-axis runs from 180 days to expiration."
        )
    concept_pair(
        ("clock", "Theta",
         "Theta describes theoretical sensitivity to a small change in time remaining. "
         "It is commonly quoted per day.",
         "The time-decay Greek"),
        ("shield", "A key limitation",
         "A real option's value can rise despite the passage of time if "
         "the stock moves favorably or implied volatility increases enough.",
         "Time is only one influence"),
    )
    insight(
        "Why short-dated options are risky.",
        "A low dollar premium does not automatically mean a good bargain. "
        "A short-dated option can lose its entire purchase price quickly.",
    )


def _chapter_six() -> None:
    chapter(6, COUNT, "APPLIED REASONING", CHAPTER_TITLES[5],
            "A favorable stock move does not guarantee a profitable option trade.",
            icon="activity")
    _prose(
        "Imagine a fictional company has an important announcement tomorrow. "
        "Before the event, traders expect substantial movement, so the option's "
        "assumed implied volatility is high."
    )
    before = theoretical_option(100, 100, 30, 60, "call")
    after = theoretical_option(103, 100, 29, 25, "call")
    left, right = st.columns(2, gap="medium")
    with left, st.container(border=True):
        _prose("#### Before the event")
        _caption("Stock $100 · 30 days · 60% assumed volatility")
        st.metric("Modeled call premium", f"${before.premium:,.2f}")
    with right, st.container(border=True):
        _prose("#### After the event")
        _caption("Stock $103 · 29 days · 25% assumed volatility")
        st.metric("Modeled call premium", f"${after.premium:,.2f}")
    _prose("### What changed?")
    concept_pair(
        ("chart-line", "Stock rose $3",
         "The call benefited from the stock moving above the $100 strike.",
         "Direction was favorable"),
        ("waves", "Expected volatility fell",
         "The much lower assumed volatility reduced the remaining time value.",
         "Uncertainty dropped"),
    )
    difference = after.premium - before.premium
    st.metric(
        "Change in theoretical option premium / share",
        f"{difference:+.2f} dollars",
    )
    insight(
        "A key lesson: the stock can rise while the call loses value.",
        "In this fictional example, a volatility decline overwhelms the "
        "favorable directional movement. This possibility is often called IV crush.",
    )
    _caption(
        "A stylized two-state comparison, not an actual announcement prediction. "
        "Rates and dividends are fixed at zero. An options buyer's realized "
        "profit also depends on their actual entry/exit price and costs."
    )


def _chapter_seven() -> None:
    chapter(7, COUNT, "ANALYST VOCABULARY", CHAPTER_TITLES[6],
            "The Greeks describe individual sensitivities of theoretical option prices.",
            icon="layers")
    _prose(
        "By this point you know why an option can change value. Analysts use "
        "the **Greeks** to estimate how responsive a theoretical premium is "
        "to small changes in its inputs."
    )
    forces((
        ("chart-line", "Delta (Δ)",
         "How much the theoretical premium may change for a $1 change in the stock, "
         "holding other inputs constant.",
         "Stock-price sensitivity; typically positive for calls and negative for puts."),
        ("activity", "Gamma (Γ)",
         "How delta changes when the underlying stock price moves.",
         "Large gamma means delta can change rapidly."),
        ("hourglass", "Theta (Θ)",
         "How theoretical premium responds to the passage of time.",
         "For a typical long at-the-money option, theta is negative."),
        ("waves", "Vega",
         "How theoretical premium responds to an absolute one-percentage-point "
         "change in assumed implied volatility.",
         "An option with positive vega tends to gain value when IV rises."),
        ("landmark", "Rho (ρ)",
         "How theoretical value changes with an interest-rate adjustment.",
         "Typically less prominent in short-dated beginner examples."),
    ))
    insight(
        "Sensitivity is not destiny.",
        "Greeks are local estimates and can change when market conditions change. "
        "They are not guaranteed future profit and loss. You can explore these "
        "ideas further in Quant Lab's Greeks Analysis and Volatility Lab.",
    )


def _chapter_eight() -> None:
    chapter(8, COUNT, "FROM THEORY TO PAYOFF", CHAPTER_TITLES[7],
            "Separate a changing option premium from what you ultimately gain or lose.",
            icon="target")
    _prose(
        "Suppose you pay a **$6 premium per share** to buy a fictional "
        "**$100-strike call**. Ignore trading fees for this lesson. "
        "At expiration, the call's exercise payoff depends on "
        "how far the stock price finishes above the strike."
    )
    _prose(
        "**Call payoff at expiration = max(stock price − strike, $0)**\n\n"
        "**Net profit = payoff − original premium paid**"
    )
    _prose("### Four outcomes from the same contract")
    _prose(
        "The premium paid at entry is always $6. "
        "What changes below is **only the ending stock price**."
    )
    st.table([
        {"Ending stock price": "$95", "Payoff / share": "$0", "Net result / share": "−$6"},
        {"Ending stock price": "$104", "Payoff / share": "$4", "Net result / share": "−$2"},
        {"Ending stock price": "$106", "Payoff / share": "$6", "Net result / share": "$0"},
        {"Ending stock price": "$115", "Payoff / share": "$15", "Net result / share": "+$9"},
    ])
    _prose(
        "At **$104**, the call has value at expiration, but that value "
        "does not recover the $6 paid. At **$106**, the payoff exactly "
        "recovers the original premium. That's break-even, before fees."
    )
    stocks = list(range(80, 131))
    values = [expiration_profit(s, 100, 6, "call") for s in stocks]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=stocks, y=values, mode="lines", name="Long call net P/L",
        line={"width": 4, "color": "#FF78B7"},
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#8192AD")
    fig.add_vline(x=106, line_dash="dot", line_color="#8192AD")
    _chart_style(
        fig, x_title="Stock price at expiration ($)",
        y_title="Net profit / loss per share ($)",
    )
    with st.container(border=True):
        _prose("**Visualize the break-even point**")
        st.plotly_chart(
            fig, width="stretch", key="qi_opt_course_payoff_chart_v2",
            config={"displaylogo": False, "scrollZoom": False},
        )
        _caption(
            "Pink line = payoff minus the original premium. "
            "The horizontal line shows zero profit; the vertical line "
            "marks the $106 break-even stock price."
        )
    insight(
        "Predicting the right direction is not enough.",
        "An option can finish in the money while still producing a loss. "
        "The purchase price, time, volatility and final payoff all matter.",
    )
    _prose("### What you've learned")
    _prose(
        "You can now explain why a premium changes, separate intrinsic "
        "from time value, understand basic Greek sensitivities, "
        "and distinguish an option's price from its payoff and net profit."
    )
    _caption(
        "The buyer of a plain long option generally risks the premium "
        "paid plus costs. Uncovered short-option sellers can face much "
        "larger losses. Educational examples, not trading advice."
    )
    st.link_button(
        "Further reading — Options Industry Council",
        "https://www.optionseducation.org/",
    )


_CHAPTER_RENDERERS = (
    _chapter_one,
    _chapter_two,
    _chapter_three,
    _chapter_four,
    _chapter_five,
    _chapter_six,
    _chapter_seven,
    _chapter_eight,
)


def render_options_premium_lesson() -> None:
    """Render a readable lesson, not a prematurely presented recall quiz."""
    page = st.session_state.setdefault(CHAPTER_KEY, 0)
    if type(page) is not int or not 0 <= page <= COUNT:
        _set_chapter(0)
        page = 0

    with st.container(key="qi_opt_course_reading"):
        if page == 0:
            _overview()
        else:
            _CHAPTER_RENDERERS[page - 1]()
            from dashboard.options_premium_depth import render_chapter_depth
            render_chapter_depth(page)

    st.divider()
    if page == 0:
        with st.container(key="qi_opt_course_start_bottom"):
            st.button(
                "Begin chapter 1 →",
                on_click=_set_chapter, args=(1,),
                key="qi_opt_course_next_v2",
                type="primary", use_container_width=True,
            )
    elif page < COUNT:
        left, right = st.columns(2, gap="medium")
        with left:
            label = "← Back to lesson overview" if page == 1 else "← Previous chapter"
            st.button(
                label,
                on_click=_set_chapter, args=(page - 1,),
                key="qi_opt_course_previous_v2",
                use_container_width=True,
            )
        with right:
            st.button(
                "Next chapter →",
                on_click=_set_chapter, args=(page + 1,),
                key="qi_opt_course_next_v2",
                type="primary", use_container_width=True,
            )
    else:
        st.button(
            "← Previous chapter",
            on_click=_set_chapter, args=(COUNT - 1,),
            key="qi_opt_course_previous_v2", use_container_width=True,
        )
        st.success(
            "All eight chapters viewed. You're ready for independent practice. "
            "Reading completion is not a mastery score."
        )
    _caption(
        "All illustrations and modeled option prices are hypothetical. "
        "No third-party market-data APIs, brokerage services, or personalized "
        "investment recommendations are used."
    )
