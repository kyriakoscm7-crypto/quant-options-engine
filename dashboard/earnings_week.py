"""Weekly earnings entry point. No vendor or inferred SEC dates admitted."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st


def week_bounds(day, offset=0):
    start = day - timedelta(days=day.weekday()) + timedelta(weeks=offset)
    return start, start + timedelta(days=6)


def render_earnings_week():
    st.title("Earnings this week")
    st.write("See who is reporting, then understand the business behind the results.")
    today = datetime.now(ZoneInfo("America/Toronto")).date()
    offset = st.session_state.get("qi_earnings_week_offset", 0)
    previous, current, following = st.columns(3)
    if previous.button("← Previous week", width="stretch"):
        st.session_state["qi_earnings_week_offset"] = offset - 1
        st.rerun()
    if current.button("This week", width="stretch"):
        st.session_state["qi_earnings_week_offset"] = 0
        st.rerun()
    if following.button("Next week →", width="stretch"):
        st.session_state["qi_earnings_week_offset"] = offset + 1
        st.rerun()
    start, end = week_bounds(today, offset)
    st.subheader(f"{start:%b %d, %Y} – {end:%b %d, %Y}")
    st.caption("Week shown in America/Toronto. No verified calendar feed connected.")
    st.info("Earnings dates are unavailable. Connect an approved earnings calendar to see verified companies here.")
    st.write("This does not mean no companies are reporting. SEC filing dates cannot tell us when earnings will be announced.")
    if st.button("Find stocks instead", type="primary"):
        st.session_state["_navigation_request"] = "💎 Quant Discovery"
        st.rerun()
    with st.expander("Connect a verified calendar"):
        st.write("No earnings provider is approved or configured. An API key alone does not enable a source.")
        st.write("A provider integration must verify display, derived-use and retention rights, identify the dataset owner, and validate company identity, confirmation status, freshness and event timezone. Estimated, stale or conflicting dates must not appear as confirmed events.")
        st.caption("Integration guide: docs/DISCOVER_SIMPLE.md. Keep provider credentials on the server; never paste them into this page or a notebook.")
