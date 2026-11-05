"""Session model, independent of provider displays and Streamlit widget cleanup."""

import streamlit as st

FIELDS = ("kind", "contracts", "days", "spot", "strike", "vol", "rate", "dividend")
DEFAULTS = dict(
    kind="Call",
    contracts=1,
    days=30,
    spot=100.0,
    strike=100.0,
    vol=25,
    rate=4.0,
    dividend=0.0,
)


def widget_key(page, field):
    return f"qi_{page}_{'volatility' if page == 'greeks' and field == 'vol' else field}"


def remember_model(page):
    model = st.session_state.setdefault("qi_model", DEFAULTS.copy())
    for field in FIELDS:
        key = widget_key(page, field)
        if key in st.session_state:
            model[field] = st.session_state[key]


def hydrate_model(page):
    model = st.session_state.setdefault("qi_model", DEFAULTS.copy())
    for field in FIELDS:
        st.session_state[widget_key(page, field)] = model[field]


def transfer_assumptions(source, target, route):
    remember_model(source)
    hydrate_model(target)
    st.session_state["_navigation_request"] = route
