"""Company identity and SEC-powered financial briefing."""

import streamlit as st

from dashboard.company_financial_intelligence import (
    render_financial_intelligence,
)
from dashboard.news_events_panel import _services


def render_company_briefing(symbol: str) -> None:
    ticker = symbol.rsplit(":", 1)[-1].replace(".", "-")

    directory, _ = _services()
    snapshot = directory.get()

    if snapshot.registry is None:
        st.info("Official company research is temporarily unavailable.")
        return

    try:
        company = snapshot.registry.resolve_ticker(ticker)
    except ValueError:
        st.warning("Multiple company identities match this ticker.")
        return

    if company is None:
        st.info(
            "An exact SEC filing identity could not be established "
            "for this security. We will not guess."
        )
        return

    render_financial_intelligence(company)
