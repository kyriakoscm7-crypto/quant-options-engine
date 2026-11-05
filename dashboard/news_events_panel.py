"""Company discovery and source evidence in the shared research workspace."""

from datetime import date

import streamlit as st

from app.intelligence.company_directory_service import CompanyDirectoryService
from app.intelligence.news_events import NewsEventsService, configured_providers


@st.cache_resource
def _services():
    return CompanyDirectoryService(), NewsEventsService(configured_providers())


def render_news_events():
    st.subheader("News & Events Intelligence")
    st.caption("OFFICIAL IDENTITY · SOURCE EVIDENCE · TRANSPARENT COVERAGE")
    st.write("Search SEC filing entities, inspect disclosures and review headline identity evidence.")
    if not st.toggle("Connect official SEC directory and configured news sources", key="qi_news_connect"):
        st.info("Enable to search the SEC directory. News sources require operator-configured display rights; GDELT is optional.")
        return
    directory, service = _services()
    snapshot = directory.get()
    st.caption(f"SEC directory: {snapshot.status} · Cache age: {snapshot.age_seconds if snapshot.age_seconds is not None else 'unknown'} seconds")
    if snapshot.registry is None:
        st.warning("SEC directory unavailable. Configure QI_SEC_USER_AGENT with the application name and administrative email, or try later.")
        return
    query = st.text_input("Company name or SEC ticker", max_chars=100, key="qi_news_search")
    if not query.strip():
        return
    try:
        matches = snapshot.registry.search(query)
    except ValueError as error:
        st.warning(str(error))
        return
    if not matches:
        st.info("No matching SEC filing entity. Global listings are not fully covered.")
        return
    company = st.selectbox("Confirm company and security", matches,
                           format_func=lambda c: f"{c.ticker} · {c.name} · CIK {c.cik}")
    days = st.select_slider("Lookback in days", [1, 3, 7, 14, 30], value=7)
    event = st.date_input("Filings through date", value=date.today(), max_value=date.today())
    if st.button("Build intelligence report", type="primary"):
        with st.spinner("Gathering source evidence…"):
            st.session_state["qi_news_report"] = service.build(company, days=days, event_date=event)
        st.session_state["qi_news_report_key"] = (company, days, event)
    report = st.session_state.get("qi_news_report")
    if report is None or st.session_state.get("qi_news_report_key") != (company, days, event):
        return
    st.markdown(f"**{company.name} · {company.ticker}**")
    st.caption(f"CIK {company.cik} · Retrieved {report.as_of} · SEC filing entities, not exchange verification")
    a, b, c = st.columns(3)
    a.metric("Headline candidates", len(report.articles))
    b.metric("Official filings", len(report.filings))
    c.metric("Duplicates removed", report.duplicates)
    st.info("Coverage is incomplete. No results does not mean no events. Headline relevance is a heuristic, not factual verification; filings do not establish price causation or a confirmed earnings calendar.")
    news, filings, sources = st.tabs(["Headlines", "Official filings", "Coverage & sources"])
    with news:
        st.caption("News uses the recent lookback from retrieval time. The date control applies only to filings.")
        for item in report.articles:
            with st.container(border=True):
                st.text(item["title"])
                st.caption(f"{item['publisher']} · {item['published']} · {item['source']}")
                st.caption(f"{item['relevance']} · {item['reason']}")
                st.link_button("Read source ↗", item["url"])
        if not report.articles:
            st.write("No usable headlines returned. Check source status below.")
    with filings:
        st.caption("Recent SEC submissions only; archived filing pages are not searched. Same-day timing remains unverified.")
        for item in report.filings:
            with st.container(border=True):
                st.text(f"{item['form']} · {item['filing_date']} · {item['description']}")
                st.caption(item["relationship"])
                st.link_button("Open SEC filing ↗", item["url"])
        if not report.filings:
            st.write("No filings in the available submissions window, or SEC unavailable.")
    with sources:
        st.dataframe(list(report.diagnostics), hide_index=True, width="stretch")
        st.caption(f"Rejected invalid or out-of-window records: {report.rejected}. Distinct article totals are not a measure of market-wide coverage or accuracy.")
