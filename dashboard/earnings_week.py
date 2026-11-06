"""Weekly provider calendar and existing SEC research entry point."""
import os
from datetime import date, datetime, timedelta
from itertools import groupby
from zoneinfo import ZoneInfo

import streamlit as st


def week_bounds(day, offset=0):
    start = day - timedelta(days=day.weekday()) + timedelta(weeks=offset)
    return start, start + timedelta(days=6)


def render_earnings_week():
    st.title("Earnings calendar")
    from app.intelligence.issuer_calendar import REVIEWED, select_events

    st.write("Upcoming company-announced earnings releases and calls.")
    st.caption(f"Curated coverage: seven companies · Manually checked {REVIEWED:%B %d, %Y} · Not a live or market-wide feed")
    today = datetime.now(ZoneInfo("America/Toronto")).date()
    if (today - REVIEWED).days > 7:
        st.warning("This schedule needs a fresh source review. Dates may have changed; check the company announcement.")
    window = st.selectbox("Show dates", ["Next 30 days", "This week", "Next week"])
    query = st.text_input("Find a company or ticker", placeholder="Try TTD, Disney or Target", max_chars=100)
    events = select_events(today, window, query)
    st.caption("Dates use the issuer's announced event date. Times are US Eastern (ET). A call time is not the results-release time.")
    if not events:
        st.info("No matching events in this curated schedule. This does not mean no companies are reporting. Try another date range or the broader calendar below.")
    for day, rows in groupby(events, key=lambda e: e["day"]):
        st.subheader(date.fromisoformat(day).strftime("%A, %B %d, %Y"))
        for event in rows:
            with st.container(border=True):
                st.markdown(f"**{event['company']} · {event['symbol']}**")
                st.write(f"Results release: {event['release']}")
                st.write(f"Earnings call / webcast: {event['call']}")
                st.caption(f"Company-announced event · Checked {REVIEWED.isoformat()} · Schedule subject to change")
                st.link_button("Company announcement ↗", event["source"])
    with st.expander("Sources & coverage"):
        st.write("Independently compiled factual dates and times from each linked company announcement or investor-relations events page. No analyst estimates, article text or vendor calendar data is copied. Call-only announcements do not establish a precise results-release time. This small editorial schedule is manually maintained, not automatically refreshed; entries are withheld after 30 days without review.")
    st.subheader("Broader earnings coverage")
    st.link_button(
        "Open earnings calendar on TradingView ↗",
        "https://www.tradingview.com/earnings-calendar/?countries=us",
        type="primary",
        width="stretch",
    )
    st.caption("Opens TradingView in a new tab. Dates and coverage are supplied by TradingView and can change; verify important dates with the company’s investor-relations announcement.")
    st.write("Then use the checklist below to understand the results.")
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
