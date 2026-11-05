"""Session-local research decisions, without ingesting third-party market data."""

import json
from datetime import date
from urllib.parse import urlencode, urlsplit

import pandas as pd
import streamlit as st

# Covers 50 maximum-length Unicode records, including legacy ASCII-escaped JSON.
MAX_IMPORT_BYTES = 16_000_000

STATUSES = ("To investigate", "Reading filings", "Monitoring", "Archived")
FIELDS = (
    "Research question",
    "Thesis & valuation",
    "Evidence & source links",
    "Risks & counterevidence",
    "Next review trigger",
)


# Verified primary SEC entity identifiers. Never synthesize a CIK from a ticker.
# EDGAR issuer IDs are not interchangeable with exchange tickers.
_VERIFIED_CIK = {
    "NASDAQ:AAPL": "0000320193",
    "NASDAQ:MSFT": "0000789019",
}


def official_filings_url(symbol: str) -> str:
    """Link to a verified SEC issuer, or to SEC's manual search.

    A symbol isn't a CIK. Unknown, ambiguous, cross-listed or foreign
    instruments must be matched by a human before using issuer filings.
    Do not construct an EDGAR browse URL from an unverified ticker.
    """
    cik = _VERIFIED_CIK.get(symbol.upper().strip())
    if cik is not None:
        return "https://www.sec.gov/edgar/browse/?" + urlencode(
            {
                "CIK": cik,
                "owner": "exclude",
            }
        )
    return "https://www.sec.gov/search-filings"


def safe_source_url(value: str) -> bool:
    """Never fetch user links; only offer ordinary external HTTPS links."""
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and not any(char.isspace() for char in value)
        )
    except ValueError:
        return False


def _add(symbol: str) -> None:
    notebook = st.session_state.setdefault("qi_discovery_notebook", {})
    if symbol not in notebook and len(notebook) < 50:
        notebook[symbol] = {
            "Status": STATUSES[0],
            "Source URL": "",
            "Source as of": "",
            **dict.fromkeys(FIELDS, ""),
        }


def validate_import(raw: bytes) -> dict:
    """Strict, bounded all-or-nothing restore; never fetch URLs or execute content."""
    import re

    if len(raw) > MAX_IMPORT_BYTES:
        raise ValueError("Import exceeds 16 MB")
    try:
        data = json.loads(raw)
    except (ValueError, RecursionError) as exc:
        raise ValueError("Invalid notebook JSON") from exc
    if not isinstance(data, dict) or data.get("format") not in (
        "Quant Intelligence research notebook v1",
        "Quant Intelligence research notebook v2",
    ):
        raise ValueError("Unsupported notebook format")
    rows = data.get("records")
    if not isinstance(rows, list) or len(rows) > 50:
        raise ValueError("Expected at most 50 records")
    result = {}
    fields = ("Status", "Source URL", "Source as of", *FIELDS)
    for row in rows:
        if isinstance(row, dict) and data["format"].endswith("v1"):
            row = {"Thesis & valuation": "", **row}
        if not isinstance(row, dict) or set(row) != {"Listing", *fields}:
            raise ValueError("Invalid record fields")
        listing = row["Listing"]
        if (
            not isinstance(listing, str)
            or not re.fullmatch(r"[A-Z0-9_]{1,24}:[A-Z0-9_.-]{1,64}", listing)
            or listing in result
        ):
            raise ValueError("Invalid or duplicate listing")
        entry = {key: row[key] for key in fields}
        if any(
            not isinstance(value, str) or len(value) > 6000 for value in entry.values()
        ):
            raise ValueError("Invalid or oversized research text")
        if entry["Status"] not in STATUSES or (
            entry["Source URL"] and not safe_source_url(entry["Source URL"])
        ):
            raise ValueError("Invalid status or HTTPS source URL")
        if len(entry["Source URL"]) > 2000 or len(entry["Source as of"]) > 80:
            raise ValueError("Source metadata too long")
        result[listing] = entry
    return result


def prepare_snapshot() -> None:
    revision = st.session_state.get("qi_notebook_revision", 0) + 1
    st.session_state["qi_notebook_revision"] = revision
    st.session_state["qi_notebook_snapshot"] = json.dumps(
        {
            "format": "Quant Intelligence research notebook v2",
            "revision": revision,
            "export_date": date.today().isoformat(),
            "provenance": "User-entered public-company research only; no provider data.",
            "records": comparison_rows(
                st.session_state["qi_discovery_notebook"],
                list(st.session_state["qi_discovery_notebook"]),
            ),
        },
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
    )


