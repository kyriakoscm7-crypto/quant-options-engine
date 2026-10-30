"""Historical market activity preview for Quant Discovery."""

import pandas as pd
import streamlit as st

from app.market_data.activity_flags import (
    GAP_Z_THRESHOLD,
    RELATIVE_VOLUME_THRESHOLD,
    classify_activity,
)
from app.market_data.stock_ranking import rank_stocks
from dashboard.market_event_investigator import render_market_event_investigator
from dashboard.market_scanner_page import cached_market_scan


def render_market_activity(
    ranked_tickers: tuple[str, ...],
    selected_ticker: str,
) -> None:
    """Show a small, on-demand historical market activity scan."""

    st.divider()

    st.subheader(
        ":primary[:material/monitoring:] "
        "Market Activity Intelligence"
    )

    st.caption(
        "Investigate historical opening gaps and unusual "
        "trading volume in the selected company and other "
        "highly ranked research candidates."
    )

    symbols = tuple(
        dict.fromkeys(
            (selected_ticker, *ranked_tickers)
        )
    )

    st.caption(
        f"Research universe: {len(symbols)} companies. "
        "The scan uses one year of available daily history."
    )

    if st.button(
        "Analyze Market Activity",
        icon=":material/analytics:",
        type="primary",
        key="qi_activity_scan_button",
    ):
        with st.spinner("Analyzing historical market activity..."):
            try:
                scan_results = cached_market_scan(
                    symbols,
                    "1y",
                )
                ranked_scan = rank_stocks(scan_results)

            except (ValueError, RuntimeError) as exc:
                st.error(f"Market activity scan failed: {exc}")
                return

        st.session_state["qi_discover_activity_result"] = {
            "symbols": symbols,
            "data": ranked_scan,
        }

    saved = st.session_state.get(
        "qi_discover_activity_result"
    )

    if saved is None or saved["symbols"] != symbols:
        st.info(
            "Run the activity scan to inspect historical "
            "price gaps, volume anomalies, and signal dates."
        )
        return

    results = saved["data"]

    columns = [
        "Ticker",
        "Opening Gap (%)",
        "Relative Volume",
        "Gap Z-Score",
        "Gap Signal Date",
        "Gap Status",
    ]

    missing = [
        column
        for column in columns
        if column not in results.columns
    ]

    if missing:
        st.warning(
            "The scanner did not return all required "
            "market activity measurements."
        )
        return

    activity = results.loc[:, columns].copy()

    valid = activity[
        activity["Gap Status"] == "OK"
    ].copy()

    left, right = st.columns(2)

    left.metric(
        "Companies Screened",
        len(activity),
    )

    right.metric(
        "Valid Activity Observations",
        len(valid),
    )

    if valid.empty:
        st.warning(
            "No eligible gap signals were available for "
            "this research universe."
        )
        return

    for column in (
        "Opening Gap (%)",
        "Relative Volume",
        "Gap Z-Score",
    ):
        valid[column] = pd.to_numeric(
            valid[column],
            errors="coerce",
        )

    valid = valid.sort_values(
        "Relative Volume",
        ascending=False,
        na_position="last",
    )

    # Apply the same tested screening rules to each observation.
    valid["Activity Reasons"] = [
        classify_activity(gap_z, volume)
        for gap_z, volume in zip(
            valid["Gap Z-Score"],
            valid["Relative Volume"],
            strict=True,
        )
    ]

    flagged = valid.loc[
        valid["Activity Reasons"].map(bool)
    ].copy()

    st.markdown(
        "#### :primary[:material/radar:] Activity Flags"
    )

    st.caption(
        f"Exploratory thresholds: absolute gap Z-score "
        f"of at least {GAP_Z_THRESHOLD:.1f}, or relative "
        f"trading volume of at least "
        f"{RELATIVE_VOLUME_THRESHOLD:.1f} times its "
        "reference level."
    )

    if flagged.empty:
        st.info(
            "No companies meet the current activity "
            "thresholds. Valid historical observations "
            "are shown below."
        )
    else:
        st.markdown(
            f"**{len(flagged)} of {len(valid)} companies** "
            "meet at least one screening threshold."
        )

        for _, observation in flagged.iterrows():
            st.markdown(
                f"**{observation['Ticker']}**: "
                + ", ".join(observation["Activity Reasons"])
                + f" | {observation['Gap Signal Date']}"
            )

    st.markdown("#### Latest Historical Observations")

    st.dataframe(
        valid[
            [
                "Ticker",
                "Opening Gap (%)",
                "Relative Volume",
                "Gap Z-Score",
                "Gap Signal Date",
            ]
        ],
        hide_index=True,
        width="stretch",
        column_config={
            "Ticker": st.column_config.TextColumn(
                "Ticker",
                width="small",
            ),
            "Opening Gap (%)": st.column_config.NumberColumn(
                "Opening Gap",
                format="%+.2f%%",
            ),
            "Relative Volume": st.column_config.NumberColumn(
                "Relative Volume",
                format="%.2fx",
            ),
            "Gap Z-Score": st.column_config.NumberColumn(
                "Gap Z-Score",
                format="%.2f",
            ),
        },
    )

    unavailable = len(activity) - len(valid)

    if unavailable:
        st.caption(
            f"Activity measurements were unavailable "
            f"for {unavailable} screened companies."
        )

    st.caption(
        "Measurements describe historical market activity "
        "at each ticker's reported signal date. They are "
        "not real-time alerts, causal explanations, "
        "or validated return predictions."
    )

    render_market_event_investigator(
        valid=valid,
        flagged=flagged,
    )
