"""Weekly provider calendar and existing SEC research entry point."""
import os
from datetime import datetime, timedelta
from itertools import groupby
from zoneinfo import ZoneInfo

import streamlit as st

from app.intelligence.earnings_calendar import CalendarConfig, calendar_service


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
    st.caption("America/Toronto week · US calendar · Dates and market sessions are supplied by Finnhub; exact times and event timezone are not supplied.")
    try:
        settings = st.secrets.get("earnings", {})
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        settings = {}
    config = CalendarConfig(
        os.environ.get("FINNHUB_API_KEY") or settings.get("api_key", ""),
        os.environ.get("QI_EARNINGS_USE") or settings.get("use", ""),
    )
    result = calendar_service.load(config, start, end)
    if result.error:
        st.info("Earnings dates are unavailable. " + result.error)
        st.caption("This does not mean no companies are reporting.")
    else:
        st.caption(f"Source: Finnhub · Retrieved {result.retrieved_at.astimezone(ZoneInfo('America/Toronto')):%Y-%m-%d %H:%M %Z} · Cache up to 15 minutes · Source update time unavailable")
        st.link_button("Calendar source & methodology", "https://finnhub.io/docs/api/earnings-calendar")
        st.info("Scheduled dates are unconfirmed: Finnhub does not identify company-confirmed versus estimated dates. Check the company's investor relations announcement before relying on a date.")
        if result.rejected:
            st.warning(f"{result.rejected} invalid or conflicting records withheld. Coverage may be incomplete.")
        if not result.events:
            st.info("Finnhub returned no events for this week. Coverage or plan limits may apply; this is not proof that no companies report.")
        for day, events in groupby(result.events, key=lambda e: e.day):
            st.subheader(f"{day:%A, %b %d}")
            for event in events:
                with st.container(border=True):
                    st.markdown(f"**{event.symbol}**")
                    st.write(event.session)
                    st.caption(event.status)
                    st.caption("Provider ticker · Company identity checked when research opens")
                    if st.button(f"Open {event.symbol} research →", key=f"earnings_{event.day}_{event.symbol}", width="stretch"):
                        open_research(event.symbol)
    if st.button("Find stocks instead", type="primary"):
        st.session_state["_navigation_request"] = "💎 Quant Discovery"
        st.rerun()
    with st.expander("Calendar setup & coverage"):
        st.write("Finnhub US earnings calendar. Personal plan is for your own local research only; sharing or business use requires written provider approval. Configuration and Mac instructions: docs/EARNINGS_CALENDAR.md.")
        st.caption("No earnings data is written to your notebook or disk. No investment score is derived from calendar events. Restart the app to clear cached calendar data when ending provider access.")


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
