"""Earnings week: provider events + original SEC-backed company research."""
import os
from datetime import date, datetime, timedelta
from itertools import groupby
from zoneinfo import ZoneInfo

import streamlit as st


def week_bounds(day, offset=0):
    start = day - timedelta(days=day.weekday()) + timedelta(weeks=offset)
    return start, start + timedelta(days=6)


def _earnings_api_key():
    """Read server-side only; do not show keys in the UI or link URLs."""
    key = os.environ.get("EARNINGSAPI_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("EARNINGSAPI_API_KEY", "")).strip()
    except Exception:  # Streamlit raises a custom error when no secrets file exists
        return ""


def _render_provider_calendar(today, key):
    from app.intelligence.earnings_api_provider import (
        earnings_api_service,
        reporting_week,
    )

    start = reporting_week()
    end = start + timedelta(days=6)
    query = st.text_input("Search earnings companies", placeholder="Company or ticker", max_chars=100).strip().lower()
    with st.spinner("Loading earnings dates…"):
        result = earnings_api_service.load_week(key, start)

    st.caption(f"{start:%b %d} – {end:%b %d, %Y} · EarningsAPI.com · Provider-reported dates")
    if result.error:
        st.warning(result.error)
        st.info("The curated company-announcement schedule is available below.")
        return False
    from html import escape

    from app.intelligence.earnings_ranking import order_events, select_page

    ordered, ordering = order_events(result.events, today)
    st.caption(ordering)
    days = sorted({e.day for e in ordered})
    chosen = st.selectbox("Reporting day", [None, *days],
                          format_func=lambda d: "All days" if d is None else f"{d:%a, %b %d} · {sum(e.day == d for e in ordered)} events")
    signature = (start.isoformat(), query, chosen, result.retrieved_at)
    if st.session_state.get("earnings_view") != signature:
        st.session_state["earnings_view"] = signature
        st.session_state["earnings_limit"] = 10
    rows, count = select_page(ordered, query, chosen, st.session_state.get("earnings_limit", 10))
    st.markdown(f"**{count:,} matching earnings events** · {len(result.events):,} this week · Showing {len(rows):,}")
    if result.rejected:
        st.caption(f"{result.rejected} inconsistent or invalid provider entries omitted.")
    if not rows:
        st.info("No matching provider events for this week. This is not proof that no companies are reporting.")
    st.markdown("""<style>
    .earnings-card {padding:18px 20px 12px;border-top:2px solid #FF78B7;
      border-radius:12px;background:linear-gradient(130deg,#121D35,#0D1424);color:#f3f5fc;min-height:132px}
    .earnings-card h3 {font-size:1.3rem;margin:8px 0 4px;color:#fff}
    .earnings-card p {margin:0;overflow-wrap:anywhere}
    .earnings-meta {font-size:.85rem;color:#c2cade}
    </style>""", unsafe_allow_html=True)
    for index in range(0, len(rows), 2):
        columns = st.columns(2)
        for col, event in zip(columns, rows[index:index + 2]):
            with col, st.container(border=True):
                session = {"Before market": "BMO · Before market", "After market": "AMC · After market"}.get(event.session, "Time not supplied")
                st.markdown(f'<article class="earnings-card"><p class="earnings-meta">{event.day:%a, %b %d, %Y} · {session}</p>'
                            f'<h3>{escape(event.symbol)}</h3><p>{escape(event.name)}</p></article>', unsafe_allow_html=True)
                st.caption("Source: EarningsAPI.com · Provider-reported")
                if st.button(f"Research {event.symbol}", key=f"ea_{event.day.isoformat()}_{event.symbol}", width="stretch"):
                    open_stock_explorer(event.symbol)
    if len(rows) < count and st.button("Show 10 more", width="stretch"):
        st.session_state["earnings_limit"] = len(rows) + 10
        st.rerun()
    with st.expander("Data source and limitations"):
        st.write("Market-cap ranking is unavailable: no comparable, display-authorized feed is connected. The first 10 are calendar events, not the largest companies.")
        if result.retrieved_at:
            timestamp = datetime.fromtimestamp(result.retrieved_at, ZoneInfo("America/New_York"))
            st.caption(f"Retrieved {timestamp:%b %d, %Y at %I:%M %p} ET · Shared cache up to 24 hours")
        st.write("EarningsAPI.com supplies the date and pre-market/after-market/unspecified category. It does not establish company confirmation, guarantee completeness, or supply an exact release time. The calendar is separate from SEC financial scores and is not investment advice. Provider results are displayed, not offered as a downloadable feed.")
        st.link_button("Provider documentation", "https://www.earningsapi.com/docs/calendar-earnings")
    return True


def render_earnings_week():
    st.title("Earnings calendar")
    st.write("See who's reporting earnings, then open their financial research in one click.")
    today = datetime.now(ZoneInfo("America/New_York")).date()
    key = _earnings_api_key()
    if key and _render_provider_calendar(today, key):
        return

    from app.intelligence.issuer_calendar import EVENTS, REVIEWED, select_events
    st.caption(f"Company-announced schedule · {len(EVENTS)} curated entries · Last reviewed {REVIEWED:%B %d, %Y}")
    if not key:
        st.info("The live calendar is not connected yet. Add EARNINGSAPI_API_KEY to Streamlit server secrets to enable weekly earnings coverage. The verified company-announcement list below works without a key.")
    if (today - REVIEWED).days > 7:
        st.warning("This manually reviewed schedule may be out of date. Check each issuer announcement.")
    from app.intelligence.earnings_api_provider import reporting_week
    start = reporting_week()
    st.caption(f"{start:%b %d} – {start + timedelta(days=6):%b %d, %Y} · Automatic reporting week")
    query = st.text_input("Find a company", placeholder="Ticker or company", max_chars=100)
    events = [e for e in select_events(start, "This week", query)
              if start <= date.fromisoformat(e["day"]) <= start + timedelta(days=6)]
    if not events:
        st.info("No matching events in this limited curated list. This does not mean no companies are reporting.")
    for day, rows in groupby(events, key=lambda e: e["day"]):
        with st.expander(date.fromisoformat(day).strftime("%A, %B %d, %Y"), expanded=True):
            for event in rows:
                with st.container(border=True):
                    a, b = st.columns([3, 1], vertical_alignment="center")
                    with a:
                        st.markdown(f"**{event['company']} ({event['symbol']})**")
                        st.caption(f"Results: {event['release']} · Call: {event['call']}")
                        st.link_button("Official announcement", event["source"])
                    with b:
                        if st.button("Research", key=f"issuer_{day}_{event['symbol']}", width="stretch"):
                            open_stock_explorer(event["symbol"])
    st.caption("Issuer-announced dates and conference-call times can change. Call time does not necessarily equal financial-results release time.")
    with st.expander("Sources and other research options"):
        st.write("Curated facts come from original issuer announcements. This is not a complete market-wide calendar. The broader TradingView calendar opens separately; its data is not imported into our engine.")
        st.link_button("View broader TradingView calendar", "https://www.tradingview.com/earnings-calendar/?countries=us")
        st.link_button("Search original SEC filings", "https://www.sec.gov/edgar/search/")
    if st.button("Find stocks"):
        st.session_state["_navigation_request"] = "💎 Quant Discovery"
        st.rerun()


def open_stock_explorer(symbol):
    """Open Stock Explorer's existing verified ticker search flow."""
    import re

    if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z][A-Z0-9.\\-]{0,14}", symbol):
        st.warning("This listing symbol cannot be passed to Research.")
        return
    st.session_state["_research_ticker_request"] = symbol
    st.session_state["_navigation_request"] = "🔎 Stock Explorer"
    st.rerun()


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
