"""A guided beginner-first curriculum without quotes, settings, or third-party feeds."""
from __future__ import annotations

import streamlit as st

from dashboard.learn_design import (
    chapter, concept_grid, concept_pair, forces, hero, insight,
    lesson_journey, lesson_timeline,
)

KEY = "qi_foundations_chapter"
TITLES = (
    "Your money and your goals",
    "Saving, inflation and compounding",
    "What is a stock?",
    "Why stock prices change",
    "Diversification, funds and ETFs",
    "Returns, dividends and fees",
    "Understanding risk",
    "How to research a company",
)
DESCRIPTIONS = (
    "Spending, saving, investing and when you'll need the money.",
    "Time, purchasing power, interest and investment uncertainty.",
    "Companies, shares, profits and what ownership means.",
    "Buyers, sellers, expectations and business news.",
    "Why owning different things can reduce—but not remove—risk.",
    "Price gain versus total return, costs and dividend myths.",
    "Time horizons, losses, debt, leverage and scams.",
    "A beginner's evidence-first research framework.",
)
LEVELS = (
    "START HERE", "BUILD THE BASICS", "UNDERSTAND OWNERSHIP", "UNDERSTAND MARKETS",
    "BUILD A PORTFOLIO", "MEASURE RESULTS", "THINK ABOUT RISK",
    "RESEARCH WITH CONFIDENCE",
)
ICONS = ("wallet", "clock", "building", "activity", "layers",
         "calculator", "shield", "target")


def _p(text: str) -> None:
    """Avoid treating currency markers as Streamlit inline-math delimiters."""
    st.markdown(text.replace("$", r"\$"))


def _one() -> None:
    _p(
        "Imagine you earn **$1,000 after deductions** from a job. Before "
        "considering which stock to buy, ask what this money needs to do. "
        "Some covers essentials today. Some might be needed next month. "
        "Some might support a goal years away."
    )
    concept_pair(
        ("wallet", "Money for today",
         "Pays for housing, food, transport, recurring bills and things you enjoy.",
         "Spending and daily life"),
        ("shield", "Money for later",
         "Supports goals and unexpected expenses. The right place for it "
         "depends on when it must be available.", "Saving for a purpose"),
    )
    _p("### Three uses of money")
    forces((
        ("wallet", "Spending", "You exchange money for something useful or enjoyable now.",
         "Buying groceries or a bus pass."),
        ("shield", "Saving", "You set money aside, often where it stays readily accessible.",
         "An emergency expense or a purchase next month."),
        ("chart-line", "Investing",
         "You buy an asset that might generate income or increase in value. "
         "Unlike ordinary cash savings, its price can decline.",
         "A fund containing shares of many companies."),
    ))
    _p(
        "### The first decision is about time\n\n"
        "If you'll need money for an important payment soon, losing a large "
        "portion just before that payment could cause a problem. A goal far "
        "in the future provides a different time horizon—but does not "
        "make investing risk-free."
    )
    lesson_timeline((
        ("Money arrives", "Income and other resources."),
        ("Money is allocated", "Needs, wants, debts and future goals."),
        ("Money is managed", "Saving or investing based on purpose."),
    ))
    insight(
        "First principle.",
        "Don't begin with 'Which stock will rise?' Begin with "
        "'What is this money for, when do I need it, and what happens if I'm wrong?'",
    )
    with st.expander("A deeper idea: cash flow versus net worth"):
        _p(
            "**Cash flow** describes money coming in and going out during "
            "a period. **Net worth** is the value of assets minus liabilities "
            "at a particular time. A person can earn a large salary yet "
            "have little net worth if expenses and debt consume their income."
        )


def _two() -> None:
    _p(
        "Imagine an item costs **$100** today. One year later, the same "
        "item costs **$103**. Your $100 hasn't vanished, but it no longer "
        "buys the same amount. This is the effect of **inflation** on "
        "purchasing power."
    )
    concept_pair(
        ("wallet", "Nominal money",
         "The number written on an account balance. A cash balance of "
         "$100 is still $100 if nothing changes.", "Amount on the statement"),
        ("activity", "Purchasing power",
         "What that money can buy. Rising prices can reduce purchasing power.",
         "The practical value of money"),
    )
    _p("### Compound growth, step by step")
    _p(
        "Suppose **$1,000** grows at a constant, hypothetical **5% per "
        "year**, with no extra contributions, tax or fees. This is a "
        "mathematical illustration, **not a forecast or guarantee**."
    )
    a, b, c = st.columns(3)
    a.metric("Starting money", "$1,000.00")
    b.metric("After year one", "$1,050.00")
    c.metric("After year two", "$1,102.50")
    lesson_timeline((
        ("Year 0", "$1,000 to start"),
        ("Year 1", "$1,000 plus $50 earned"),
        ("Year 2", "$1,050 plus $52.50 earned"),
    ))
    _p(
        "The second year's increase is **$52.50**, compared with the "
        "first year's **$50**. That's the effect of earning a return "
        "on earlier returns. Investments can also lose money, "
        "and their annual returns are not fixed."
    )
    insight(
        "Growth and inflation pull in different directions.",
        "Compounding can increase the number of dollars. Inflation "
        "changes how much those dollars can buy.",
    )
    with st.expander("Go deeper: debt, emergency funds and savings accounts"):
        _p(
            "High-interest debt and unexpected expenses can create financial "
            "pressure. Before taking investment risk, it helps to understand "
            "your borrowing costs, access to savings and whether an account "
            "has appropriate deposit protection. Rules vary by country."
        )


