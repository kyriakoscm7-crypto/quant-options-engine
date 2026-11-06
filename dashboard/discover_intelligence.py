"""Simple company evidence workspace; no widget extraction or recommendations."""
import os
from datetime import UTC, datetime
from html import escape

import streamlit as st

from app.intelligence.company_registry import CompanyRegistry
from app.intelligence.discover_evidence import earnings_label
from app.intelligence.discover_financials import health_observations
from app.intelligence.discover_screen import UNIVERSES, rank_reports
from app.intelligence.discover_sec import SecGateway
from app.intelligence.discover_service import company_deep_dive
from app.intelligence.filing_crosscheck import check_original_filing
from app.intelligence.fundamental_factors import (
    ANCHORS,
    ARCHETYPES,
    compatible,
    operating_scenario,
)
from app.intelligence.research_checks import internal_agreement, pattern_diagnostics


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


def format_factor(key, value):
    if value is None:
        return "Unavailable"
    if key == "cash_conversion":
        return f"{value:.2f}×"
    if key == "margin_change":
        return f"{value * 100:+.1f} pp"
    return f"{value:.1%}"


def company_synopsis(report):
    """Describe observed accounting facts without inferring investment merit."""
    research = report.get("research") or {}
    factors = research.get("factors", {})
    growth, margin = factors.get("revenue_cagr"), factors.get("operating_margin")
    if growth is None and margin is None:
        return "There is not enough comparable financial evidence to summarize this business."
    parts = []
    if growth is not None:
        parts.append(f"Sales {'grew' if growth >= 0 else 'fell'} by {abs(growth):.1%} a year over the observed annual history.")
    if margin is not None:
        parts.append(f"The latest annual business {'earned' if margin >= 0 else 'lost'} about {abs(margin) * 100:.0f}¢ in operating profit for every $1 of sales.")
    if research.get("issues"):
        parts.append("Some evidence needs review; see the source checks.")
    return " ".join(parts)


PATTERN_GUIDES = {
    "Quality compounders": "Looks for growing revenue, strong operating profit, consistent profits and manageable liabilities. It helps you find businesses to study for durability.",
    "Improving fundamentals": "Looks for improving margins, revenue growth and a comparable share-count trend. It helps you investigate what is changing inside a business.",
    "Cash generators": "Looks for cash left after equipment spending, cash backing profits and manageable liabilities. It helps you examine how reported profit turns into cash.",
    "Turnarounds to investigate": "Requires an observed move from loss to profit alongside improving fundamentals. It helps you investigate recovery evidence and what could reverse it.",
}


def _section_guide(title, text):
    st.markdown(f'<div style="background:#121D35;border-left:3px solid #FF78B7;border-radius:8px;padding:12px 16px;margin:4px 0 12px;color:#BBC7DE"><strong style="color:#F4F6FF">{escape(title)}</strong><br>{escape(text)}</div>', unsafe_allow_html=True)


