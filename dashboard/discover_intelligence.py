"""Simple company evidence workspace; no widget extraction or recommendations."""
import os
from datetime import UTC, datetime

import streamlit as st

from app.intelligence.company_registry import CompanyRegistry
from app.intelligence.discover_evidence import earnings_label
from app.intelligence.discover_financials import health_observations
from app.intelligence.discover_screen import UNIVERSES, rank_reports
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
    agent = os.environ.get("QI_SEC_USER_AGENT", "")
    st.caption("SEC annual fundamentals · Dated issuer evidence · No investment recommendations")
    with st.expander("Data coverage & setup"):
        st.write("Coverage identifies SEC filers, not exchange listings. No sector adjustment; financial businesses may need different measures. International listings may be unsupported.")
        st.write("SEC: annual USD US-GAAP financial facts and recent filing links, retrieved on request. Directory cache: 24 hours; company evidence: one hour. Reporting periods can differ.")
        st.write("Licensed earnings calendars, analyst estimates, prices and valuation data are unavailable. SEC filing dates are not earnings dates. Stock Explorer retains its separate consented chart display.")
        st.code('export QI_SEC_USER_AGENT="Quant Intelligence $YOUR_REAL_CONTACT_EMAIL"', language="sh")
        st.caption("Replace the contact variable with your genuine operator email before starting Streamlit. No API key is required; an email-shaped value alone cannot prove contact ownership.")
    universe = st.selectbox("Start with a research universe", [*UNIVERSES, "My own tickers"])
    st.caption("Editorial starting sets or your own tickers · Up to eight companies per scan · No market-wide coverage")
    if not agent:
        st.info("SEC research is not connected. Set QI_SEC_USER_AGENT with your genuine operator contact, then restart Streamlit.")
        st.caption("Enable SEC research with a genuine operator contact in QI_SEC_USER_AGENT. No live facts or example scores are substituted.")
        return
    with st.form("discover_evidence_search"):
        tickers = st.text_input("Companies to investigate", value=", ".join(UNIVERSES.get(universe, ())), placeholder="AAPL, MSFT", max_chars=100,
                               help="Choose up to eight exact SEC tickers.")
        submitted = st.form_submit_button("Find research candidates", type="primary")
    with st.expander("Find SEC tickers by company name"):
        with st.form("discover_identity_search"):
            query = st.text_input("Company name or ticker", max_chars=100)
            find_identity = st.form_submit_button("Search official directory")
        if find_identity:
            try:
                directory = _gateway(agent).fetch("directory")
                matches = CompanyRegistry(directory["data"]).search(query)
                if matches:
                    st.dataframe([{"Ticker": c.ticker, "Company": c.name, "CIK": c.cik} for c in matches], hide_index=True)
                    st.caption(f"Official SEC directory retrieved {directory['retrieved_at']}. Copy exact tickers into Companies to investigate. Results identify filers, not verified exchange listings.")
                else:
                    st.info("No matching SEC filing entity. Try another company name or ticker.")
            except (ValueError, RuntimeError, OSError):
                st.warning("SEC company directory unavailable or search invalid. No identities substituted.")
    if submitted:
        symbols = list(dict.fromkeys(x.strip().upper() for x in tickers.split(",") if x.strip()))
        if not 1 <= len(symbols) <= 8:
            st.warning("Choose between one and eight SEC tickers.")
            st.session_state["qi_discover_reports"] = []
            st.session_state["qi_discover_errors"] = []
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
        with st.expander("Compare annual fundamentals"):
            st.markdown("#### Your comparison")
            st.caption("Annual periods can differ. Compare filing dates, accounting policies and sector context; ratios are not a score.")
            st.dataframe([{"Company": r["company"].name, "Annual period": (r["health"] or {}).get("period"),
                           **(r["health"] or {}).get("ratios", {})} for r in reports], hide_index=True)
    if reports:
        st.markdown("#### Research candidates")
        st.caption("Order: number of four disclosed criteria met, descending; ticker breaks ties. All four ratios and an annual period within 550 days are required; conflicts are excluded. This is a screening rule, not a quality or investment score. Missing evidence is never zero.")
        only_matches = st.checkbox("Show only candidates meeting at least three criteria")
        visible = [(r, screen) for r, screen in rank_reports(reports) if not only_matches or (screen["eligible"] and screen["matches"] >= 3)]
        if not visible:
            st.info("No candidates meet this screen. Clear the filter to inspect missing evidence and counterevidence.")
    else:
        visible = []
    if visible:
        st.caption(f"{len(visible)} companies shown · {sum(screen['eligible'] for _, screen in visible)} with comparable screening evidence")
        for candidate, candidate_screen in visible:
            candidate_health = candidate["health"] or {}
            with st.container(border=True):
                st.markdown(f"**{candidate['company'].ticker} · {candidate['company'].name}**")
                st.caption(f"Annual period {candidate_health.get('period') or 'unavailable'} · " +
                           (f"{candidate_screen['matches']} / 4 disclosed criteria met" if candidate_screen["eligible"] else candidate_screen["reason"]))
                observations = candidate_health.get("observations", {})
                st.write(" · ".join(f"{label}: ${observations[key]['value']:,.0f}" if key in observations else f"{label}: unavailable"
                                   for key, label in (("revenue", "Revenue"), ("income", "Net income"), ("operating_cash", "Operating cash"))).replace("$", r"\$"))
                st.caption("; ".join(health_observations(candidate_health)) if candidate_health else "Financial facts unavailable; inspect filing sources.")
        candidates = {r["company"].ticker: (r, screen) for r, screen in visible}
        labels = {ticker: f"{ticker} · {row[0]['company'].name}" for ticker, row in candidates.items()}
        selected = st.radio("Investigate a candidate", list(candidates), format_func=labels.get, horizontal=True)
        visible = [candidates[selected]]
    for report, screen in visible:
        company, health = report["company"], report["health"]
        with st.container(border=True):
            st.subheader(f"{company.name} · {company.ticker}")
            st.caption(f"SEC CIK {company.cik} · Identity matched to official directory · Coverage: {(health or {}).get('status', 'unavailable')}")
            st.write(f"{screen['matches']} of 4 criteria met" if screen["eligible"] else screen["reason"])
            for check in screen["checks"]:
                state = "Meets" if check["passes"] is True else "Does not meet" if check["passes"] is False else "Unavailable"
                value = check["value"]
                formatted = "unavailable" if value is None else f"{value:.2f}×" if check["factor"] == "Current ratio" else f"{value:.1%}"
                st.write(f"{state} · {check['criterion']} · Reported: {formatted}")
            if report["sources"]:
                st.caption(f"Evidence retrieved {report['sources'][-1]['retrieved_at']} · Build the brief again to check for updates.")
            if health:
                st.write(f"Annual financial health · period ending {health['period'] or 'unavailable'}")
                facts_columns = st.columns(3)
                for column, (key, label) in zip(facts_columns, (("revenue", "Annual revenue"), ("income", "Annual net income"), ("operating_cash", "Annual operating cash")), strict=True):
                    fact = health["observations"].get(key)
                    column.metric(label, f"${fact['value']:,.0f}" if fact else "Unavailable")
                dates = sorted({fact["filed"] for fact in health["observations"].values()})
                st.caption(f"Issuer-reported USD · Filed {', '.join(dates) or 'unavailable'} · Each observation retains its filing accession and source.")
                columns = st.columns(2)
                for index, (name, value) in enumerate(health["ratios"].items()):
                    columns[index % 2].metric(name, f"{value:.2f}×" if name == "Current ratio" else f"{value:.1%}")
                st.caption("Current ratio = current assets / current liabilities. Other figures divide liabilities by assets, net income by revenue, or operating cash by revenue. Same filing and period required; sector suitability is not assessed.")
                if health["issues"]:
                    st.warning("Evidence is incomplete or revised. Review the source issues before comparing this company.")
                for observation in health_observations(health):
                    st.write(observation)
                with st.expander("Financial facts & source evidence"):
                    st.dataframe(list(health["observations"].values()), hide_index=True)
                    for issue in health["issues"]:
                        st.write(f"• {issue}")
            st.markdown("**Catalysts & upcoming earnings**")
            earnings = report["earnings"]
            st.write(f"Evidence: {earnings['status']}")
            confirmed = [item for item in earnings["evidence"] if item.confirmed]
            for item in confirmed:
                st.write(earnings_label(item, now=datetime.now(UTC)))
                st.link_button(f"Earnings source · {item.provider}", item.url)
            if not confirmed:
                st.caption("No confirmed licensed catalyst available. A filing date is not an earnings date; estimated dates are not shown as catalysts.")
            st.markdown("**Analyst perspective**")
            st.caption("Unavailable · No licensed analyst dataset connected. SEC filings and news headlines do not establish expert sentiment.")
            st.markdown("**Risks & next investigation**")
            st.caption("These are accounting flags and research prompts, not an exhaustive business-risk assessment. Read the issuer’s risk factors and management discussion.")
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
