"""Simple company and ticker search for Stock Explorer."""

import os
import re
from difflib import get_close_matches

import requests
import streamlit as st

from dashboard.stock_explorer_widget import SYMBOLS

KNOWN = {
    "S&P 500": "AMEX:SPY",
    "SP500": "AMEX:SPY",
    "SPY": "AMEX:SPY",
    "SHOPIFY": "TSX:SHOP",
    "SHOPIFY CANADA": "TSX:SHOP",
    "ROYAL BANK OF CANADA": "TSX:RY",
    "RBC": "TSX:RY",
    "CANADIAN NATIONAL RAILWAY": "TSX:CNR",
    "CNR": "TSX:CNR",
    "TD BANK": "TSX:TD",
    "TORONTO DOMINION BANK": "TSX:TD",
}

EXCHANGES = {
    "Nasdaq": "NASDAQ",
    "NYSE": "NYSE",
    "NYSE American": "AMEX",
    "NYSE Arca": "AMEX",
}

SYMBOL_PATTERN = re.compile(
    r"[A-Z0-9_]{1,24}:[A-Z0-9_.-]{1,64}"
)


@st.cache_data(ttl=86400, show_spinner=False)
def sec_search_directory(agent):
    """Load official US ticker/exchange associations once per day."""
    if not agent or "@" not in agent:
        return []

    response = requests.get(
        "https://www.sec.gov/files/company_tickers_exchange.json",
        headers={"User-Agent": agent, "Accept": "application/json"},
        timeout=15,
        stream=True,
    )
    try:
        response.raise_for_status()
        chunks = []
        size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 3_000_000:
                raise ValueError("Directory response too large.")
            chunks.append(chunk)

        import json

        payload = json.loads(b"".join(chunks))
        fields = payload["fields"]
        if not {"name", "ticker", "exchange"}.issubset(fields):
            raise ValueError("Unexpected directory format.")

        entries = []
        for row in payload["data"]:
            record = dict(zip(fields, row))
            exchange = EXCHANGES.get(record["exchange"])
            ticker = str(record["ticker"]).upper()
            if exchange and re.fullmatch(r"[A-Z0-9_.-]{1,64}", ticker):
                entries.append((
                    f"{exchange}:{ticker}",
                    str(record["name"]),
                    ticker,
                ))
        return entries
    finally:
        response.close()


def resolve(query):
    """Return confirmed matches without guessing unknown exchanges."""
    query = query.strip()
    upper = query.upper()

    if SYMBOL_PATTERN.fullmatch(upper):
        return [(upper, upper)]

    if not query or len(query) > 100:
        return []

    # Keep explicitly supported company shortcuts.
    results = []
    for label, symbol in SYMBOLS.items():
        company = label.split(" · ")[0]
        ticker = symbol.split(":")[-1]

        if upper in (company.upper(), ticker.upper()):
            results.append((symbol, label))

    if upper in KNOWN:
        results.append((KNOWN[upper], query))

    # US-listed records with published exchange associations.
    try:
        directory = sec_search_directory(
            os.environ.get("QI_SEC_USER_AGENT", "")
        )
    except (requests.RequestException, ValueError, KeyError, TypeError):
        directory = []

    for symbol, name, ticker in directory:
        name_upper = name.upper()

        if upper in (ticker, name_upper):
            results.append((symbol, name))

    if len(upper) >= 2:
        for symbol, name, ticker in directory:
            if (
                ticker.startswith(upper)
                or upper in name.upper()
            ):
                results.append((symbol, name))
                if len(results) >= 50:
                    break

    unique = {}
    for symbol, name in results:
        unique.setdefault(symbol, name)

    return list(unique.items())




def autocomplete_options(query):
    """Search verified listings, prioritizing exact matches and market cap."""
    query = query.strip()

    if not query or len(query) > 100:
        return []

    matches = resolve(query)
    upper = query.upper()

    # Market caps provide ranking signals for covered US companies.
    # This API is cached separately; a failure must never break search.
    caps = {}

    try:
        from dashboard.perp_market_size import market_universe, valid_cap

        snapshot = market_universe()

        for record in snapshot["records"]:
            if not isinstance(record, dict):
                continue

            ticker = str(record.get("ticker", "")).upper()
            cap = record.get("marketCapUsd")

            if (
                record.get("assetClass") == "equity"
                and str(record.get("country", "")).upper() == "US"
                and valid_cap(cap)
            ):
                caps[ticker] = max(caps.get(ticker, 0), cap)

    except Exception:
        # Company discovery remains usable if the optional
        # market-cap service is offline.
        pass

    def rank(item):
        symbol, name = item
        ticker = symbol.split(":")[-1].upper()
        clean_name = name.upper()

        exact_ticker = ticker == upper
        exact_name = clean_name == upper
        starts = (
            ticker.startswith(upper)
            or clean_name.startswith(upper)
        )

        verified_cap = (
            caps.get(ticker, 0)
            if symbol.split(":")[0] in {"NASDAQ", "NYSE", "AMEX"}
            else 0
        )

        return (
            0 if exact_ticker else
            1 if exact_name else
            2 if starts else 3,
            -verified_cap,
            clean_name,
            symbol,
        )

    matches = sorted(matches, key=rank)

    return [
        f"{name} | {symbol}"
        for symbol, name in matches[:15]
    ]






def render_search():
    """Live company autocomplete with persistent selection."""
    from streamlit_searchbox import st_searchbox

    # Receive navigation requests from Discover and other tools.
    # Do not guess an exchange for ambiguous or unknown tickers.
    incoming = st.session_state.pop("_research_ticker_request", None)
    incoming_handled = incoming is not None

    if incoming_handled:
        requested = str(incoming).strip().upper()

        if SYMBOL_PATTERN.fullmatch(requested):
            selected = requested
        else:
            matches = resolve(requested)
            exact_matches = {
                symbol for symbol, _ in matches
                if symbol.rsplit(":", 1)[-1] == requested
            }
            selected = (
                next(iter(exact_matches))
                if len(exact_matches) == 1
                else None
            )

        st.session_state["qi_active_stock_symbol"] = selected

        if selected is None:
            st.warning(
                "The requested stock could not be identified "
                "unambiguously. Search for its exact listing."
            )

    # Default to SPY only when no stock has been selected
    # and no navigation request has been received.
    if not incoming_handled:
        st.session_state.setdefault(
            "qi_active_stock_symbol", "AMEX:SPY"
        )

    st.markdown("#### Search the markets")
    st.caption(
        "Find companies by name, ticker, or exchange."
    )

    selection = st_searchbox(
        autocomplete_options,
        key="qi_live_stock_search_v2",
        label="Search a company or stock",
        placeholder="Search Apple, AMD, Shopify, NVIDIA...",
        debounce=250,
        clear_on_submit=True,
        edit_after_submit="disabled",
        default_options=["S&P 500 · SPY ETF | AMEX:SPY"],
    )

    if selection and not incoming_handled:
        symbol = selection.rsplit(" | ", 1)[-1]
        if SYMBOL_PATTERN.fullmatch(symbol):
            st.session_state["qi_active_stock_symbol"] = symbol

    active = st.session_state.get("qi_active_stock_symbol")

    if active:
        st.caption(f"Selected listing · {active}")
        return active

    st.caption("Search by company name, ticker or exchange.")
    return None


def suggested_tickers(query):
    """Offer familiar corrections without silently selecting them."""
    tickers = [
        symbol.split(":")[-1]
        for symbol in SYMBOLS.values()
    ]
    return get_close_matches(query.upper(), tickers, n=3, cutoff=0.65)
