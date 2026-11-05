"""Interactive Greeks Risk Intelligence dashboard."""

import plotly.graph_objects as go
import streamlit as st

from app.pricing.greeks_workspace import calculate_greeks, compare_repricing
from dashboard.model_handoff import hydrate_model, remember_model, transfer_assumptions


def render_greeks_workspace():
    hydrate_model("greeks")
    st.title("Greeks Risk Intelligence")
    st.caption(
        "Investigate how an option responds to changing market assumptions. "
        "All results are theoretical, not live option quotes."
    )

    st.caption("European exercise model · Constant rates and volatility · No fees, taxes or early assignment. Use hypothetical inputs only.")

    st.markdown("### 01 / Define your position")
    a, b, c = st.columns(3)
    with a:
        kind = st.radio(
            "Option type", ["Call", "Put"], horizontal=True,
            key="qi_greeks_kind", on_change=remember_model, args=("greeks",)
        )
    with b:
        days = st.selectbox(
            "Days to expiration", [7, 14, 30, 60, 90, 180, 365],
            index=2, key="qi_greeks_days", on_change=remember_model, args=("greeks",)
        )
    with c:
        contracts = st.number_input(
            "Contracts", min_value=1, max_value=100,
            value=1, step=1, key="qi_greeks_contracts", on_change=remember_model, args=("greeks",)
        )

    a, b, c = st.columns(3)
    with a:
        spot = st.number_input(
            "Underlying price ($)", min_value=0.01,
            max_value=1_000_000.0, value=100.0, step=1.0, key="qi_greeks_spot", on_change=remember_model, args=("greeks",)
        )
    with b:
        strike = st.number_input(
            "Strike price ($)", min_value=0.01,
            max_value=1_000_000.0, value=100.0, step=1.0, key="qi_greeks_strike", on_change=remember_model, args=("greeks",)
        )
    with c:
        volatility = st.slider(
            "Annualized volatility (%)", 5, 150, 25, 5,
            key="qi_greeks_volatility", on_change=remember_model, args=("greeks",)
        )

    with st.expander("Advanced assumptions"):
        rate = st.number_input(
            "Risk-free interest rate (%)", min_value=-20.0, max_value=100.0, value=4.0,
            step=0.25, key="qi_greeks_rate", on_change=remember_model, args=("greeks",)
        )
        dividend = st.number_input(
            "Dividend yield (%)", min_value=0.0, max_value=100.0,
            value=0.0, step=0.25, key="qi_greeks_dividend", on_change=remember_model, args=("greeks",)
        )

    greek = calculate_greeks(
        kind, spot, strike, days, volatility, rate, dividend
    )

    st.button("Use these assumptions in Options Lab", key="qi_greeks_to_options",
              on_click=transfer_assumptions,
              args=("greeks", "workspace", "💰 Options Lab"))
    st.caption("Only your manual assumptions transfer. Provider prices and ratings are never model inputs.")

    st.markdown("### 02 / Understand your risk")
    st.metric("Theoretical option price / share", f"${greek['price']:.4f}")

    a, b, c, d = st.columns(4)
    a.metric("Delta · per $1", f"{greek['delta']:+.4f}")
    b.metric("Gamma · per $1", f"{greek['gamma']:.4f}")
    c.metric("Vega · per vol point", f"${greek['vega']:+.4f}")
    d.metric("Theta · per day", f"${greek['theta']:+.4f}")

    st.caption(
        "These are per-share theoretical sensitivities. Standard equity "
        "options generally represent 100 shares per contract. Vega is per "
        "one percentage-point volatility change; Theta is per calendar day."
    )

    st.markdown("### 03 / Test a price movement")
    max_down = min(40.0, spot * 0.8)
    move = st.slider(
        "Underlying price change ($)",
        -max_down, 40.0, 5.0, 0.01,
        key="qi_greeks_move"
    )

    result = compare_repricing(
        kind, spot, strike, days, volatility,
        float(move), rate, dividend
    )

    moves = [-max_down + i * (40.0 + max_down) / 80 for i in range(81)]
    outcomes = [
        compare_repricing(
            kind, spot, strike, days, volatility,
            float(m), rate, dividend
        )
        for m in moves
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[x["new_spot"] for x in outcomes],
        y=[x["full_price"] for x in outcomes],
        name="Full Black-Scholes",
        mode="lines",
        line=dict(color="#FF78B7", width=3),
    ))
    fig.add_trace(go.Scatter(
        x=[x["new_spot"] for x in outcomes],
        y=[x["approx_price"] for x in outcomes],
        name="Delta-Gamma approximation",
        mode="lines",
        line=dict(color="#79B8FF", width=2, dash="dash"),
    ))
    fig.add_vline(x=spot, line_color="#8B99B2", line_dash="dot")
    fig.add_vline(
        x=result["new_spot"], line_color="#FF78B7", line_dash="dot"
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#080D1D",
        plot_bgcolor="#111B30",
        height=410,
        margin=dict(l=18, r=18, t=50, b=20),
        legend=dict(orientation="h", y=1.15),
        xaxis_title="Underlying price ($)",
        yaxis_title="Theoretical option value / share ($)",
    )
    st.plotly_chart(fig, use_container_width=True)

    a, b, c = st.columns(3)
    a.metric("Full repricing / share", f"${result['full_price']:.4f}")
    b.metric("Greek approximation / share", f"${result['approx_price']:.4f}")
    c.metric(
        "Approximation error / position",
        f"${result['approx_error'] * 100 * contracts:+,.2f}"
    )

    st.info(
        "Delta and Gamma approximate how an option responds near the "
        "starting underlying price. For larger moves, recalculating "
        "the full pricing model generally provides a better estimate "
        "under the same assumptions. The approximation may even "
        "produce an impossible negative option value far away."
    )

    st.markdown("### 04 / Interpret the results")
    st.write(
        f"**Delta ({greek['delta']:+.4f}):** Approximates the change "
        "in option value per share for a small $1 underlying move."
    )
    st.write(
        f"**Gamma ({greek['gamma']:.4f}):** Measures how Delta changes "
        "as the underlying moves. It captures local curvature."
    )
    st.write(
        f"**Vega (${greek['vega']:.4f}):** Approximates the change in "
        "option value for a one-percentage-point rise in volatility."
    )
    st.write(
        f"**Theta (${greek['theta']:+.4f}):** Approximates the change "
        "from one calendar day passing, holding other inputs constant."
    )

    with st.expander("Rho and model limitations"):
        st.write(
            f"**Rho (${greek['rho']:+.4f}):** Sensitivity to a "
            "one-percentage-point increase in the risk-free interest rate."
        )
        st.write(
            "The chart changes only the underlying price. Volatility, "
            "time, rates, and dividends are held constant. Actual "
            "option markets may behave differently due to volatility "
            "smiles, bid-ask spreads, liquidity and exercise rules."
        )
        st.write(
            "The engine returns rounded Greek values, so minor "
            "approximation differences also include rounding."
        )

    st.caption(
        "Educational Black-Scholes European-option analysis only. "
        "Not personalized investment advice."
    )
