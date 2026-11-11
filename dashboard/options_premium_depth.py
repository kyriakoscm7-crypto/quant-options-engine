"""Further explanations for each Quant Learn options-premium chapter.

Core teaching renders first. Optional nuance follows without quizzes.
All examples are fictional, without external market data.
"""
from __future__ import annotations

import streamlit as st

from app.education.options_premium import theoretical_option
from dashboard.learn_design import concept_pair, insight, lesson_timeline, premium_bar


def _teach(text: str) -> None:
    """Prevent currency from being parsed as an inline Markdown equation."""
    st.markdown(text.replace("$", r"\$"))


def _one() -> None:
    _teach("### Follow the contract from start to finish")
    _teach(
        "Buying a call gives you a **choice**, not automatic stock ownership. "
        "The seller receives your premium and accepts the contract obligation. "
        "If the option is exercised, the buyer must also pay the strike price "
        "for the shares; the premium does not pay for those shares."
    )
    lesson_timeline((
        ("Today", "You pay an option premium."),
        ("Before expiration", "The premium may rise or fall; you may sell the contract."),
        ("At exercise / expiration", "Exercise or settlement depends on the contract and its value."),
    ))
    concept_pair(
        ("gem", "Premium paid",
         "At $3.50 per share, a typical 100-share call costs $350. "
         "That is what you pay for the contractual right.",
         "Upfront option cost"),
        ("calculator", "Exercise cost",
         "Exercising a $100-strike call for 100 shares also involves paying "
         "$10,000 to buy those shares (before fees).",
         "Separate from the premium"),
    )
    insight(
        "Why beginners confuse the two.",
        "A $350 option is not the same as buying $350 of stock. "
        "You hold a contract tied to 100 shares, with an expiration date. "
        "Your payoff and risk behave differently from stock ownership.",
    )
    with st.expander("Go deeper: American vs. European exercise"):
        _teach(
            "**American-style** options generally permit exercise before expiration. "
            "**European-style** options permit exercise only at expiration. "
            "Many US single-stock options are American-style; exercise and "
            "cash-versus-share settlement vary by contract. This lesson uses "
            "a simplified European-style theoretical pricing model."
        )
        _teach(
            "An option can often be sold in the market before expiration. "
            "Whether to exercise or sell is a separate decision influenced "
            "by remaining time value, liquidity, costs, and contract rules."
        )


def _two() -> None:
    _teach("### What if the option is out of the money?")
    _teach(
        "Suppose the stock is **$100**, and a call has a **$110 strike**. "
        "You would not exercise a right to buy at $110 when shares trade at $100. "
        "So its current intrinsic value is **$0**. If that call trades for an "
        "illustrative **$2 premium**, all **$2** is time value."
    )
    premium_bar(2.0, 0.0)
    _teach(
        "The $2 premium is not a guaranteed amount you recover. If the call "
        "expires out of the money, it generally expires worthless and its buyer "
        "loses the original premium, plus any costs."
    )
    _teach("### Calls and puts: the same idea, opposite directions")
    concept_pair(
        ("chart-line", "Call intrinsic value",
         "The larger of zero or (stock price − strike). "
         "Example: stock $112 and strike $100 gives $12 intrinsic value.",
         "Valuable above the strike"),
        ("shield", "Put intrinsic value",
         "The larger of zero or (strike − stock price). "
         "Example: stock $88 and strike $100 gives $12 intrinsic value.",
         "Valuable below the strike"),
    )
    insight(
        "Intrinsic is not profit.",
        "If you paid $14 for a call with $12 intrinsic value at expiration, "
        "the result would still be a $2 loss per share before fees.",
    )
    with st.expander("Go deeper: what does time value really represent?"):
        _teach(
            "Time value is the **premium above intrinsic value**, not a fixed "
            "charge for each day. It changes with time to expiration, "
            "implied volatility, interest rates, dividends and the contract. "
            "The lesson's simplified zero-rate, zero-dividend model has "
            "nonnegative time value; some real European pricing cases "
            "are more nuanced."
        )


