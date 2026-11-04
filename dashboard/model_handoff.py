"""Explicit transfer of user-entered assumptions only, never provider values."""

import streamlit as st

FIELDS = ("kind", "contracts", "days", "spot", "strike", "vol", "rate", "dividend")


def transfer_assumptions(source: str, target: str, route: str) -> None:
    for field in FIELDS:
        source_field = "volatility" if source == "greeks" and field == "vol" else field
        target_field = "volatility" if target == "greeks" and field == "vol" else field
        key = f"qi_{source}_{source_field}"
        if key in st.session_state:
            st.session_state[f"qi_{target}_{target_field}"] = st.session_state[key]
    st.session_state["_navigation_request"] = route