def _three() -> None:
    _p(
        "A **business** sells goods or services and pays employees, suppliers "
        "and other costs. **A stock is a fractional ownership interest** in "
        "a company. Owning a share doesn't mean you personally receive "
        "a fraction of every sale; the company's results, decisions and "
        "market expectations affect what that share is worth."
    )
    concept_pair(
        ("building", "The company",
         "Operates the business, sells products, pays expenses, invests "
         "in growth and sometimes makes a profit.", "Real economic activity"),
        ("chart-pie", "The share",
         "Represents equity ownership. It can appreciate, decline or "
         "sometimes pay distributions.", "Ownership comes with risk"),
    )
    _p("### Revenue and profit are different")
    _p(
        "A fictional bakery brings in **$10,000** from sales during a month. "
        "Ingredients, rent, wages and other costs total **$8,000**. "
        "Simplified profit is **$2,000**—not $10,000."
    )
    a, b, c = st.columns(3)
    a.metric("Sales (revenue)", "$10,000")
    b.metric("Costs", "$8,000")
    c.metric("Profit", "$2,000")
    _p(
        "A company can raise money by **issuing new shares**. Once shares "
        "trade on an exchange, buying them usually sends money to "
        "another shareholder, not directly to the company. "
        "**Market capitalization** roughly equals stock price multiplied "
        "by shares outstanding."
    )
    insight(
        "Don't judge a share by its price alone.",
        "A $10 stock is not necessarily cheaper than a $100 stock. "
        "The number of outstanding shares and the business's actual "
        "economics both matter.",
    )
    with st.expander("Go deeper: shareholder equity and debt"):
        _p(
            "Companies may raise funds by selling equity or borrowing. "
            "Debt normally creates repayment obligations; shareholders "
            "bear residual ownership risk. A company could become "
            "very successful, or its shareholders could lose most or "
            "all of their investment."
        )


def _four() -> None:
    _p(
        "Stocks trade when buyers and sellers agree on a price. "
        "What they're willing to pay depends on expectations about "
        "the company's future, alternatives, interest rates and risk. "
        "That is why price can change before the business visibly changes."
    )
    lesson_timeline((
        ("Before news", "Investors form expectations."),
        ("New information", "Results, guidance or events surprise investors."),
        ("New prices", "Buying and selling reflect changed expectations."),
    ))
    _p("### Good news can still disappoint")
    _p(
        "Imagine analysts expected a fictional company to earn **$120 million**, "
        "but it reports **$110 million**. That's better than last year's "
        "**$100 million**—yet below what was expected. "
        "Investors might reduce their forecasts and the stock might fall."
    )
    concept_pair(
        ("chart-line", "Historical improvement",
         "Profit increased from $100 million to $110 million.",
         "Better than last year"),
        ("activity", "Expectation missed",
         "The result was below the $120 million investors were anticipating.",
         "Worse than expected"),
    )
    forces((
        ("newspaper", "Company news",
         "Earnings, product launches and competition affect anticipated results.",
         "Good news might already be priced in."),
        ("globe", "Economic conditions",
         "Changes in interest rates, employment and demand change expectations.",
         "Financing costs can change valuations."),
        ("waves", "Uncertainty and sentiment",
         "Fear, liquidity and risk appetite also affect trading.",
         "A rising price does not prove intrinsic value increased."),
    ))
    insight(
        "Markets look forward.",
        "Always ask what happened, what people expected, "
        "and what might change their expectations next.",
    )
    with st.expander("Go deeper: stock price versus business value"):
        _p(
            "Market price is the price of a transaction today. "
            "An estimate of **intrinsic value** attempts to account "
            "for future cash flows and risk. Valuation involves "
            "assumptions, so different analysts may disagree or be wrong."
        )