def _three() -> None:
    _teach("### Compare calls and puts on the same stock")
    _teach(
        "Imagine two options with the same $100 strike and 30 days left. "
        "If **only the stock price rises**, the call generally gains "
        "theoretical value and the put generally loses value. "
        "But if time or volatility also changes, the real market outcome "
        "can be different."
    )
    concept_pair(
        ("chart-line", "Call holder",
         "Benefits from rising stock prices, all else equal, but still "
         "needs to recover the original premium to earn a net profit.",
         "Positive directional exposure"),
        ("shield", "Put holder",
         "Generally benefits from falling stock prices, but can "
         "lose the entire premium paid.",
         "Negative directional exposure"),
    )
    _teach("### The quote is not the theoretical value")
    _teach(
        "A tradable option quote typically includes a **bid** (what buyers "
        "offer) and an **ask** (what sellers demand). A theoretical model "
        "may output a number in between, but actual transactions depend "
        "on liquidity, spread and fees."
    )
    concept_pair(
        ("calculator", "Theoretical value",
         "A calculation under specific assumptions that helps "
         "explain how premiums respond to changes.",
         "Not necessarily executable"),
        ("target", "Bid–ask spread",
         "The difference between the bid and ask. "
         "A wider spread can increase the cost of trading.",
         "Real-world market friction"),
    )
    with st.expander("Advanced: volatility smile, skew and term structure"):
        _teach(
            "Implied volatility is not the same for every strike or expiration. "
            "A **volatility smile or skew** compares different strikes, "
            "while **term structure** compares expirations. "
            "This is one reason a single volatility slider is a learning "
            "tool rather than an actual option-chain representation."
        )


def _four() -> None:
    _teach("### How to read the value you just calculated")
    _teach(
        "A modeled premium of $4.00 means **$4 per underlying share** "
        "in this example. For a typical 100-share contract, that corresponds "
        "to $400 of premium before costs. The bar above separates intrinsic "
        "value from remaining time value; it is not a trade recommendation."
    )
    concept_pair(
        ("target", "Change one input",
         "Keep everything fixed except the factor you want to study. "
         "That isolates the effect instead of mixing several causes.",
         "Controlled learning"),
        ("waves", "Then combine them",
         "Real prices reflect stock movement, time, uncertainty and "
         "other effects simultaneously.",
         "More realistic reasoning"),
    )
    insight(
        "This model cannot predict a quote.",
        "It doesn't know the market's current bid/ask, changing assumptions, "
        "or American early-exercise features. It uses zero rates and "
        "dividends to make the mathematical relationships clear.",
    )
    with st.expander("Go deeper: why use this simplified model?"):
        _teach(
            "The Black–Scholes European-style model makes assumptions "
            "about volatility, dividends, interest and exercise. "
            "Real US equity options can behave differently, "
            "including around dividends. The controlled model is useful "
            "for studying direction and sensitivity, not for promising "
            "a realistic transaction price."
        )


def _five() -> None:
    _teach("### Compare time value at three expirations")
    v90 = theoretical_option(100, 100, 90, 30, "call").premium
    v30 = theoretical_option(100, 100, 30, 30, "call").premium
    v1 = theoretical_option(100, 100, 1, 30, "call").premium
    a, b, c = st.columns(3)
    a.metric("90 days left", f"USD {v90:.2f}")
    b.metric("30 days left", f"USD {v30:.2f}")
    c.metric("1 day left", f"USD {v1:.2f}")
    _teach(
        "These are three points on the same theoretical curve: stock $100, "
        "strike $100, annualized volatility 30% and no rates or dividends. "
        "The option has no intrinsic value in any of these scenarios. "
        "Less time generally means less room for a favorable move."
    )
    insight(
        "Theta isn't a fixed daily fee.",
        "Time decay is generally nonlinear and depends on strike and "
        "time remaining. Near expiration, an at-the-money option often "
        "loses time value rapidly while other moneyness levels behave differently.",
    )
    with st.expander("Go deeper: why is expiration especially important?"):
        _teach(
            "A sharp stock move can create intrinsic value even with one day "
            "remaining, whereas a small favorable move may not recover "
            "the premium. Some contracts may be automatically exercised "
            "in the money, subject to exchange and brokerage rules. "
            "Know how your contract settles or exercises."
        )


