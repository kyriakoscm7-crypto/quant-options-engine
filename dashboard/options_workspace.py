"""Interactive Options Research Workspace."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.pricing.greeks_workspace import calculate_greeks
from app.pricing.options_workspace import (
    CONTRACT_SIZE,
    breakeven,
    expiration_profit,
    scenario_mark_profit,
    theoretical_price,
)
from dashboard.model_handoff import transfer_assumptions

PINK = "#FF78B7"
BLUE = "#79B8FF"


def render_options_workspace():
    st.title("Options Research Workspace")
    st.caption(
        "Explore a hypothetical long call or long put. "
        "Pricing is based on Black-Scholes, not a live option-chain quote."
    )

    st.caption("European exercise model · Constant rates and volatility · No fees, taxes or early assignment. Use hypothetical inputs only.")

    reference = st.session_state.get("qi_model_reference")
    if reference:
        st.caption(f"Research context: {reference}. No prices, ratings or calibration were transferred. Use independently authorized or hypothetical inputs.")

    st.markdown("### 01 / Construct a position")
    a, b, c = st.columns([1, 1, 1])
    with a:
        kind = st.radio(
            "Position", ["Call", "Put"], horizontal=True,
            key="qi_workspace_kind"
        )
    with b:
        contracts = st.number_input(
            "Contracts", min_value=1, max_value=100,
            value=1, step=1, key="qi_workspace_contracts"
        )
    with c:
        days = st.selectbox(
            "Days to expiration", [7, 14, 30, 60, 90, 180, 365],
            index=2, key="qi_workspace_days"
        )

    a, b, c = st.columns(3)
    with a:
        spot = st.number_input(
            "Underlying price ($)", min_value=0.01,
            max_value=1_000_000.0, value=100.0, step=1.0, key="qi_workspace_spot"
        )
    with b:
        strike = st.number_input(
            "Strike price ($)", min_value=0.01,
            max_value=1_000_000.0, value=100.0, step=1.0, key="qi_workspace_strike"
        )
    with c:
        volatility = st.slider(
            "Annualized volatility (%)", min_value=5,
            max_value=150, value=25, step=5,
            key="qi_workspace_vol"
        )

    with st.expander("Advanced model assumptions"):
        rate = st.number_input(
            "Risk-free rate (%)", min_value=-20.0, max_value=100.0, value=4.0, step=0.25,
            key="qi_workspace_rate"
        )
        dividend = st.number_input(
            "Dividend yield (%)", min_value=0.0,
            max_value=100.0, value=0.0, step=0.25,
            key="qi_workspace_dividend"
        )

    premium = theoretical_price(
        kind, spot, strike, days, volatility, rate, dividend
    )
    break_even = breakeven(kind, strike, premium)
    cost = premium * CONTRACT_SIZE * contracts

    st.markdown("### 02 / Understand the position")
    a, b, c = st.columns(3)
    a.metric("Theoretical premium / share", f"${premium:,.2f}")
    b.metric("Illustrative entry cost", f"${cost:,.2f}")
    c.metric(
        "Expiration breakeven",
        f"${break_even:,.2f}" if break_even >= 0 else "Not attainable",
    )
    st.caption(
        f"Assumes {contracts} standard contract(s) covering "
        f"{CONTRACT_SIZE * contracts:,} shares total. "
        "Entry cost is based on the theoretical premium, not an executable "
        "bid or ask. The maximum loss for this long position is the "
        "premium paid, excluding fees."
    )

    sensitivity = calculate_greeks(kind, spot, strike, days, volatility, rate, dividend)
    st.write(
        f"Near these assumptions, a $1 underlying increase changes the model value by about "
        f"${sensitivity['delta'] * CONTRACT_SIZE * contracts:+,.2f} for the position; "
        f"one calendar day changes it by about ${sensitivity['theta'] * CONTRACT_SIZE * contracts:+,.2f}, "
        "holding other inputs fixed. Sensitivities change as assumptions move."
    )
    st.button("Investigate these assumptions in Greeks", key="qi_options_to_greeks",
              on_click=transfer_assumptions,
              args=("workspace", "greeks", "📊 Greeks Analysis"))

    st.markdown("### 03 / Profit or loss at expiration")
    lower = max(0.0, min(spot, strike, max(0.0, break_even)) * 0.5)
    upper = max(spot, strike, max(0.0, break_even)) * 1.6
    prices = [
        lower + i * (upper - lower) / 100 for i in range(101)
    ]
    pnl = [
        expiration_profit(kind, strike, premium, x, int(contracts))
        for x in prices
    ]
    chart = go.Figure()
    chart.add_trace(go.Scatter(
        x=prices, y=pnl, mode="lines",
        name="Expiration P/L",
        line=dict(color=PINK, width=3),
        fill="tozeroy",
        fillcolor="rgba(255,120,183,0.09)",
    ))
    chart.add_hline(y=0, line_dash="dash", line_color="#8B99B2")
    chart.add_vline(
        x=spot, line_dash="dot", line_color=BLUE,
        annotation_text="Current underlying"
    )
    if break_even >= 0:
        chart.add_vline(
            x=break_even, line_dash="dash", line_color=PINK,
            annotation_text="Breakeven",
        )
    chart.update_layout(
        template="plotly_dark",
        paper_bgcolor="#080D1D",
        plot_bgcolor="#111B30",
        margin=dict(l=16, r=16, t=28, b=18),
        xaxis_title="Underlying price at expiration ($)",
        yaxis_title="Position profit / loss ($)",
        height=400,
        showlegend=False,
    )
    st.plotly_chart(chart, use_container_width=True)
    st.write(
        "This chart shows **intrinsic value at expiration minus "
        "the illustrative premium paid**. It does not represent "
        "the option's price before expiration."
    )

    st.markdown("### 04 / Explore a market scenario")
    st.write(
        "Move the underlying price, volatility, or time remaining "
        "to see a new theoretical mark for the same contract."
    )
    a, b, c = st.columns(3)
    with a:
        spot_change = st.slider(
            "Underlying move (%)", -40, 40, 5, 1,
            key="qi_workspace_move"
        )
    with b:
        vol_change = st.slider(
            "Volatility change (points)", -20, 40, 0, 1,
            key="qi_workspace_volmove"
        )
    with c:
        elapsed = st.slider(
            "Days elapsed", 0, max(0, days - 1),
            min(7, days - 1), 1,
            key="qi_workspace_elapsed"
        )

    scenario_spot = spot * (1 + spot_change / 100)
    scenario_vol = max(1.0, volatility + vol_change)
    remaining = days - elapsed
    scenario_price = theoretical_price(
        kind, scenario_spot, strike, remaining,
        scenario_vol, rate, dividend
    )
    scenario_pnl = scenario_mark_profit(
        kind, scenario_spot, strike, remaining, scenario_vol,
        premium, int(contracts), rate, dividend
    )
    a, b, c = st.columns(3)
    a.metric("Scenario underlying", f"${scenario_spot:,.2f}")
    b.metric(
        "Scenario option mark", f"${scenario_price:,.2f}",
        f"{scenario_price - premium:+.2f} / share"
    )
    c.metric("Hypothetical position P/L", f"${scenario_pnl:+,.2f}")

    st.dataframe(
        pd.DataFrame([
            {
                "State": "Initial",
                "Underlying": spot,
                "Volatility %": volatility,
                "Days remaining": days,
                "Model premium / share": premium,
            },
            {
                "State": "Scenario",
                "Underlying": scenario_spot,
                "Volatility %": scenario_vol,
                "Days remaining": remaining,
                "Model premium / share": scenario_price,
            },
        ]),
        hide_index=True,
        use_container_width=True,
    )
    st.info(
        "Scenario P/L is the difference between two theoretical "
        "values at different assumed market states, multiplied "
        "by position size. It is not an actual realized return "
        "or a guarantee of a tradable exit price."
    )

    with st.expander("What the model does and does not tell you"):
        st.write(
            "**Call:** the right to buy at the strike. "
            "**Put:** the right to sell at the strike. "
            "Both illustrations assume purchasing the option."
        )
        st.write(
            "Black-Scholes uses the underlying price, strike, time, "
            "annualized volatility, interest rate and dividend yield. "
            "It does not incorporate live option bid/ask spreads, "
            "transaction fees, volatility smiles or execution slippage."
        )
        st.write(
            "The framework assumes European-style exercise and "
            "continuous idealized markets. Real listed contracts "
            "can have different exercise and settlement rules. "
            "Confirm actual contract specifications before trading."
        )

    st.caption(
        "Educational, hypothetical scenarios only. "
        "Not personalized investment advice."
    )
