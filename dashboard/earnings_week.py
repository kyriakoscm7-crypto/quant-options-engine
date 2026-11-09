"""Earnings week: provider events + original SEC-backed company research."""
import os
from datetime import date, datetime, timedelta
from itertools import groupby
from zoneinfo import ZoneInfo

import streamlit as st


def week_bounds(day, offset=0):
    start = day - timedelta(days=day.weekday()) + timedelta(weeks=offset)
    return start, start + timedelta(days=6)


def _earnings_setting(name):
    """Read server configuration without exposing values in the UI."""
    key = os.environ.get(name, "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get(name, "")).strip()
    except Exception:  # Streamlit raises a custom error when no secrets file exists
        return ""


def _earnings_api_key():
    return _earnings_setting("EARNINGSAPI_API_KEY")


def _render_provider_calendar(today, key):
    from app.intelligence.earnings_api_provider import (
        earnings_api_service,
        reporting_week,
    )

    start = reporting_week()
    end = start + timedelta(days=6)
    query = st.text_input("Search earnings companies", placeholder="Company or ticker", max_chars=100).strip().lower()
    # A shared PostgreSQL ledger is required for multi-instance cloud hosting.
    # Local SQLite remains available for a single-host durable volume.
    database_url = _earnings_setting("EARNINGSAPI_DATABASE_URL")
    with st.spinner("Loading earnings dates…"):
        if database_url:
            from app.intelligence.earnings_postgres_provider import (
                postgres_earnings_service,
            )
            result = postgres_earnings_service.load_week(key, start, database_url=database_url)
        else:
            result = earnings_api_service.load_week(
                key, start, cache_path=_earnings_setting("EARNINGSAPI_CACHE_PATH")
            )

    st.caption(f"{start:%b %d} – {end:%b %d, %Y} · EarningsAPI.com · Provider-reported dates")
    if result.retrieved_at and not result.error:
        retrieved = datetime.fromtimestamp(result.retrieved_at, ZoneInfo("America/New_York"))
        st.caption(f"Shared weekly snapshot · Retrieved {retrieved:%b %d, %Y at %I:%M %p} ET · Dates can change; check the issuer before acting.")
    if result.error:
        st.warning(result.error)
        st.info("The curated company-announcement schedule is available below.")
        return False
    from html import escape

    from app.intelligence.earnings_ranking import order_featured_events, select_page
    from app.intelligence.issuer_calendar import reconcile_provider_events

    events, issuer_sources, corrections = reconcile_provider_events(result.events, start, today)
    ordered, ordering = order_featured_events(events)
    if corrections:
        st.info(f'{corrections} provider schedules corrected using reviewed issuer announcements. Official sources are linked on the affected cards.')
    st.caption(ordering)
    from app.intelligence.earnings_ranking import (
        FEATURED_MAJOR_SYMBOLS,
        normalize_featured_symbol,
    )

    # Week-scoped widget identity survives Research navigation and resets on rollover.
    days = [start + timedelta(days=i) for i in range(5)]
    options = ['Top this week', 'All week', *[d.strftime('%a') for d in days]]
    saved_week, saved_choice = st.session_state.get('earnings_selection', (None, options[0]))
    initial = options.index(saved_choice) if saved_week == start.isoformat() and saved_choice in options else 0
    choice = st.radio('Browse earnings', options, horizontal=True, index=initial,
                      key=f'earnings_day_{start.isoformat()}')
    st.session_state['earnings_selection'] = (start.isoformat(), choice)
    chosen = days[options.index(choice) - 2] if choice not in options[:2] else None
    top = choice == 'Top this week' and not query
    candidates = tuple(e for e in ordered if normalize_featured_symbol(e.symbol) in FEATURED_MAJOR_SYMBOLS) if top else ordered
    st.subheader('Top earnings this week' if top else ('Search earnings this week' if query and chosen is None else 'Earnings this week' if chosen is None else chosen.strftime('%A earnings')))
    if top:
        st.caption('Up to 10 featured companies to start · Ranked across all reporting days. Browse All week for every provider event.')
    signature = (start.isoformat(), query, choice)
    if st.session_state.get('earnings_view') != signature:
        st.session_state['earnings_view'] = signature
        st.session_state['earnings_limit'] = 10
    rows, count = select_page(candidates, query, chosen, st.session_state.get('earnings_limit', 10))
    st.markdown(f"**{count:,} matching earnings events** · {len(events):,} this week · Showing {len(rows):,}")
    if result.rejected:
        st.caption(f"{result.rejected} inconsistent or invalid provider entries omitted.")
    if not rows:
        st.info("No matching provider events for this week. This is not proof that no companies are reporting.")
    st.markdown("""<style>
    div[data-testid="stRadio"] label[data-testid="stRadioOption"] {border:1px solid #586078;border-radius:18px;padding:3px 10px}
    div[data-testid="stRadio"] label[data-selected="true"] {border-color:#FF78B7;background:#121D35}
    div[data-testid="stRadio"] label:focus-within {outline:2px solid #FF78B7;outline-offset:2px}
    .earnings-card {padding:12px 16px 10px;border-top:2px solid #FF78B7;
      border-radius:12px;background:linear-gradient(130deg,#121D35,#0D1424);color:#f3f5fc;min-height:102px}
    .earnings-card h3 {font-size:1.3rem;margin:8px 0 4px;color:#fff}
    .earnings-card p {margin:0;overflow-wrap:anywhere}
    .earnings-meta {font-size:.85rem;color:#c2cade}
    </style>""", unsafe_allow_html=True)
    for index in range(0, len(rows), 2):
        columns = st.columns(2)
        for position, (col, event) in enumerate(zip(columns, rows[index:index + 2]), start=index + 1):
            with col, st.container(border=True):
                session = {"Before market": "BMO · Before market", "After market": "AMC · After market"}.get(event.session, "Time not supplied")
                st.markdown(f'<article class="earnings-card"><p class="earnings-meta">{event.day:%a, %b %d, %Y} · {session}</p>'
                            f'<h3>{("#" + str(position) + " · ") if top else ""}{escape(event.symbol)}</h3><p>{escape(event.name)}</p></article>', unsafe_allow_html=True)
                fact = issuer_sources.get((event.day, event.symbol))
                if fact:
                    st.caption('Source: Issuer announcement · Reviewed Nov 8, 2026')
                    st.link_button('Official announcement', fact['source'])
                else:
                    st.caption("Source: EarningsAPI.com · Provider-reported; not issuer-verified")
                if st.button(f"Research {event.symbol}", key=f"ea_{event.day.isoformat()}_{event.symbol}", width="stretch"):
                    open_stock_explorer(event.symbol)
    if len(rows) < count and st.button("Show 10 more", width="stretch"):
        st.session_state["earnings_limit"] = len(rows) + 10
        st.rerun()
    with st.expander("Data source and limitations"):
        st.write("Featured major companies uses a manually curated list of recognizable companies, not market-cap ranking or a complete list of large companies. Only this week’s provider events and dated, reviewed issuer release announcements can appear. Reviewed issuer release facts take precedence, with their official source linked; call-only announcements do not override release dates. This is a limited manual verification layer, not automatic verification of every provider event. Featured matches use a published editorial priority sequence across the entire week, then ticker for the remaining curated membership. Other events follow by date then ticker. Top this week includes only featured matches; All week includes provider events reconciled with the reviewed issuer releases; conflicting duplicates are replaced. Search and day filters cover the entire week. If the list has no matches, all events use date then ticker. True market-cap ranking is unavailable: no approved market-cap source is connected. No market caps are calculated or fetched.")
        from app.intelligence.earnings_ranking import EDITORIAL_PRIORITY
        st.caption('Editorial priority v3 (Nov 8, 2026): ' + ', '.join(EDITORIAL_PRIORITY) + '. Remaining curated companies: ticker order. This is editorial judgment, not a measured financial ranking.')
        if result.retrieved_at:
            timestamp = datetime.fromtimestamp(result.retrieved_at, ZoneInfo("America/New_York"))
            st.caption(f"Retrieved {timestamp:%b %d, %Y at %I:%M %p} ET · Shared cache up to 7 days, replaced on reporting-week rollover")
        if result.cache_expires_at:
            expires = datetime.fromtimestamp(result.cache_expires_at, ZoneInfo("America/New_York"))
            st.caption(f"Snapshot valid until {expires:%b %d, %Y at %I:%M %p} ET. The first later calendar visit loads the new reporting week; no visitor-triggered refresh before expiry.")
        st.write("EarningsAPI.com supplies the date and pre-market/after-market/unspecified category. It does not establish company confirmation, guarantee completeness, or supply an exact release time. The calendar is separate from SEC financial scores and is not investment advice. Provider results are displayed, not offered as a downloadable feed.")
        st.link_button("Provider documentation", "https://www.earningsapi.com/docs/calendar-earnings")
    return True


def render_earnings_week():
    st.title("Earnings calendar")
    st.write("See who's reporting earnings, then open their financial research in one click.")
    today = datetime.now(ZoneInfo("America/New_York")).date()
    # Release defaults to issuer-only coverage. Existing credentials/cache paths
    # cannot activate a hosted feed without a deliberate separate opt-in.
    enabled = _earnings_setting('EARNINGSAPI_ENABLED').casefold() == 'true'
    key = _earnings_api_key() if enabled else ''
    if key and _render_provider_calendar(today, key):
        return

    from app.intelligence.issuer_calendar import EVENTS, REVIEWED, select_events
    st.caption(f"Company-announced schedule · {len(EVENTS)} curated entries · Last reviewed {REVIEWED:%B %d, %Y}")
    if not enabled:
        st.info("Limited issuer-announcement calendar. Broader API coverage is paused for this release while persistent shared storage is arranged. This is not a complete earnings calendar.")
    elif not key:
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
