"""Source-linked company news around a selected market activity event."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import streamlit as st

from app.intelligence.catalyst_engine import analyze_headline
from app.intelligence.event_news import news_near_event
from app.intelligence.news_engine import fetch_company_news


@st.cache_data(ttl=900, show_spinner=False)
def _cached_event_news(ticker: str) -> list[dict]:
    return fetch_company_news(ticker, days=30, limit=100)


def render_event_news(ticker: str, event_date: str) -> None:
    """Present recent source-linked articles without implying causation."""
    st.markdown("---")
    st.markdown(
        "### :primary[:material/newspaper:] Catalyst Intelligence"
    )
    st.caption(
        "Explore published news around the selected market event. "
        "Matching dates or keywords does not establish causation."
    )

    try:
        day = datetime.fromisoformat(str(event_date)[:10]).date()
    except ValueError:
        st.warning("The event date could not be interpreted.")
        return

    today = datetime.now(UTC).astimezone(
        ZoneInfo("America/New_York")
    ).date()
    event_age = (today - day).days

    if event_age < 0:
        st.info("This event is dated in the future.")
        return

    if event_age >= 30:
        st.info(
            "This event falls outside the existing 30-day news "
            "retrieval window. Historical news is not available "
            "through this source."
        )
        return

    st.caption(
        f"Event: {ticker} | {day.isoformat()} | "
        "News source: Google News RSS"
    )

    request_key = f"{ticker}:{day.isoformat()}"

    if st.button(
        "Find News Around Event",
        icon=":material/search:",
        key="qi_event_search_news",
    ):
        try:
            with st.spinner("Searching published company news..."):
                articles = _cached_event_news(ticker)
                matched = news_near_event(articles, day)
        except Exception as exc:
            st.warning(f"Company news is temporarily unavailable: {exc}")
        else:
            st.session_state["qi_event_news_results"] = {
                "request_key": request_key,
                "articles": matched,
            }

    saved = st.session_state.get("qi_event_news_results")

    if not saved or saved.get("request_key") != request_key:
        return

    articles = saved["articles"]

    if not articles:
        st.info(
            "No matching articles were returned for the event window. "
            "This does not mean no news or disclosures existed."
        )
        return

    st.markdown(f"**{len(articles)} dated articles found**")

    for article in articles[:12]:
        title = str(article.get("title") or "Untitled article")
        publisher = str(article.get("publisher") or "Unknown publisher")

        st.markdown(f"**{title}**")
        st.caption(
            f"{publisher} | {article['published_eastern']} | "
            f"{article['event_timing']}"
        )

        catalysts = analyze_headline(title)
        if catalysts:
            labels = ", ".join(item.label for item in catalysts)
            st.caption(f"Headline keyword classifications: {labels}")

        st.link_button(
            "Read Original Source",
            article["url"],
            icon=":material/open_in_new:",
        )
        st.divider()

    st.caption(
        "Coverage is limited to recent indexed news returned by "
        "the provider. Ticker searches can include unrelated articles; "
        "verify the company and publication time at the original source. "
        "This panel does not affect investment rankings or predictions."
    )