def _source_checks(report, archetype):
    _section_guide("Evidence checks", "See what was checked, what is missing, and where each number came from. Agreement is useful only when definitions, dates and units match.")
    st.info("Primary issuer evidence only · SEC JSON and the issuer’s filing share one origin. Independent financial-source corroboration has not run.")
    st.caption("Public primary sources first · No paid feed connected. Links below let you inspect original documents; a link alone is not a completed cross-check.")
    st.markdown("**Original annual filing cross-check**")
    st.caption("On request, compare the SEC-extracted values with tagged facts in the original annual document. Same issuer origin; not an independent second dataset. Unsupported formats remain not comparable.")
    ticker = report["company"].ticker
    key = f"qi_filing_check_{ticker}"
    if st.button("Check original annual filing", key=f"check_filing_{ticker}"):
        try:
            with st.spinner("Comparing the original SEC annual document…"):
                result = check_original_filing(_gateway(os.environ.get("QI_SEC_USER_AGENT", "")), report)
            st.session_state[key] = result
        except (ValueError, RuntimeError, OSError):
            st.session_state.pop(key, None)
            st.warning("Original filing check unavailable. No agreement or replacement values assumed.")
    result = st.session_state.get(key)
    if result:
        agreed = sum(r["Status"] in {"exact agreement", "within reported rounding"} for r in result["rows"])
        unmatched = sum(r["Status"] == "not comparable" for r in result["rows"])
        st.caption(f"{agreed} agreeing observations · {unmatched} not comparable · {len(result['rows'])} examined. Agreement is document consistency, not a probability of accuracy.")
        st.dataframe(result["rows"], hide_index=True, width="stretch")
        st.link_button(f"Checked original filing · {result['accession']}", result["url"])
        st.caption(f"Document retrieved {result['retrieved_at']}. Discrepancies do not silently change scores; review them before relying on this pattern.")
        if any(r["Status"] in {"discrepancy", "conflicting filing facts"} for r in result["rows"]):
            st.warning("Original-document discrepancy detected. Treat this pattern as unresolved until the source contexts are reviewed.")
    checks = internal_agreement(report)
    st.markdown("**Internal extraction agreement**")
    st.caption("Two extraction paths over the same SEC payload. Not an independent-source check; different contexts remain not comparable.")
    st.dataframe(checks, hide_index=True, width="stretch")
    research = report.get("research") or {}
    window = research.get("factor_windows", {}).get("share_cagr")
    if window:
        st.caption(f"Share-count basis · {window['observations']} annual observations from one filing · {window['start']} → {window['end']} · {window['accession']}. No inferred split adjustment.")
    else:
        st.warning("Share-count basis is not comparable across at least three annual observations in one filing. Share CAGR is unavailable; a split is never treated as dilution by inference.")
    for issue in research.get("issues", []):
        st.write(f"• {issue}")
    st.markdown("**Cross-check the original documents**")
    for filing in report.get("filings", [])[:8]:
        st.link_button(f"{filing['form']} · {filing['filing_date']} · {filing['accession']}", filing["url"])
    for source in report.get("sources", []):
        st.link_button(f"SEC JSON · retrieved {source['retrieved_at']}", source["url"])
    if not report.get("filings") and not report.get("sources"):
        st.caption("No source links available in this report.")
    if research:
        diagnostics = pattern_diagnostics(research, archetype)
        st.markdown("**How much does each factor affect the pattern?**")
        st.caption("Remove one factor at a time and average the rest. This tests dependence on the chosen inputs; it is not a confidence interval, a validated accuracy estimate or a replacement score.")
        if diagnostics["omission_min"] is not None:
            st.write(f"Remaining-factor means: {diagnostics['omission_min']:.1f}–{diagnostics['omission_max']:.1f} / 100")
            st.dataframe(diagnostics["omissions"], hide_index=True, width="stretch")
        else:
            st.caption("Sensitivity unavailable for an unranked pattern.")
        st.caption(f"{len(diagnostics['at_anchor'])} selected factors are at a fixed anchor boundary. Beyond that boundary, a more extreme raw value does not improve the factor score.")


def _filing_warning(ticker):
    result = st.session_state.get(f"qi_filing_check_{ticker}") or {}
    if any(r["Status"] in {"discrepancy", "conflicting filing facts"} for r in result.get("rows", [])):
        st.warning("Evidence discrepancy · Pattern unresolved. Review Evidence & checks before relying on this score.")


def _margin_trend(history):
    """Render observed annual margins only; missing observations break the line."""
    values = [h.get("operating_margin") for h in history]
    known = [v for v in values if v is not None]
    if len(known) < 2:
        return
    low, high = min(known), max(known)
    spread = high - low or 1
    points = [(8 + i * 284 / max(1, len(values) - 1), 48 - (v - low) / spread * 36)
              if v is not None else None for i, v in enumerate(values)]
    segments = "".join(f'<line x1="{a[0]:.2f}" y1="{a[1]:.2f}" x2="{b[0]:.2f}" y2="{b[1]:.2f}"/>'
                       for a, b in zip(points, points[1:]) if a and b)
    dots = "".join(f'<circle cx="{p[0]:.2f}" cy="{p[1]:.2f}" r="3"/>' for p in points if p)
    label = "Operating margin · observed annual periods; gaps are missing"
    st.markdown(f'<svg viewBox="0 0 300 60" height="60" width="100%" role="img" aria-label="{label}"><title>{label}</title><g stroke="#FF78B7" stroke-width="2" fill="#FF78B7">{segments}{dots}</g></svg>', unsafe_allow_html=True)
    first, last = history[0], history[-1]
    st.caption(f"Operating margin · {first['period']} {format_factor('operating_margin', values[0])} → {last['period']} {format_factor('operating_margin', values[-1])}")


