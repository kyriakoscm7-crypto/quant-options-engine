"""Investigate historical market events with price and volume charts."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from app.market_data.stock_history import fetch_stock_history
from dashboard.company_catalyst_panel import render_event_news


@st.cache_data(ttl=900, show_spinner=False)
def cached_event_history(ticker: str) -> pd.DataFrame:
    return fetch_stock_history(ticker, period="1y")


def render_market_event_investigator(
    valid: pd.DataFrame,
    flagged: pd.DataFrame,
) -> None:
    """Investigate eligible historical gap and volume observations."""

    st.divider()

    st.subheader(
        ":primary[:material/candlestick_chart:] "
        "Market Event Investigator"
    )

    st.caption(
        "Select a company to examine the historical "
        "price and volume data surrounding its reported event."
    )

    candidates = flagged if not flagged.empty else valid

    tickers = candidates["Ticker"].astype(str).tolist()

    selected_ticker = st.selectbox(
        "Company to Investigate",
        options=tickers,
        key="qi_event_investigator_ticker",
    )

    observation = candidates.loc[
        candidates["Ticker"].astype(str) == selected_ticker
    ].iloc[0]

    event_date = str(observation["Gap Signal Date"])[:10]

    a, b, c = st.columns(3)

    a.metric(
        "Opening Gap",
        f"{float(observation['Opening Gap (%)']):+.2f}%",
    )

    b.metric(
        "Relative Volume",
        f"{float(observation['Relative Volume']):.2f}x",
    )

    c.metric(
        "Gap Z-Score",
        f"{float(observation['Gap Z-Score']):+.2f}",
    )

    st.caption(f"Reported event date: {event_date}")

    if st.button(
        "Investigate Selected Event",
        icon=":material/query_stats:",
        type="primary",
        key="qi_load_event_chart",
    ):
        with st.spinner(
            f"Loading historical data for {selected_ticker}..."
        ):
            try:
                history = cached_event_history(selected_ticker)
            except (ValueError, RuntimeError) as exc:
                st.error(f"Historical data unavailable: {exc}")
                return

        st.session_state["qi_event_chart_data"] = {
            "ticker": selected_ticker,
            "event_date": event_date,
            "history": history,
        }

    saved = st.session_state.get("qi_event_chart_data")

    if (
        saved is None
        or saved["ticker"] != selected_ticker
        or saved["event_date"] != event_date
    ):
        st.info(
            "Click Investigate Selected Event to load "
            "the company's historical price and volume charts."
        )
        return

    history = saved["history"].copy()

    history["Date"] = pd.to_datetime(
        history["Date"],
        utc=True,
    )

    history = history.sort_values("Date").reset_index(drop=True)

    event_day = pd.to_datetime(
        event_date,
        errors="coerce",
    )

    if pd.isna(event_day):
        st.warning("The reported event date is invalid.")
        return

    event_day = event_day.date()

    session_days = history["Date"].dt.date

    matches = history.index[
        session_days == event_day
    ].tolist()

    if not matches:
        st.warning(
            "The reported event date could not be matched "
            "to the retrieved historical price data. "
            "The market-data snapshot may have changed."
        )
        return

    event_index = matches[-1]

    start = max(0, event_index - 50)
    end = min(len(history), event_index + 11)

    window = history.iloc[start:end].copy()

    dates = window["Date"].dt.strftime("%Y-%m-%d")

    volume_colors = [
        "#FF78B7" if day == event_date else "#6680AB"
        for day in dates
    ]

    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.72, 0.28],
        subplot_titles=("Adjusted OHLC Prices", "Trading Volume"),
    )

    figure.add_trace(
        go.Candlestick(
            x=dates,
            open=window["Open"],
            high=window["High"],
            low=window["Low"],
            close=window["Close"],
            name="Price",
            increasing_line_color="#FF78B7",
            decreasing_line_color="#8EA8FF",
        ),
        row=1,
        col=1,
    )

    figure.add_trace(
        go.Bar(
            x=dates,
            y=window["Volume"],
            name="Volume",
            marker_color=volume_colors,
            hovertemplate=(
                "Date: %{x}<br>"
                "Volume: %{y:,.0f}<extra></extra>"
            ),
        ),
        row=2,
        col=1,
    )

    figure.add_vline(
        x=event_date,
        line_color="#FF78B7",
        line_dash="dash",
        line_width=1.5,
        row="all",
        col=1,
    )

    prior_volume = history["Volume"].iloc[
        max(0, event_index - 20):event_index
    ]

    if len(prior_volume) >= 5:
        baseline = float(prior_volume.mean())

        if baseline > 0:
            figure.add_hline(
                y=baseline,
                line_color="#A8B9D4",
                line_dash="dot",
                line_width=1,
                row=2,
                col=1,
            )

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="#101B30",
        plot_bgcolor="#101B30",
        font=dict(color="#DCE5F5"),
        height=620,
        margin=dict(l=15, r=15, t=65, b=20),
        showlegend=False,
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        dragmode="zoom",
    )

    tick_dates = list(dict.fromkeys(
        [*dates.iloc[::7].tolist(), event_date]
    ))

    figure.update_xaxes(
        type="category",
        gridcolor="#263650",
        showgrid=True,
        tickmode="array",
        tickvals=tick_dates,
        ticktext=[
            pd.Timestamp(value).strftime("%b %d")
            for value in tick_dates
        ],
        tickangle=0,
    )

    figure.update_yaxes(
        gridcolor="#263650",
        zeroline=False,
    )

    figure.update_yaxes(
        title_text="Price ($)",
        row=1,
        col=1,
    )

    figure.update_yaxes(
        title_text="Shares",
        row=2,
        col=1,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
        key="qi_market_event_investigator_chart",
    )

    st.caption(
        "The pink dashed line marks the reported event "
        "session. Pink volume bars identify that session. "
        "The dotted volume baseline uses up to 20 "
        "preceding sessions."
    )

    st.caption(
        "Historical OHLC prices use corporate-action-adjusted "
        "market data. The chart is descriptive, and the "
        "flag does not establish the cause of the activity "
        "or predict future returns."
    )

    render_event_news(selected_ticker, event_date)

    if st.button(
        "Open Full Stock Research",
        icon=":material/open_in_new:",
        key="qi_event_open_full_research",
    ):
        st.session_state["_research_ticker_request"] = selected_ticker
        st.session_state["_navigation_request"] = "🔎 Stock Explorer"
        st.rerun()
