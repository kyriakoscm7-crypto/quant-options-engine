"""Market-size research using the attributed PerpEquities public API."""

import math
from datetime import UTC, datetime

import requests
import streamlit as st

from dashboard.market_size_intelligence import compact, size_category

API_URL = "https://perpequities.com/api/v1/assets"


def valid_cap(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


@st.cache_data(ttl=600, show_spinner=False)
def market_universe():
    """Fetch one bounded, cached snapshot of covered equities."""
    response = requests.get(
        API_URL,
        params={"assetClass": "equity", "limit": 2000},
        headers={"Accept": "application/json"},
        timeout=15,
        stream=True,
    )
    try:
        response.raise_for_status()

        chunks = []
        size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 8_000_000:
                raise ValueError("Market data response too large.")
            chunks.append(chunk)

        import json

        payload = json.loads(b"".join(chunks))

        if not isinstance(payload, dict):
            raise ValueError("Invalid market-data response.")

        records = payload.get("data")
        if not isinstance(records, list):
            raise ValueError("Market data missing.")

        total = payload.get("total")
        complete = (
            isinstance(total, int)
            and not isinstance(total, bool)
            and total == len(records)
        )

        return {
            "records": records,
            "complete": complete,
            "generated": payload.get("generatedAt"),
            "stale": payload.get("stale", False),
        }
    finally:
        response.close()


def calculate_standing(symbol, snapshot):
    """Find an unambiguous US equity and its covered-universe rank."""
    exchange, _, ticker = symbol.partition(":")

    if exchange not in {"NASDAQ", "NYSE", "AMEX"}:
        return None

    records = [
        r for r in snapshot["records"]
        if isinstance(r, dict)
        and r.get("assetClass") == "equity"
        and valid_cap(r.get("marketCapUsd"))
    ]

    matches = [
        r for r in records
        if str(r.get("ticker", "")).upper() == ticker
        and str(r.get("country", "")).upper() == "US"
    ]

    if len(matches) != 1:
        return None

    selected = matches[0]
    ordered = sorted(
        records,
        key=lambda r: r["marketCapUsd"],
        reverse=True,
    )

    position = next(
        i for i, r in enumerate(ordered, 1)
        if r is selected
    )

    return selected, position, len(ordered)


def render_perp_market_size(symbol):
    """Present attributed figures without claiming a global ranking."""
    if symbol in {"AMEX:SPY", "SP:SPX"}:
        return

    exchange = symbol.partition(":")[0]
    if exchange not in {"NASDAQ", "NYSE", "AMEX"}:
        return

    st.markdown("#### Market size & standing")

    try:
        snapshot = market_universe()
    except (requests.RequestException, ValueError, TypeError):
        st.caption(
            "Market-size data is temporarily unavailable. "
            "Other stock research remains available."
        )
        return

    result = calculate_standing(symbol, snapshot)

    if result is None:
        st.caption(
            "This stock does not have an unambiguous market-cap "
            "record in the current PerpEquities coverage. "
            "No ranking has been estimated."
        )
        return

    record, position, count = result
    cap = record["marketCapUsd"]

    a, b, c = st.columns(3)

    a.metric(
        "Market capitalization",
        compact(cap, "USD"),
    )
    b.metric(
        "Company size",
        size_category(cap, "USD"),
    )
    c.metric(
        "Rank among covered equities",
        f"#{position}" if snapshot["complete"] else "Unavailable",
        help=(
            "Rank by reported USD market capitalization among "
            "covered equities with available figures. "
            "Not a global public-company ranking."
        ),
    )

    generated = snapshot.get("generated")
    timestamp_label = "Snapshot time unavailable"

    if isinstance(generated, str):
        try:
            dt = datetime.fromisoformat(
                generated.replace("Z", "+00:00")
            )
            if dt.tzinfo is not None:
                timestamp_label = (
                    "Snapshot: "
                    + dt.astimezone(UTC).strftime(
                        "%Y-%m-%d %H:%M UTC"
                    )
                )
        except ValueError:
            pass

    if snapshot["stale"]:
        st.warning("The provider marks this snapshot as stale.")

    st.caption(
        f"{timestamp_label} · "
        f"{count:,} covered equities with reported market caps · "
        "This is not a worldwide ranking. "
        "Individual market-cap reference dates are not provided."
    )

    st.markdown(
        "Data: [PerpEquities](https://perpequities.com) · "
        "[Coverage and methodology](https://perpequities.com/data)"
    )
