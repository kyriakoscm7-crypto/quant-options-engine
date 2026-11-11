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
    lesson_timeline,
    premium_bar,
)

CHAPTER_TITLES = (
    "What are you buying?",
    "What makes up the premium?",
    "What moves an option premium?",
    "Experiment with option prices",
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
    st.markdown(markdown_text.replace("$", r"\\$"))


def _caption(markdown_text: str) -> None:
    st.caption(markdown_text.replace("$", r"\\$"))


def _set_chapter(value: int) -> None:
    st.session_state[CHAPTER_KEY] = min(COUNT, max(0, value))


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
    chapter(4, COUNT, "INTERACTIVE EXPLORATION", CHAPTER_TITLES[3],
            "Change one input at a time to see how option value responds.",
            icon="calculator")
    _prose(
        "Below is a **European-style theoretical pricing model** with a "
        "$100 strike, no interest or dividends and a 365-day year. "
        "It illustrates relationships, not live prices or tradable quotes."
    )
    with st.container(border=True):
        choice = st.radio(
            "Which option do you want to explore?",
            ["Call", "Put"], key="qi_opt_course_kind_v2", horizontal=True,
        )
        stock = st.slider(
            "Stock price ($)", 75, 125, 100, 1,
            key="qi_opt_course_stock_v2",
        )
        remaining = st.slider(
            "Days remaining", 1, 180, 30, 1,
            key="qi_opt_course_days_v2",
        )
        assumed_vol = st.slider(
            "Assumed annualized volatility (%)", 10, 80, 30, 5,
            key="qi_opt_course_vol_v2",
        )
        value = theoretical_option(
            stock, 100, remaining, assumed_vol, choice.lower()
        )
        _prose("#### Theoretical premium")
        premium_bar(max(value.premium, 0.0000001), value.intrinsic)
        a, b = st.columns(2)
        a.metric("Intrinsic value / share", f"${value.intrinsic:,.2f}")
        b.metric("Time value / share", f"${value.time_value:,.2f}")
        _caption(
            f"Model premium: ${value.premium:,.2f} per share (before spread and fees). "
            "Time value is the modeled premium minus intrinsic value."
        )
        if choice == "Call":
            if stock > 100:
                st.info("This call is in the money: the right to buy at $100 is valuable now.")
            else:
                st.info("This call has no intrinsic value; remaining time can still give it value.")
        elif stock < 100:
            st.info("This put is in the money: the right to sell at $100 is valuable now.")
        else:
            st.info("This put has no intrinsic value; remaining time can still give it value.")
    _prose("### Explore three cause-and-effect relationships")
    _prose(
        "**Stock price:** Hold time and volatility fixed. Move the stock slider "
        "upward. Compare a call against a put."
    )
    _prose(
        "**Time:** Return the stock to $100 and shorten expiration. "
        "Notice what happens to the time-value portion."
    )
    _prose(
        "**Volatility:** Return to 30 days, then increase the assumed volatility. "
        "Observe how both calls and puts respond."
    )
    insight(
        "This model is not a prediction.",
        "Actual US equity options commonly permit early exercise and trade with "
        "bid–ask spreads. This educational model uses European expiration rules "
        "and zero rates/dividends to isolate the core forces.",
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
            "Learn the difference between a changing market premium and the profit from a completed trade.",
            icon="target")
    _prose(
        "Suppose you buy a fictional **$100-strike call for a $6 premium per "
        "share**. At expiration, its exercise payoff depends on the amount "
        "by which the stock exceeds $100."
    )
    _prose(
        "**Call payoff = max(stock at expiration − strike, $0)**\n\n"
        "**Call profit = payoff − premium paid** (ignoring fees)"
    )
    stock = st.slider(
        "Stock price at expiration ($)", 80, 130, 110, 1,
        key="qi_opt_course_expiry_stock_v2",
    )
    payoff = max(stock - 100, 0)
    profit = expiration_profit(stock, 100, 6, "call")
    a, b, c = st.columns(3)
    a.metric("Payoff / share", f"${payoff:,.2f}")
    b.metric("Net P/L / share", f"{profit:+.2f} dollars")
    c.metric("Break-even stock price", "$106")
    stocks = list(range(80, 131))
    values = [expiration_profit(s, 100, 6, "call") for s in stocks]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=stocks, y=values, mode="lines", name="Long call net P/L",
        line={"width": 4, "color": "#FF78B7"},
    ))
    fig.add_trace(go.Scatter(
        x=[stock], y=[profit], mode="markers",
        name="Selected expiration price",
        marker={"size": 12, "color": "#80A8F5"},
    ))
    fig.add_hline(y=0, line_dash="dot", line_color="#8192AD")
    fig.add_vline(x=106, line_dash="dot", line_color="#8192AD")
    _chart_style(
        fig, x_title="Stock price at expiration ($)",
        y_title="Net profit / loss per share ($)",
    )
    with st.container(border=True):
        st.plotly_chart(
            fig, width="stretch", key="qi_opt_course_payoff_chart_v2",
            config={"displaylogo": False, "scrollZoom": False},
        )
        _caption(
            "Pink = payoff minus initial premium, not the call's market value "
            "before expiration. Blue dot = selected ending stock price."
        )
    _caption(
        "The $6 is the original premium paid, not a current quote or time value. "
        "At expiration, option time value is zero."
    )
    insight(
        "A correct prediction about direction is not enough.",
        "A call can finish in the money and still lose money after accounting "
        "for the premium paid. Here, a $104 ending stock price pays $4 but "
        "produces a $2 loss per share before fees.",
    )
    _prose("### Before you move on")
    _prose(
        "You can now explain why premiums change, distinguish intrinsic and "
        "time value, describe delta/theta/vega, and reason about trade outcomes "
        "without confusing premiums, payoffs and profits."
    )
    _caption(
        "Long-option maximum loss is generally the premium paid plus fees. "
        "Different positions, including written options, can have much greater risks. "
        "This lesson is educational and does not recommend trading."
    )
    st.link_button(
        "Learn more — Options Industry Council",
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
        if st.button(
            "← Previous chapter",
            on_click=_set_chapter, args=(COUNT - 1,),
            key="qi_opt_course_previous_v2", use_container_width=True,
        ):
            pass
        st.success(
            "All eight chapters viewed. You're ready for independent practice. "
            "Reading completion is not a mastery score."
        )
    _caption(
        "All illustrations and modeled option prices are hypothetical. "
        "No third-party market-data APIs, brokerage services, or personalized "
        "investment recommendations are used."
    )