def _research_detail(research, ticker, archetype, report):
    overview = st.container()
    trends = st.expander("Financial history")
    factors = st.expander("How the pattern is calculated")
    scenarios = st.expander("Try a business scenario")
    evidence = st.expander("Sources & evidence checks")
    with evidence:
        st.caption(f"As of {research['as_of']} · {research['coverage']} factors available · {research['sector']}")
        st.caption(research["uncertainty"])
        _source_checks(report, archetype)
    with overview:
        st.write(company_synopsis(report))
        st.caption("Financial quality: annual SEC evidence · Valuation: unavailable · Market environment: unavailable · Earnings: see Earnings this week for calendar coverage")
    import pandas as pd
    history = research["history"]
    with trends:
        chart = pd.DataFrame([{"Period": h['period'], "Operating margin": h['operating_margin'],
                               "FCF margin": h['fcf_margin']} for h in history])
        if not chart.empty:
            st.line_chart(chart.set_index("Period"), y_label="Margin (decimal)", color=["#FF78B7", "#79D4CF"])
        _section_guide("Follow the reported trajectory", "Compare annual revenue, operating cash and balance-sheet figures over time. Trends show what happened; they do not predict what happens next.")
        for title, metrics in (("Annual revenue & operating cash · USD", ("revenue", "cfo")), ("Assets & liabilities · USD", ("assets", "liabilities"))):
            frame = pd.DataFrame([{"Period": h["period"], **{k.replace("_", " ").title(): (h["observations"].get(k) or {}).get("value") for k in metrics}} for h in history])
            if not frame.empty:
                st.caption(title)
                st.line_chart(frame.set_index("Period"), color=["#FF78B7", "#79D4CF"])
        st.caption("Reported annual observations; gaps remain missing. Accounting tags and revisions are retained in evidence below.")
    with factors:
        _section_guide("See the math behind the fit", "Eight accounting measures describe growth, profitability, cash and financing. Your selected pattern uses only the marked factors, with equal weights.")
        st.markdown("**All 8 factors · contributions, formulas & filing evidence**")
        st.caption("Fixed-anchor normalization: clip (value − lower)/(upper − lower) to [0,1], reverse for lower-is-better, multiply by 100. Equal weights; all archetype factors required. Scores describe accounting patterns, not probabilities. No sample-relative or sector percentile claims.")
        st.dataframe([{"Factor": k, "Value": format_factor(k, v), "Pattern score / 100": research['scores'][k],
                       "Lower anchor": ANCHORS[k][0], "Upper anchor": ANCHORS[k][1],
                       "Direction": "higher" if ANCHORS[k][2] == 1 else "lower",
                       "In selected pattern": k in ARCHETYPES[archetype]}
                      for k, v in research['factors'].items()], hide_index=True)
        with st.expander("Methodology & observation ledger"):
            st.write("Revenue and share CAGR use actual elapsed years with at least three consecutive annual observations and unchanged tags. Share CAGR additionally requires a common filing basis and may use a shorter explicitly dated window; no split adjustment is inferred. Margin change is last minus first (percentage points). Earnings consistency is positive-income years / observed consecutive years. FCF = CFO − positive reported PP&E purchases; excludes acquisitions and other investment. Cash conversion = CFO / positive net income. Liabilities / assets uses positive assets. Ratios require identical filing accession and period; unavailable is never zero.")
            st.dataframe([o for h in history for o in h['observations'].values() if o], hide_index=True)
            for issue in research['issues']:
                st.write(issue)
    with overview:
        st.markdown("**What could go wrong**")
        for risk in research['risks']:
            st.write(f"• {risk}")
    with scenarios:
        _section_guide("Test your operating assumptions", "Change sales and profit margin to see the mechanical effect on operating income. You choose the shocks; this is not a forecast or a stock-price model.")
        st.markdown("**Stress the operating thesis · user assumptions**")
        st.caption("Mechanical sensitivity, not a forecast. Applies user-selected revenue and margin shocks to the latest reported annual operating result. No tax, financing, cash-flow or stock-price projection.")
        obs = history[-1]['observations'] if history else {}
        rev, inc = obs.get('revenue'), obs.get('operating_income')
        if compatible(rev, inc) and rev['value'] > 0:
            shock = st.slider("Revenue change (%)", -100, 100, -10, key=f"rev_{ticker}")
            margin = st.slider("Operating margin change (percentage points)", -20., 20., -2., step=.5, key=f"margin_{ticker}")
            result = operating_scenario(rev['value'], inc['value'], revenue_change=shock / 100, margin_change_pp=margin)
            st.metric("Hypothetical operating income", f"${result['operating_income']:,.0f}", f"${result['income_change']:,.0f} vs reported")
            st.caption(f"Hypothetical revenue ${result['revenue']:,.0f}; operating margin {result['operating_margin']:.1%}. Baseline annual period {research['period']}.")
        else:
            st.info("Compatible annual revenue and operating income required; no assumed baseline.")