def _six() -> None:
    _teach("### Historical volatility and implied volatility are different")
    concept_pair(
        ("activity", "Historical volatility",
         "A statistic computed from observed changes in past prices.",
         "Looks backward"),
        ("waves", "Implied volatility",
         "A volatility assumption inferred from option premiums under "
         "a pricing model. It relates to market pricing of uncertainty.",
         "Inferred from current options"),
    )
    _teach(
        "Before a major event, the option market may price a wide range "
        "of outcomes. When the uncertainty resolves, implied volatility "
        "can fall, reducing time value. This is commonly called "
        "**IV crush**."
    )
    insight(
        "Direction is only part of the trade.",
        "Someone can buy an expensive call, watch the stock go up, "
        "and lose money if implied volatility drops enough. "
        "The price paid and timing matter.",
    )
    with st.expander("Advanced: does IV crush always follow earnings?"):
        _teach(
            "No. Implied volatility can rise, stay elevated or decline "
            "by more or less than expected. The market may have already "
            "priced an anticipated event outcome. This fictional example "
            "shows a **possibility**, never a guarantee."
        )


def _seven() -> None:
    _teach("### Learn to read a Greek estimate")
    _teach(
        "Suppose a fictional call has **delta +0.50**. A small $1 rise "
        "in the stock would imply roughly **$0.50 more option value** "
        "per share from delta alone, with other pricing inputs held fixed. "
        "For a large move, gamma and other effects mean that estimate "
        "need not remain accurate."
    )
    concept_pair(
        ("chart-line", "First-order sensitivity",
         "Delta tracks stock price, theta tracks time, "
         "and vega tracks assumed volatility under a model.",
         "Isolate one variable"),
        ("activity", "Sensitivity can change",
         "Gamma tells you how delta itself responds as the stock price "
         "moves, rather than remaining constant.",
         "Nonlinear behavior"),
    )
    insight(
        "Greeks are not promises.",
        "They describe a theoretical model at one set of inputs. "
        "Actual trading includes spread, liquidity and changing market "
        "conditions; position size also determines exposure.",
    )
    with st.expander("Advanced: does delta equal the chance of expiring in the money?"):
        _teach(
            "No. Traders sometimes treat delta as a rough probability-like "
            "heuristic under specific model assumptions, but delta is "
            "a **price sensitivity**, not an exact objective probability. "
            "Do not confuse the two."
        )


def _eight() -> None:
    _teach("### Translate the payoff to one full contract")
    _teach(
        "One standard 100-share call costs **$600** at a $6 premium per "
        "share. If the stock finishes at $115 and the strike is $100, "
        "the call's expiration payoff is $15 per share—**$1,500** "
        "for a typical 100-share contract. Minus the initial $600 "
        "premium, that is **$900 of pre-fee profit**."
    )
    concept_pair(
        ("calculator", "At expiration",
         "Payoff depends on stock versus strike; profit subtracts "
         "the premium paid and, in a real trade, costs.",
         "Terminal exercise value"),
        ("hourglass", "Before expiration",
         "Selling an option before it expires can recover a changing "
         "market premium that still includes time value.",
         "Price changes before expiry"),
    )
    _teach("### A real trade has an entry, a holding period and an exit")
    lesson_timeline((
        ("Entry", "Premium paid plus applicable costs."),
        ("Holding", "Stock, time, volatility and risk evolve."),
        ("Exit", "Sell, exercise or settle under the contract rules."),
    ))
    insight(
        "Buying versus writing options have different risks.",
        "A buyer of a plain long call or put generally risks the entire "
        "premium plus costs. Sellers of uncovered options can have "
        "substantially larger risk—potentially unlimited for an "
        "uncovered short call.",
    )
    with st.expander("Advanced: contract settlement, assignment and liquidity"):
        _teach(
            "Contract terms determine whether exercise creates a stock "
            "position, cash settlement or other obligations. A wide "
            "bid–ask spread can make exiting expensive. Automatic "
            "exercise and assignment can also matter near expiration. "
            "Options carry substantial risks and are not appropriate "
            "for every investor."
        )


_DEPTH = (_one, _two, _three, _four, _five, _six, _seven, _eight)


def render_chapter_depth(chapter_number: int) -> None:
    """Additional explanations follow the original chapter, before practice."""
    if type(chapter_number) is not int or not 1 <= chapter_number <= 8:
        raise ValueError("Invalid course chapter")
    _DEPTH[chapter_number - 1]()
