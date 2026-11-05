"""Licensed, source-labelled market capitalization display."""

import math
import os
import re
from datetime import date

import requests
import streamlit as st


def size_category(cap, currency):
    """Broad company-size classification, using USD only."""
    if currency != "USD":
        return "Currency-normalized classification unavailable"
    if cap >= 200_000_000_000:
        return "Mega-cap"
    if cap >= 10_000_000_000:
        return "Large-cap"
    if cap >= 2_000_000_000:
        return "Mid-cap"
    if cap >= 300_000_000:
        return "Small-cap"
    if cap >= 50_000_000:
        return "Micro-cap"
    return "Nano-cap"


def compact(cap, currency):
    if cap >= 1e12:
        return f"{cap / 1e12:,.2f}T {currency}"
    if cap >= 1e9:
        return f"{cap / 1e9:,.2f}B {currency}"
    if cap >= 1e6:
        return f"{cap / 1e6:,.2f}M {currency}"
    return f"{cap:,.0f} {currency}"


@st.cache_data(ttl=3600, show_spinner=False)
def get_market_cap(symbol, api_key):
    """Get one dated market cap from an authorized API account."""
    response = requests.get(
        "https://financialmodelingprep.com/stable/market-capitalization",
        params={"symbol": symbol, "apikey": api_key},
        timeout=12,
    )
    response.raise_for_status()

    records = response.json()
    if not isinstance(records, list):
        return None

    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("symbol", "").upper() != symbol:
            continue

        value = record.get("marketCap")
        as_of = record.get("date")

        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value > 0
            and isinstance(as_of, str)
        ):
            try:
                day = date.fromisoformat(as_of)
            except ValueError:
                continue

            if day > date.today():
                continue

            return value, as_of

    return None


def render_market_size(symbol):
    """Display permitted market data, never inferred rankings."""
    # ETF and index market caps should not be confused
    # with the equity value of a single operating company.
    if symbol in {"AMEX:SPY", "SP:SPX"}:
        return

    # US listings only until international symbol mapping
    # and currency conversion are verified.
    exchange, _, ticker = symbol.partition(":")
    if exchange not in {"NASDAQ", "NYSE", "AMEX"}:
        return

    if not re.fullmatch(r"[A-Z0-9.-]{1,20}", ticker):
        return

    key = os.getenv("QI_FMP_API_KEY", "").strip()
    licensed = os.getenv("QI_FMP_DISPLAY_LICENSED") == "1"

    # Do not publish data without approved display rights.
    if not key or not licensed:
        return

    try:
        result = get_market_cap(ticker, key)
    except (requests.RequestException, ValueError, TypeError):
        result = None

    if result is None:
        st.caption("Current market capitalization is unavailable.")
        return

    cap, as_of = result
    classification = size_category(cap, "USD")

    st.markdown("#### Market size & standing")

    a, b, c = st.columns(3)

    a.metric("Market capitalization", compact(cap, "USD"))
    b.metric("Company size", classification)
    c.metric("Global market-cap rank", "Not available")

    st.caption(
        f"Market cap as of {as_of} · Source: Financial Modeling Prep · "
        "Rank requires a complete, licensed comparison universe. "
        "Company-size categories are approximate."
    )