def render_record_editor(selected: str) -> None:
    notebook = st.session_state.setdefault("qi_discovery_notebook", {})
    entry = notebook[selected]
    with st.form(f"qi_record_form_{selected}"):
        st.caption(
            "Save & prepare export commits every field together, including the last field you type. Download the saved revision below."
        )
        values = {}
        values["Status"] = st.selectbox(
            "Status",
            STATUSES,
            index=STATUSES.index(entry["Status"]),
            key=f"qi_edit_{selected}_status",
        )
        for field in ("Source URL", "Source as of", *FIELDS):
            key = f"qi_edit_{selected}_{field}"
            if field in ("Source URL", "Source as of"):
                values[field] = st.text_input(
                    field,
                    value=entry[field],
                    max_chars=2000 if field == "Source URL" else 80,
                    key=key,
                )
            else:
                values[field] = st.text_area(
                    field, value=entry[field], max_chars=6000, height=100, key=key
                )
        if st.form_submit_button("Save & prepare export", type="primary"):
            if values["Source URL"] and not safe_source_url(values["Source URL"]):
                st.error("Use an HTTPS source URL without credentials.")
            else:
                notebook[selected] = values
                prepare_snapshot()
                st.success(
                    f"Saved revision {st.session_state['qi_notebook_revision']}. Your export includes all fields submitted above."
                )
    snapshot = st.session_state.get("qi_notebook_snapshot")
    if snapshot:
        st.caption(
            f"Download saved revision {st.session_state['qi_notebook_revision']}. Unsaved edits are excluded; save again after editing."
        )
        st.download_button(
            f"Download saved revision {st.session_state['qi_notebook_revision']} JSON",
            snapshot,
            "quant-intelligence-research.json",
            "application/json",
            key=f"qi_export_{selected}",
            on_click="ignore",
        )
    if entry["Source URL"] and safe_source_url(entry["Source URL"]):
        st.link_button("Open evidence link ↗", entry["Source URL"])


def _open_research(symbol: str) -> None:
    st.session_state["_research_ticker_request"] = symbol
    st.session_state["_navigation_request"] = "🔎 Stock Explorer"


def comparison_rows(notebook: dict, symbols: list[str]) -> list[dict]:
    """Compare recorded research; no inferred scores, facts or probabilities."""
    return [
        {"Listing": symbol, **notebook[symbol]}
        for symbol in symbols
        if symbol in notebook
    ]


def render_discovery_notebook(symbol: str | None) -> None:
    notebook = st.session_state.setdefault("qi_discovery_notebook", {})
    st.markdown("### Your opportunity shortlist")
    st.caption(
        "Session only · Up to 50 listings · Download before leaving. Your entries are processed by this server, not sent to TradingView. Use your own observations and links to public evidence; do not paste licensed feeds, account records or personal financial details."
    )
    if symbol and len(notebook) >= 50:
        st.caption(
            "Shortlist limit reached. Archived records still count. Delete individual records to free slots; save an export first."
        )
    if symbol:
        st.button(
            "Add selected listing to shortlist",
            key="qi_discovery_add",
            on_click=_add,
            args=(symbol,),
            disabled=symbol in notebook or len(notebook) >= 50,
        )
    with st.expander("Restore research JSON · replaces this session's records"):
        uploaded = st.file_uploader(
            "Notebook JSON · public-company notes only", type="json", max_upload_size=16
        )
        confirm = st.checkbox(
            "Replace this session's notebook with the validated import"
        )
        if st.button(
            "Restore validated notebook", disabled=not uploaded or not confirm
        ):
            try:
                restored = validate_import(uploaded.getvalue())
            except (ValueError, TypeError, KeyError):
                st.error("Invalid notebook. No records changed.")
            else:
                st.session_state["qi_discovery_notebook"] = restored
                for key in list(st.session_state):
                    if key.startswith("qi_edit_"):
                        del st.session_state[key]
                prepare_snapshot()
                st.rerun()
    if not notebook:
        st.info("Select a company to begin a source-linked research record.")
        return
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Listing": listing,
                    "Status": record["Status"],
                    "Research question": record["Research question"],
                    "Review trigger": record["Next review trigger"],
                }
                for listing, record in notebook.items()
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )
    selected = st.selectbox(
        "Edit shortlisted listing", list(notebook), key="qi_shortlist_edit"
    )
    st.button(
        "Investigate shortlisted company",
        key="qi_shortlist_open",
        on_click=_open_research,
        args=(selected,),
    )
    render_record_editor(selected)
    if st.button("Delete this listing's research", key="qi_record_delete"):
        del notebook[selected]
        for key in list(st.session_state):
            if key.startswith(f"qi_edit_{selected}_"):
                del st.session_state[key]
        prepare_snapshot()
        st.rerun()
    st.caption(
        "Evidence dates, status and notes are your records, not verified company facts. Check the issuer, currency, units, reporting period and amendments before comparing figures."
    )
    selection = st.multiselect(
        "Compare research records (up to four)",
        list(notebook),
        default=list(notebook)[:2],
        max_selections=4,
        key="qi_shortlist_compare",
    )
    if selection:
        st.dataframe(
            pd.DataFrame(comparison_rows(notebook, selection)),
            hide_index=True,
            use_container_width=True,
        )
    with st.expander("Research checklist & data limits"):
        st.write(
            "1. Identify the exact issuer and listing.\n2. Read its latest annual and interim reports, including risk factors.\n3. Record reporting periods, accounting basis, currency and source links.\n4. Challenge your thesis with debt, dilution, cash-flow and competitive risks.\n5. Set a specific review trigger and keep an independent copy of your notes."
        )
        st.write(
            "There is no authorized backend price or fundamental feed here. Valuation, growth, leverage and cash-flow figures are not invented or automatically scored. Provider screening remains inside its display. A completed notebook is not proof of investment merit."
        )
    if st.button("Clear this session's shortlist", key="qi_shortlist_clear"):
        for key in list(st.session_state):
            if key.startswith(("qi_shortlist_", "qi_edit_")):
                del st.session_state[key]
        st.session_state["qi_discovery_notebook"] = {}
        prepare_snapshot()
        st.rerun()