def _five() -> None:
    _p(
        "Owning just one company's stock exposes you to that company's "
        "specific problems. **Diversification** spreads exposure across "
        "different holdings. It can reduce some risks, but market-wide "
        "losses can still affect many assets at once."
    )
    concept_pair(
        ("target", "Concentrated holdings",
         "A single business event could affect most or all of the portfolio.",
         "Company-specific risk"),
        ("layers", "Diversified holdings",
         "Different companies or asset classes can behave differently "
         "under various conditions.", "Risk spread, not eliminated"),
    )
    _p(
        "### A clear numerical example\n\n"
        "A fictional **$10,000** portfolio puts **20% in one stock**. "
        "That stock falls **30%** while everything else stays unchanged. "
        "The whole portfolio loses **6%**, or **$600**. "
        "If all $10,000 were in the stock, the loss would be $3,000."
    )
    a, b = st.columns(2)
    a.metric("100% in that stock", "−$3,000", "−30%", delta_color="inverse")
    b.metric("20% in that stock", "−$600", "−6%", delta_color="inverse")
    st.caption("Fictional illustration with all other holdings unchanged.")
    _p(
        "### What is an ETF?\n\n"
        "An **exchange-traded fund (ETF)** is a fund whose shares can "
        "generally be bought or sold on an exchange. Many ETFs hold a "
        "basket of assets. But not every ETF is broad or diversified; "
        "some concentrate on one sector, strategy or asset."
    )
    insight(
        "More tickers does not always mean more diversification.",
        "Two funds may own many of the same stocks. "
        "Check the underlying holdings and their overlap.",
    )
    with st.expander("Go deeper: asset allocation and correlation"):
        _p(
            "**Asset allocation** divides investments among categories "
            "such as stocks, bonds and cash. **Correlation** measures "
            "how returns move together. During severe events, many "
            "normally different assets may fall together."
        )


def _six() -> None:
    _p(
        "An investment's outcome isn't only the change in its quoted price. "
        "It may pay a dividend or interest; you may also pay fees and taxes. "
        "**Total return** includes distributions as well as price change."
    )
    _p(
        "### A worked example\n\n"
        "You buy a fictional share for **$100**, sell it for **$108**, "
        "and receive a **$2 dividend**. Before fees and taxes, "
        "your $8 price gain plus $2 cash dividend makes a "
        "**$10 total gain**, or **10%** on the original $100."
    )
    a, b, c = st.columns(3)
    a.metric("Price gain", "$8")
    b.metric("Dividend", "$2")
    c.metric("Total return", "10%")
    concept_pair(
        ("chart-line", "Price return",
         "Measures only the change from $100 to $108: 8%.",
         "Stock price alone"),
        ("wallet", "Total return",
         "Combines the price gain and cash distribution: 10%.",
         "A fuller comparison"),
    )
    _p(
        "Fees, trading spreads and taxes can reduce the amount you keep. "
        "A dividend is not free extra wealth: all else equal, the price "
        "typically adjusts around its ex-dividend date."
    )
    insight(
        "Check what a claimed percentage actually measures.",
        "Does it include distributions? Fees? Inflation? "
        "What period was measured? Percentages without context "
        "can be misleading.",
    )
    with st.expander("Go deeper: losses and recovery"):
        _p(
            "A **50% loss** requires a **100% gain** to return to the "
            "original amount. Falling from $100 to $50 and returning "
            "to $100 illustrates why controlling downside matters."
        )


def _seven() -> None:
    _p(
        "Risk is broader than a changing stock price. It includes "
        "the possibility of permanent loss, needing cash at the wrong "
        "time, using borrowed money, poor information and outright fraud."
    )
    forces((
        ("clock", "Time-horizon risk",
         "A large loss before a near-term payment may force a bad sale.",
         "Next month's tuition differs from retirement in decades."),
        ("layers", "Concentration risk",
         "One company, sector or overlapping fund can dominate results.",
         "Several tickers may share the same risk."),
        ("wallet", "Liquidity and borrowing risk",
         "Some products are hard to sell; leverage can magnify losses.",
         "Margin creates obligations beyond price volatility."),
        ("shield", "Information and fraud risk",
         "Misleading returns, fabricated records and hidden fees matter.",
         "Be skeptical of guaranteed high returns with no risk."),
    ))
    concept_pair(
        ("gem", "Ability to take risk",
         "Can you financially withstand a loss and still meet your needs?",
         "Your financial capacity"),
        ("activity", "Willingness to take risk",
         "Can you tolerate fluctuations without making rushed decisions?",
         "Your emotional comfort"),
    )
    insight(
        "Think about the downside first.",
        "Before anticipating a gain, ask what happens if your "
        "assumption is wrong and whether you could afford that outcome.",
    )
    with st.expander("Go deeper: volatility versus permanent loss"):
        _p(
            "Volatility measures fluctuations, not every kind of risk. "
            "A low-volatility asset can still be dangerous, while "
            "a volatile one may have a sound business behind it. "
            "Liquidity, solvency and valuation matter too."
        )


