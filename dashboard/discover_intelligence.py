"""Simple company evidence workspace; no widget extraction or recommendations."""
import os
from datetime import UTC, datetime

import streamlit as st

from app.intelligence.discover_evidence import earnings_label
from app.intelligence.discover_financials import health_observations
from app.intelligence.discover_sec import SecGateway
from app.intelligence.discover_service import company_deep_dive


@st.cache_resource
def _gateway(agent):
    return SecGateway(agent)


def _investigation_steps(report):
    health = report["health"]
    steps = []
    if not health or health["issues"]:
        steps.append("Resolve missing or conflicting financial evidence in the latest annual filing.")
    if health and health["observations"].get("operating_cash", {}).get("value", 0) < 0:
        steps.append("Investigate negative annual operating cash flow and funding needs.")
    if report["earnings"]["status"] == "unavailable":
        steps.append("Verify the next earnings announcement on the issuer's investor-relations site.")
    else:
        steps.append("Review earnings evidence for estimates, timing changes and source conflicts.")
    steps.append("Read risk factors and record counterevidence before setting your next review trigger.")
    return steps


def render_intelligence():
    st.markdown("### Discover Intelligence")
    st.write("Understand the business. Check the evidence. Decide what to investigate next.")
    agent = os.environ.get("QI_SEC_USER_AGENT", "")
    a, b, c = st.columns(3)
    a.metric("Company financials", "Ready to check" if agent else "Not connected")
    b.metric("Earnings coverage", "Not connected")
    c.metric("Analyst coverage", "Not connected")
    st.caption("Company facts come from SEC EDGAR. Issuer reports are one source, not independent verification. Earnings dates and analyst views appear only when sourced coverage is connected.")
    if not agent:
        st.info("Company briefs are not connected yet. Keep investigating with Stock Explorer and your shortlist below.")
        return
    st.caption("SEC coverage identifies a filing entity, not an exchange listing. Use its exact SEC ticker; international listings may be unsupported.")
    with st.form("discover_evidence_search"):
        tickers = st.text_input("Companies to investigate", placeholder="AAPL, MSFT", max_chars=100,
                               help="Choose up to three SEC tickers to compare. No automatic investment ranking.")
        submitted = st.form_submit_button("Build company brief", type="primary")
    if submitted:
        symbols = list(dict.fromkeys(x.strip().upper() for x in tickers.split(",") if x.strip()))
        if not 1 <= len(symbols) <= 3:
            st.warning("Choose between one and three SEC tickers.")
        else:
            reports, errors = [], []
            for ticker in symbols:
                try:
                    with st.spinner(f"Checking SEC evidence for {ticker}…"):
                        reports.append(company_deep_dive(_gateway(agent), ticker))
                except (ValueError, LookupError, RuntimeError, OSError):
                    errors.append(f"{ticker}: SEC evidence unavailable or identity could not be verified. No company facts substituted.")
            st.session_state["qi_discover_reports"] = reports
            st.session_state["qi_discover_errors"] = errors
    for error in st.session_state.get("qi_discover_errors", []):
        st.warning(error)
    reports = st.session_state.get("qi_discover_reports", [])
    if len(reports) > 1:
        st.markdown("#### Your comparison")
        st.caption("Annual periods can differ. Compare filing dates, accounting policies and sector context; ratios are not a score.")
        st.dataframe([{"Company": r["company"].name, "Annual period": (r["health"] or {}).get("period"),
                       **(r["health"] or {}).get("ratios", {})} for r in reports], hide_index=True)
    for report in reports:
        company, health = report["company"], report["health"]
        with st.container(border=True):
            st.subheader(f"{company.name} · {company.ticker}")
            st.caption(f"SEC CIK {company.cik} · Identity matched to official directory · Coverage: {(health or {}).get('status', 'unavailable')}")
            if report["sources"]:
                st.caption(f"Evidence retrieved {report['sources'][-1]['retrieved_at']} · Build the brief again to check for updates.")
            if health:
                st.write(f"Annual financial health · period ending {health['period'] or 'unavailable'}")
                columns = st.columns(2)
                for index, (name, value) in enumerate(health["ratios"].items()):
                    columns[index % 2].metric(name, f"{value:.2f}×" if name == "Current ratio" else f"{value:.1%}")
                st.caption("Current ratio = current assets / current liabilities. Other figures divide liabilities by assets, net income by revenue, or operating cash by revenue. Same filing and period required; sector suitability is not assessed.")
                for observation in health_observations(health):
                    st.write(observation)
                with st.expander("Financial facts & source evidence"):
                    st.dataframe(list(health["observations"].values()), hide_index=True)
                    for issue in health["issues"]:
                        st.write(f"• {issue}")
            st.markdown("**Upcoming earnings**")
            earnings = report["earnings"]
            st.write(f"Evidence: {earnings['status']}")
            for item in earnings["evidence"]:
                st.write(earnings_label(item, now=datetime.now(UTC)))
                st.link_button(f"Earnings source · {item.provider}", item.url)
            if not earnings["evidence"]:
                st.caption("Date and time unavailable. A filing date is not an earnings date.")
            st.markdown("**Analyst perspective**")
            st.caption("Unavailable · No licensed analyst dataset connected. SEC filings and news headlines do not establish expert sentiment.")
            st.markdown("**Next investigation**")
            for step in _investigation_steps(report):
                st.write(f"• {step}")
            with st.expander("Recent filings & provenance"):
                for filing in report["filings"][:8]:
                    st.link_button(f"{filing['form']} · {filing['filing_date']} · {filing['accession']}", filing["url"])
                for source in report["sources"]:
                    st.link_button(f"SEC JSON · retrieved {source['retrieved_at']}", source["url"])
                st.caption("Recent submissions only; older filing history is not downloaded. SEC submissions and XBRL share one issuer origin and do not count as independent corroboration. Cached evidence retains its retrieval timestamp.")
            for issue in report["issues"]:
                st.warning(issue)
