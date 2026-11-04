"""Session-local research decisions, without ingesting third-party market data."""

import json
from datetime import date
from urllib.parse import urlencode, urlsplit

import pandas as pd
import streamlit as st

STATUSES = ("To investigate", "Reading filings", "Monitoring", "Archived")
FIELDS = ("Research question", "Evidence & source links", "Risks & counterevidence", "Next review trigger")


def official_filings_url(symbol: str) -> str:
    """Link to a search, not a claim of verified issuer identity or coverage."""
    return "https://www.sec.gov/edgar/browse/?" + urlencode({
        "CIK": symbol.split(":", 1)[-1], "owner": "exclude",
    })


def safe_source_url(value: str) -> bool:
    """Never fetch user links; only offer ordinary external HTTPS links."""
    try:
        parsed = urlsplit(value)
        return (parsed.scheme == "https" and bool(parsed.hostname)
                and not parsed.username and not parsed.password
                and not any(char.isspace() for char in value))
    except ValueError:
        return False


def _save(symbol: str, field: str, key: str) -> None:
    st.session_state["qi_discovery_notebook"][symbol][field] = st.session_state[key]


def _add(symbol: str) -> None:
    notebook = st.session_state.setdefault("qi_discovery_notebook", {})
    if symbol not in notebook and len(notebook) < 50:
        notebook[symbol] = {"Status": STATUSES[0], "Source URL": "",
                            "Source as of": "", **dict.fromkeys(FIELDS, "")}


def comparison_rows(notebook: dict, symbols: list[str]) -> list[dict]:
    """Compare recorded research; no inferred scores, facts or probabilities."""
    return [{"Listing": symbol, **notebook[symbol]} for symbol in symbols if symbol in notebook]


def render_discovery_notebook(symbol: str | None) -> None:
    notebook = st.session_state.setdefault("qi_discovery_notebook", {})
    st.markdown("### Your opportunity shortlist")
    st.caption("Session only · Up to 50 listings · Download before leaving. Your entries are processed by this server, not sent to TradingView. Use your own observations and links to public evidence; do not paste licensed feeds, account records or personal financial details.")
    if symbol:
        st.button("Add selected listing to shortlist", key="qi_discovery_add",
                  on_click=_add, args=(symbol,), disabled=symbol in notebook or len(notebook) >= 50)
    if not notebook:
        st.info("Start with a company, record a research question, then look for evidence that supports or challenges it. No company is automatically ranked or recommended.")
        return
    selected = st.selectbox("Edit shortlisted listing", list(notebook), key="qi_shortlist_edit")
    entry = notebook[selected]
    for field in ("Status", "Source URL", "Source as of", *FIELDS):
        key = f"qi_shortlist_{selected}_{field}"
        args = {"key": key, "on_change": _save, "args": (selected, field, key)}
        if field == "Status":
            st.selectbox(field, STATUSES, index=STATUSES.index(entry[field]), **args)
        elif field == "Source as of":
            st.text_input("Evidence date / reporting period (your record)", value=entry[field], max_chars=80, **args)
        elif field == "Source URL":
            st.text_input("Primary evidence URL", value=entry[field], max_chars=2000, **args)
        else:
            st.text_area(field, value=entry[field], max_chars=6000, height=100, **args)
    source = entry["Source URL"]
    if source and safe_source_url(source):
        st.link_button("Open your evidence link ↗", source)
    elif source:
        st.warning("Use an HTTPS source link without credentials. Links are never fetched or verified by this app.")
    st.caption("Evidence dates, status and notes are your records, not verified company facts. Check the issuer, currency, units, reporting period and amendments before comparing figures.")
    selection = st.multiselect("Compare research records (up to four)", list(notebook),
                               default=list(notebook)[:2], max_selections=4, key="qi_shortlist_compare")
    if selection:
        st.dataframe(pd.DataFrame(comparison_rows(notebook, selection)), hide_index=True,
                     use_container_width=True)
    st.download_button("Download shortlist & evidence", json.dumps({
        "format": "Quant Intelligence research notebook v1",
        "export_date": date.today().isoformat(),
        "provenance": "User-entered research only; no provider data or verified rankings.",
        "records": comparison_rows(notebook, list(notebook)),
    }, indent=2), "quant-intelligence-research.json", "application/json", key="qi_shortlist_export")
    with st.expander("Research checklist & data limits"):
        st.write("1. Identify the exact issuer and listing.\n2. Read its latest annual and interim reports, including risk factors.\n3. Record reporting periods, accounting basis, currency and source links.\n4. Challenge your thesis with debt, dilution, cash-flow and competitive risks.\n5. Set a specific review trigger and keep an independent copy of your notes.")
        st.write("There is no authorized backend price or fundamental feed here. Valuation, growth, leverage and cash-flow figures are not invented or automatically scored. Provider screening remains inside its display. A completed notebook is not proof of investment merit.")
    if st.button("Clear this session's shortlist", key="qi_shortlist_clear"):
        for key in list(st.session_state):
            if key.startswith("qi_shortlist_"):
                del st.session_state[key]
        st.session_state["qi_discovery_notebook"] = {}
        st.rerun()