def render_intelligence():
    agent = os.environ.get("QI_SEC_USER_AGENT", "")
    if st.session_state.get("qi_earnings_origin") and st.button("← Back to earnings week"):
        st.session_state.pop("qi_earnings_origin", None)
        st.session_state["_navigation_request"] = "📅 Earnings this week"
        st.rerun()
    st.write("Understand the business before you consider the stock.")
    st.caption("Annual SEC financials only. Price, valuation and market conditions are not assessed; no overall investment score is available.")
    with st.expander("Data coverage & setup"):
        st.write("Coverage identifies SEC filers, not exchange listings. Generic factor rankings exclude financial/real estate and utility SIC ranges; missing SIC prevents ranking. International listings may be unsupported.")
        st.write("SEC: annual USD US-GAAP financial facts and recent filing links, retrieved on request. Directory cache: 24 hours; company evidence: one hour. Reporting periods can differ.")
        st.write("The separate Earnings this week page supports a configured Finnhub calendar. Analyst estimates, prices and valuation data are unavailable here. SEC filing dates are not earnings dates. Stock Explorer retains its separate consented chart display.")
        st.code('export QI_SEC_USER_AGENT="Quant Intelligence $YOUR_REAL_CONTACT_EMAIL"', language="sh")
        st.caption("Replace the contact variable with your genuine operator email before starting Streamlit. No API key is required; an email-shaped value alone cannot prove contact ownership.")
    with st.expander("Research universe & SEC search", expanded=not bool(st.session_state.get("qi_discover_reports"))):
        with st.expander("Change starting companies"):
            universe = st.selectbox("Start with a research universe", [*UNIVERSES, "My own tickers"])
        st.caption("Editorial starting sets or your own tickers · Up to eight companies per scan · No market-wide coverage")
        if not agent:
            st.info("SEC research is not connected. Set QI_SEC_USER_AGENT with your genuine operator contact, then restart Streamlit.")
            st.caption("Enable SEC research with a genuine operator contact in QI_SEC_USER_AGENT. No live facts or example scores are substituted.")
            return
        with st.form("discover_evidence_search"):
            tickers = st.text_input("Companies to investigate", value=", ".join(UNIVERSES.get(universe, ())), placeholder="AAPL, MSFT", max_chars=100,
                                   help="Choose up to eight exact SEC tickers.", key=f"qi_tickers_{universe}")
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
                for state_key in list(st.session_state):
                    if state_key.startswith("qi_filing_check_"):
                        del st.session_state[state_key]
                st.session_state.pop("qi_detail", None)
                st.session_state["qi_discover_reports"] = reports
                st.session_state["qi_discover_errors"] = errors
                st.rerun()
    for error in st.session_state.get("qi_discover_errors", []):
        st.warning(error)
    reports = list({r["company"].ticker: r for r in st.session_state.get("qi_discover_reports", [])}.values())
    archetype = st.session_state.get("qi_pattern", next(iter(ARCHETYPES)))
    modern = any(r.get("research") for r in reports)
    visible = []
    if reports:
        with st.expander("Research options & comparison"):
            archetype = st.radio("Research pattern", list(ARCHETYPES), horizontal=True, key="qi_pattern")
            st.caption("Pattern fit describes an accounting archetype, not expected returns or an investment recommendation. Missing evidence remains unranked.")
            controls = st.columns([2, 1])
            query = controls[0].text_input("Search candidates", placeholder="Company or ticker", key="qi_candidate_query")
            order = controls[1].selectbox("Sort by", ["Pattern fit", "Company A–Z", "Revenue growth", "Operating margin"], key="qi_candidate_sort")
            only_matches = st.checkbox("Show only ranked pattern matches" if modern else "Show only candidates meeting at least three criteria")
            def score(report):
                return ((report.get("research") or {}).get("archetypes", {}).get(archetype, {}).get("score"))
            for report, screen in rank_reports(reports):
                identity = report["company"]
                ranked = score(report) is not None if modern else screen["eligible"] and screen["matches"] >= 3
                if query.strip().casefold() not in f"{identity.ticker} {identity.name}".casefold() or (only_matches and not ranked):
                    continue
                visible.append((report, screen))
            def sort_key(row):
                report, screen = row
                value = score(report) if modern else screen["matches"]
                if order in ("Revenue growth", "Operating margin"):
                    value = (report.get("research") or {}).get("factors", {}).get("revenue_cagr" if order == "Revenue growth" else "operating_margin")
                return (report["company"].name.casefold(),) if order == "Company A–Z" else (value is None, -(value or 0), report["company"].ticker)
            visible.sort(key=sort_key)
            st.caption(f"{len(visible)} of {len(reports)} companies · Annual SEC evidence")
            if not visible:
                st.info("No candidates match. Clear search or the ranked filter to inspect all evidence.")
            labels = {r["company"].ticker: f"{r['company'].ticker} · {r['company'].name}" for r in reports}
            # Keep comparison independent of the current search and reconcile refreshed universes.
            previous = st.session_state.get("qi_compare", [])
            retained = [t for t in previous if t in labels]
            if retained != previous:
                st.session_state["qi_compare"] = retained
            compare = st.multiselect("Compare companies · choose up to four", list(labels), format_func=labels.get, max_selections=4, key="qi_compare")
            if len(compare) >= 2:
                with st.expander("Your comparison", expanded=True):
                    st.caption("Reporting periods may differ. Missing values are unavailable, never zero.")
                    st.dataframe([{"Company": r["company"].ticker, "Annual period": (r.get("research") or r.get("health") or {}).get("period"),
                                   "Pattern fit / 100": score(r),
                                   **{k.replace("_", " ").title(): format_factor(k, v) for k, v in (r.get("research") or {}).get("factors", {}).items()},
                                   **{k: (f"{v:.2f}×" if k == "Current ratio" else f"{v:.1%}") for k, v in (r.get("health") or {}).get("ratios", {}).items()}}
                                  for r in reports if r["company"].ticker in compare], hide_index=True, width="stretch")
        st.markdown("""<style>
        .st-key-qi_cards [data-testid="stVerticalBlock"][data-border="true"] {background:#121D35;border-radius:18px;}
        .st-key-qi_cards [data-testid="stVerticalBlock"] {gap:.55rem}
        .qi-score {color:#FF78B7;font-size:2rem;font-weight:700;line-height:1.2}
        .qi-name {font-size:1.1rem;font-weight:650;color:#F4F6FF;overflow-wrap:anywhere}
        .qi-meta {color:#BBC7DE;font-size:.85rem}
        .qi-facts {display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0;color:#F4F6FF}
        .qi-facts small {display:block;color:#BBC7DE}
        button:focus-visible,input:focus-visible {outline:3px solid #FF78B7!important;outline-offset:3px}
        @media(max-width:700px){.st-key-qi_cards [data-testid="stHorizontalBlock"] {flex-direction:column}.st-key-qi_cards [data-testid="stColumn"] {width:100%!important;flex:1 1 100%!important}}
        </style>""", unsafe_allow_html=True)
        if not st.session_state.get("qi_detail"):
            with st.container(key="qi_cards"):
                for start in range(0, len(visible), 2):
                    columns = st.columns(2)
                    for column, (candidate, candidate_screen) in zip(columns, visible[start:start+2]):
                        with column, st.container(border=True):
                            company = candidate["company"]
                            research = candidate.get("research") or {}
                            pattern = research.get("archetypes", {}).get(archetype, {})
                            fit = pattern.get("score")
                            st.markdown(f'<div class="qi-meta">{escape(company.ticker)}</div><div class="qi-name">{escape(company.name)}</div>', unsafe_allow_html=True)
                            _filing_warning(company.ticker)
                            if research:
                                st.write(company_synopsis(candidate))
                                factors = research.get("factors", {})
                                st.markdown('<div class="qi-facts">' + ''.join(f'<div><small>{label}</small>{format_factor(key, factors.get(key))}</div>' for key, label in (("revenue_cagr", "Sales growth / year"), ("operating_margin", "Profit from each sales dollar"))) + '</div>', unsafe_allow_html=True)
                                _margin_trend(research.get("history", []))
                                if fit is None:
                                    st.caption("Why unranked · " + "; ".join(pattern.get("reasons", [])))
                            else:
                                st.write(f"{candidate_screen['matches']} of 4 criteria met" if candidate_screen["eligible"] else candidate_screen["reason"])
                                for key, label in (("revenue", "Revenue"), ("income", "Net income")):
                                    fact = (candidate.get("health") or {}).get("observations", {}).get(key)
                                    st.caption(f"{label}: ${fact['value']:,.0f}" if fact else f"{label}: unavailable")
                            st.caption(f"Annual period {research.get('period') or (candidate.get('health') or {}).get('period') or 'unavailable'}")
                            sources = candidate.get("sources", [])
                            st.caption(f"Retrieved {sources[-1]['retrieved_at']}" if sources else "Retrieval timestamp unavailable")
                            if st.button(f"Open {company.ticker} research →", key=f"open_{company.ticker}", width="stretch"):
                                st.session_state["qi_detail"] = company.ticker
                                st.rerun()
        selected = st.session_state.get("qi_detail")
        chosen = next((row for row in rank_reports(reports) if row[0]["company"].ticker == selected), None)
        if chosen:
            if st.button("← Back to candidates"):
                for state_key in list(st.session_state):
                    if state_key.startswith("qi_filing_check_"):
                        del st.session_state[state_key]
                st.session_state.pop("qi_detail", None)
                st.rerun()
            visible = [chosen]
        else:
            visible = []
    for report, screen in visible:
        company, health = report["company"], report["health"]
        with st.container(border=True):
            st.subheader(f"{company.name} · {company.ticker}")
            _filing_warning(company.ticker)
            st.caption(f"SEC CIK {company.cik} · Identity matched to official directory · Coverage: {(health or {}).get('status', 'unavailable')}")
            if report.get("research"):
                pattern = report["research"]["archetypes"][archetype]
                fit = pattern["score"]
                with st.expander("Accounting pattern fit · not an investment rating"):
                    st.markdown(f"**{archetype} · {fit:.0f}/100 pattern fit**" if fit is not None else f"**{archetype} · Unranked**")
                    st.caption(PATTERN_GUIDES[archetype])
                    st.caption("Accounting pattern only · Not expected returns or a recommendation")
                _research_detail(report["research"], company.ticker, archetype, report)
            if not modern:
                st.write(f"{screen['matches']} of 4 criteria met" if screen["eligible"] else screen["reason"])
            for check in ([] if modern else screen["checks"]):
                state = "Meets" if check["passes"] is True else "Does not meet" if check["passes"] is False else "Unavailable"
                value = check["value"]
                formatted = "unavailable" if value is None else f"{value:.2f}×" if check["factor"] == "Current ratio" else f"{value:.1%}"
                st.write(f"{state} · {check['criterion']} · Reported: {formatted}")
            if report["sources"]:
                st.caption(f"Evidence retrieved {report['sources'][-1]['retrieved_at']} · Build the brief again to check for updates.")
            if health and not modern:
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
            with st.expander("Event coverage & next investigation"):
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
            if not report.get("research"):
                with st.expander("Recent filings & provenance"):
                    for filing in report["filings"][:8]:
                        st.link_button(f"{filing['form']} · {filing['filing_date']} · {filing['accession']}", filing["url"])
                    for source in report["sources"]:
                        st.link_button(f"SEC JSON · retrieved {source['retrieved_at']}", source["url"])
                    st.caption("Recent submissions only; older filing history is not downloaded. SEC submissions and XBRL share one issuer origin and do not count as independent corroboration. Cached evidence retains its retrieval timestamp.")
            for issue in report["issues"]:
                st.warning(issue)
