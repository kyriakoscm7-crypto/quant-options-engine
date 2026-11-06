"""Weekly provider calendar and existing SEC research entry point."""
import os
from datetime import timedelta

import streamlit as st


def week_bounds(day, offset=0):
    start = day - timedelta(days=day.weekday()) + timedelta(weeks=offset)
    return start, start + timedelta(days=6)


def render_earnings_week():
    st.title("Reading earnings")
    st.write("Learn what a company report can tell you, and what it cannot.")
    st.info("No live earnings calendar is offered in this public build. No scheduled dates or provider events are substituted.")
    st.subheader("A practical report checklist")
    st.markdown("""
1. **Check the period and source.** Start with the issuer's investor-relations announcement and its SEC filing. A filing date is not a scheduled earnings date.
2. **Compare like with like.** Compare revenue, operating income and cash flow for the same periods and currency. Annual figures can hide seasonal changes.
3. **Look beyond headline EPS.** Share issuance, buybacks and one-time items can change earnings per share without the same change in the underlying business.
4. **Separate results from expectations.** Reported results describe the past. Guidance is uncertain; a good report does not guarantee a rising share price.
5. **Record the counterargument.** Note missing evidence, debt, dilution and risks before forming a research thesis.
""")
    st.caption("Find stocks provides annual SEC accounting evidence, not prices, analyst expectations, event timing or investment recommendations.")
    if st.button("Find stocks", type="primary"):
        st.session_state["_navigation_request"] = "💎 Quant Discovery"
        st.rerun()
    if st.button("Explore earnings lessons"):
        st.session_state["_navigation_request"] = "📚 Learn"
        st.rerun()
    st.link_button("Search original SEC filings", "https://www.sec.gov/edgar/search/")


def open_research(symbol):
    from app.intelligence.discover_service import company_deep_dive
    from dashboard.discover_intelligence import _gateway

    agent = os.environ.get("QI_SEC_USER_AGENT", "")
    if not agent:
        st.warning("Set QI_SEC_USER_AGENT with your genuine operator contact to open SEC company research.")
        return
    try:
        with st.spinner(f"Checking SEC identity and evidence for {symbol}…"):
            report = company_deep_dive(_gateway(agent), symbol)
    except Exception:
        st.warning("SEC identity or evidence could not be verified for this provider ticker. No other company was substituted.")
        return
    reports = st.session_state.get("qi_discover_reports", [])
    st.session_state["qi_discover_reports"] = [r for r in reports if r["company"].ticker != report["company"].ticker] + [report]
    st.session_state["qi_earnings_origin"] = True
    st.session_state["qi_detail"] = report["company"].ticker
    st.session_state["_navigation_request"] = "💎 Quant Discovery"
    st.rerun()
