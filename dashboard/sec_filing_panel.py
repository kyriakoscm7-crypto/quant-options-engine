"""Official SEC filing research for selected market events."""

import os
from datetime import date

import streamlit as st

from app.intelligence.sec_filings import (
    fetch_sec_filings,
    validate_user_agent,
)

FORM_DESCRIPTIONS = {
    "8-K": "Current report",
    "10-K": "Annual report",
    "10-Q": "Quarterly report",
    "4": "Insider ownership transaction report",
    "SC 13D": "Beneficial ownership disclosure",
    "SC 13G": "Beneficial ownership disclosure",
}


@st.cache_data(ttl=3600, show_spinner=False)
def _cached_sec_search(
    ticker: str,
    event_date: str,
    user_agent: str,
) -> tuple[str, list[dict]]:
    return fetch_sec_filings(ticker, event_date, user_agent)


def render_sec_filings(ticker: str, event_date: str) -> None:
    """Display official filing links without claiming market causation."""

    st.markdown(
        "#### :primary[:material/description:] SEC Filing Intelligence"
    )

    st.caption(
        "Investigate official SEC EDGAR disclosures around "
        "the selected trading event. Results are matched by "
        "filing date, not verified public-release time."
    )

    try:
        day = date.fromisoformat(str(event_date)[:10])
    except ValueError:
        st.warning("The selected event date is invalid.")
        return

    ticker = ticker.strip().upper()
    user_agent = os.environ.get("SEC_USER_AGENT", "").strip()

    if not user_agent:
        try:
            user_agent = str(
                st.secrets.get("SEC_USER_AGENT", "")
            ).strip()
        except FileNotFoundError:
            user_agent = ""

    try:
        validate_user_agent(user_agent)
    except ValueError:
        st.info(
            "SEC searches are ready but not yet enabled. "
            "Configure SEC_USER_AGENT with an application name "
            "and real contact email in the Streamlit server environment."
        )
        st.caption(
            "The contact identity is sent to the SEC with requests. "
            "It is not displayed here or stored in the repository."
        )
        return

    request_key = f"{ticker}:{day.isoformat()}"

    if st.button(
        "Find SEC Filings Near Event",
        icon=":material/search:",
        key="qi_find_sec_filings",
    ):
        try:
            with st.spinner("Searching official SEC filings..."):
                company_name, filings = _cached_sec_search(
                    ticker,
                    day.isoformat(),
                    user_agent,
                )
        except Exception as exc:
            st.warning(f"SEC filing search unavailable: {exc}")
        else:
            st.session_state["qi_event_sec_results"] = {
                "request_key": request_key,
                "company_name": company_name,
                "filings": filings,
            }

    saved = st.session_state.get("qi_event_sec_results")

    if not saved or saved.get("request_key") != request_key:
        return

    filings = saved["filings"]
    company_name = saved["company_name"]

    st.caption(
        f"SEC registrant: {company_name} | "
        f"Event date: {day.isoformat()}"
    )

    if not filings:
        st.info(
            "No matching filings were returned from the recent "
            "SEC submissions data for this event window. "
            "This does not prove that no relevant disclosures existed."
        )
        return

    st.markdown(f"**{len(filings)} SEC filings found**")

    for filing in filings:
        form = filing["form"]
        filed = filing["filing_date"]
        relationship = filing["relationship"]
        description = filing.get("description", "")

        st.markdown(f"**Form {form} | {filed}**")

        form_context = FORM_DESCRIPTIONS.get(
            form,
            "Regulatory filing",
        )

        st.caption(f"{form_context} | {relationship}")

        if description:
            st.caption(description)

        st.link_button(
            "View Official SEC Filing",
            filing["url"],
            icon=":material/open_in_new:",
        )

        st.divider()

    st.caption(
        "Filings are retrieved from official SEC EDGAR data. "
        "A same-day filing is not necessarily available before "
        "the market opened. Filing proximity does not establish "
        "that the disclosure caused the observed stock movement."
    )
