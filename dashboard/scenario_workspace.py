"""Joint price/volatility/time scenarios using the canonical pricing engine."""

import pandas as pd
import streamlit as st

from app.pricing.options_workspace import theoretical_price
from dashboard.model_handoff import hydrate_model, remember_model, transfer_assumptions


def scenario_rows(model, moves, vol_shock, elapsed, side):
    volatility = model["vol"] + vol_shock
    if volatility < 0 or not 0 <= elapsed <= model["days"]:
        raise ValueError(
            "Volatility must remain nonnegative and elapsed days cannot exceed expiry."
        )
    initial = theoretical_price(
        model["kind"],
        model["spot"],
        model["strike"],
        model["days"],
        model["vol"],
        model["rate"],
        model["dividend"],
    )
    rows = []
    for move in moves:
        spot = model["spot"] * (1 + move / 100)
        mark = theoretical_price(
            model["kind"],
            spot,
            model["strike"],
            model["days"] - elapsed,
            volatility,
            model["rate"],
            model["dividend"],
        )
        rows.append(
            {
                "Spot shock %": move,
                "Spot": spot,
                "Volatility %": volatility,
                "Days remaining": model["days"] - elapsed,
                "Theoretical mark": mark,
                "Position P/L": side * model["contracts"] * 100 * (mark - initial),
            }
        )
    return rows


def render_scenario_workspace():
    st.title("Scenario Explorer")
    st.caption(
        "Shared manual model · joint spot, volatility and time shocks · theoretical P/L, not an execution price or forecast."
    )
    hydrate_model("scenario")
    for field, label in [
        ("spot", "Underlying price ($)"),
        ("strike", "Strike price ($)"),
        ("rate", "Risk-free rate (%)"),
        ("dividend", "Dividend yield (%)"),
    ]:
        st.number_input(
            label,
            min_value=-20.0
            if field == "rate"
            else (0.0 if field == "dividend" else 0.01),
            max_value=100.0 if field in ("rate", "dividend") else 1_000_000.0,
            key=f"qi_scenario_{field}",
            on_change=remember_model,
            args=("scenario",),
        )
    st.radio(
        "Option type",
        ["Call", "Put"],
        key="qi_scenario_kind",
        on_change=remember_model,
        args=("scenario",),
        horizontal=True,
    )
    st.selectbox(
        "Days to expiration",
        [7, 14, 30, 60, 90, 180, 365],
        key="qi_scenario_days",
        on_change=remember_model,
        args=("scenario",),
    )
    st.slider(
        "Annualized volatility (%)",
        5,
        150,
        key="qi_scenario_vol",
        on_change=remember_model,
        args=("scenario",),
    )
    st.number_input(
        "Contracts",
        1,
        100,
        key="qi_scenario_contracts",
        on_change=remember_model,
        args=("scenario",),
    )
    side = (
        1
        if st.radio("Position direction", ["Long", "Short"], horizontal=True) == "Long"
        else -1
    )
    shock = st.slider("Volatility shock (percentage points)", -150, 150, 0)
    elapsed = st.slider(
        "Calendar days elapsed", 0, int(st.session_state["qi_model"]["days"]), 0
    )
    try:
        rows = scenario_rows(
            st.session_state["qi_model"],
            [-20, -10, -5, 0, 5, 10, 20],
            shock,
            elapsed,
            side,
        )
    except ValueError as exc:
        st.error(str(exc))
    else:
        frame = pd.DataFrame(rows)
        st.line_chart(frame, x="Spot shock %", y="Position P/L", color="#FF78B7")
        st.dataframe(frame, hide_index=True, use_container_width=True)
    st.caption(
        "100-share multiplier; no fees, taxes, slippage, financing or early exercise. Short-option losses can exceed initial premium. All assumptions are fictional; no provider data enters this engine."
    )
    st.button(
        "Continue in Options Lab",
        on_click=transfer_assumptions,
        args=("scenario", "workspace", "💰 Options Lab"),
    )