def _eight() -> None:
    _p(
        "The aim of researching a company isn't to find a guaranteed "
        "winner. It's to ask better questions, check evidence and "
        "understand what could prove your assumptions wrong."
    )
    lesson_timeline((
        ("Understand", "What does the business sell, and to whom?"),
        ("Measure", "Revenue, profit, cash flow, debt and share count."),
        ("Challenge", "What risks and assumptions could change the conclusion?"),
    ))
    forces((
        ("building", "Understand the business",
         "Identify the customers, product, competitors and revenue model.",
         "Can you explain the business in plain language?"),
        ("calculator", "Read financial statements",
         "Look for patterns in sales, profit, cash flow and borrowing.",
         "Profit and cash are not interchangeable."),
        ("target", "Examine price and risk",
         "Compare the market price with assumptions about future performance.",
         "No single ratio proves a stock is cheap."),
        ("newspaper", "Check primary evidence",
         "Use financial filings, reliable sources and opposing viewpoints.",
         "Distinguish facts from forecasts and promotion."),
    ))
    _p(
        "### A small fictional research case\n\n"
        "A company reports higher revenue but lower profits and weaker "
        "cash flow because costs are rising. That doesn't automatically "
        "make the stock good or bad. A careful learner asks why margins "
        "fell, whether spending is temporary, and what future results "
        "are already implied by the market price."
    )
    insight(
        "A stronger question than 'Will it go up?'",
        "Ask what evidence supports your view, what would disprove "
        "it, and what risk you are accepting.",
    )
    with st.expander("Where your learning goes next"):
        _p(
            "The earlier learning labs on ETFs, diversification, market "
            "expectations and earnings expand these foundations. "
            "Once you understand businesses and portfolio risk, "
            "Advanced Finance introduces options and derivatives."
        )


RENDERERS = (_one, _two, _three, _four, _five, _six, _seven, _eight)


def _change(page: int) -> None:
    st.session_state[KEY] = page
    st.session_state["qi_learn_scroll_serial"] = (
        st.session_state.get("qi_learn_scroll_serial", 0) + 1
    )


def render_foundations_lesson() -> None:
    """One coherent guided course, with overview and independent chapters."""
    page = st.session_state.setdefault(KEY, 0)
    if type(page) is not int or not 0 <= page <= len(TITLES):
        page = 0
        st.session_state[KEY] = 0

    with st.container(key="qi_foundations_reading"):
        if page == 0:
            hero(
                "QUANT LEARN · START HERE",
                "Money and Investing: From Zero",
                "Start with everyday financial decisions. Learn what stocks "
                "actually are, why prices change, how diversification works, "
                "and how to reason about risk. No experience required.",
                icon="book-open",
            )
            st.caption("8 beginner chapters · Guided demonstrations · No sliders · No trading")
            concept_grid((
                ("wallet", "Start with money",
                 "Spending, saving, inflation and goals.", "Plain English first"),
                ("chart-line", "Learn stocks",
                 "Companies, shares and how markets operate.", "No jargon assumed"),
                ("layers", "Understand portfolios",
                 "Diversification, fees and returns with worked examples.", "Clear visual models"),
                ("shield", "Practice good judgment",
                 "Risk, evidence and sensible research questions.", "No stock tips"),
            ))
            _p("### Your learning journey")
            lesson_journey(TITLES, DESCRIPTIONS)
        else:
            chapter(
                page, len(TITLES), LEVELS[page - 1],
                TITLES[page - 1], DESCRIPTIONS[page - 1],
                icon=("wallet","clock","building","activity","layers",
                      "calculator","shield","target")[page - 1],
            )
            RENDERERS[page - 1]()
    st.divider()
    if page == 0:
        with st.container(key="qi_foundations_start_button"):
            st.button(
                "Start Chapter 1 →", on_click=_change, args=(1,),
                key="qi_foundations_next", type="primary", use_container_width=True,
            )
    elif page < len(TITLES):
        left, right = st.columns(2)
        with left:
            st.button(
                "← Course overview" if page == 1 else "← Previous chapter",
                key="qi_foundations_previous", on_click=_change,
                args=(page - 1,), use_container_width=True,
            )
        with right:
            st.button(
                "Next chapter →", key="qi_foundations_next",
                on_click=_change, args=(page + 1,),
                type="primary", use_container_width=True,
            )
    else:
        st.button(
            "← Previous chapter", key="qi_foundations_previous",
            on_click=_change, args=(page - 1,), use_container_width=True,
        )
        st.success(
            "You've finished the guided introduction. "
            "Reading is the first step, not a score or proof of mastery."
        )
    st.caption("Fictional educational examples. No market feeds or personalized advice.")
