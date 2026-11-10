"""Interactive, simulation-only volatility education for any selected symbol."""
from html import escape

import streamlit as st
import plotly.graph_objects as go

from app.visualization.historical_volatility import (
    historical_volatility_from_csv,
    latest_hv,
)

from app.visualization.volatility_simulation import (
    EXPIRIES,
    simulated_slice,
    simulation_figure,
)


def _render_simulation_lab(symbol: str) -> None:
    with st.container(border=True):
        st.markdown(
            f"""<div style="background:linear-gradient(115deg,#111A31,#29203C 70%,#42233B);
padding:18px 22px;border-radius:13px;border-top:2px solid #FF78B7">
<div style="color:#FF9ACA;font-size:11px;font-weight:700;letter-spacing:1.8px">
VOLATILITY INTELLIGENCE · EDUCATIONAL SIMULATION</div>
<h3 style="margin:8px 0 6px;color:white;font-size:24px">See how volatility changes across strikes and time</h3>
<p style="margin:0;color:#CCD8EB;font-size:13px">Research context: {escape(symbol)} ·
Hypothetical assumptions, not data from this security.</p></div>""",
            unsafe_allow_html=True,
        )

        st.caption(
            "**SIMULATION — NOT LIVE IMPLIED VOLATILITY.** All tickers use the same "
            "illustrative model. No option quotes are fetched or estimated."
        )

        view = st.radio(
            "Explore the model",
            ["Volatility curve", "3D surface", "2D heatmap"],
            horizontal=True, key="qi_vol_view",
            help="Start with a volatility curve for a clear comparison. Rotate the optional 3D chart.",
        )
        expiry = st.selectbox(
            "Time until expiration",
            EXPIRIES, index=1,
            format_func=lambda d: f"{d} days",
            key="qi_vol_expiry",
            help="Select the hypothetical expiry to inspect in the curve or heatmap.",
        )

        with st.expander("Adjust the hypothetical assumptions"):
            a, b = st.columns(2)
            with a:
                level = st.slider(
                    "Baseline volatility (%)", 5, 100, 30, key="qi_vol_level",
                    help="Annualized modeled volatility at reference strike and 30 days.",
                )
                skew = st.slider(
                    "Downside skew", -30, 30, 12, key="qi_vol_skew",
                    help="Positive skew lifts volatility for lower strikes.",
                )
            with b:
                curvature = st.slider(
                    "Smile curvature", 0, 60, 20, key="qi_vol_curve",
                    help="Curvature raises modeled volatility away from the reference strike.",
                )
                term = st.slider(
                    "Expiry slope", -15, 15, 5, key="qi_vol_term",
                    help="Positive values raise modeled volatility for longer expiries.",
                )
            def restore_example():
                for key, value in (
                    ("qi_vol_level", 30), ("qi_vol_skew", 12),
                    ("qi_vol_curve", 20), ("qi_vol_term", 5),
                ):
                    st.session_state[key] = value

            st.button(
                "Restore example assumptions",
                key="qi_vol_defaults", on_click=restore_example,
            )
            st.caption(
                "All controls are hypothetical. No stock price or company fundamentals "
                "are used to calculate these curves."
            )

        x, values = simulated_slice(level, skew, curvature, term, expiry)
        low_iv = float(values[8])  # 0.80x strike
        at_iv = float(values[len(x) // 2])
        high_iv = float(values[-9])  # 1.20x strike
        a, b, c = st.columns(3)
        a.metric("80% strike", f"{low_iv:.1f}%")
        b.metric("Reference strike", f"{at_iv:.1f}%")
        c.metric("120% strike", f"{high_iv:.1f}%")
        st.caption(
            f"Modeled {expiry}-day annualized volatility at three strikes, "
            "not a stock forecast. Compare the values to understand skew."
        )

        if view == "3D surface":
            if st.button("Reset camera", key="qi_vol_reset"):
                st.session_state["qi_vol_camera_revision"] = (
                    st.session_state.get("qi_vol_camera_revision", 0) + 1
                )
            st.caption("Drag to rotate the 3D landscape. Zoom and pan are disabled.")
        elif view == "Volatility curve":
            st.caption(
                "**How to read it:** The pink line compares modeled implied volatility "
                f"across strike ratios at {expiry} days. The dashed vertical line is "
                "the reference strike. It is not a predicted price path."
            )
        else:
            st.caption(
                f"**How to read it:** Each color represents the modeled annualized "
                f"volatility (%) for a strike and expiry. The dashed horizontal line "
                f"marks your selected {expiry}-day slice."
            )

        st.plotly_chart(
            simulation_figure(
                level, skew, curvature, term, view,
                expiry_days=expiry,
                camera_revision=st.session_state.get("qi_vol_camera_revision", 0),
            ),
            width="stretch", key="qi_vol_chart", config={
                "displaylogo": False, "scrollZoom": False,
                "doubleClick": False, "responsive": True,
                "modeBarButtonsToRemove": [
                    "toImage", "pan3d", "zoom3d", "orbitRotation",
                    "zoomIn2d", "zoomOut2d", "autoScale2d",
                    "select2d", "lasso2d",
                ],
            },
        )

        with st.expander("What does this teach me?"):
            st.write(
                "**Skew:** lower strikes sometimes have higher IV than higher strikes. "
                "**Smile:** implied volatility can increase away from the reference "
                "strike in either direction. **Term structure:** volatility can "
                "change with time to expiration."
            )
            st.write(
                "Real implied volatility is backed out from observed option prices. "
                "These curves are invented demonstrations, not calibrated, arbitrage-free "
                "surfaces or predictions. Their height does not tell you whether a "
                "stock will rise. Real company IV would require licensed, valid quotes."
            )
            st.code(
                "vol % = clip(baseline − skew × ln(K/S) + curvature × ln(K/S)²\n"
                "             + expiry slope × ln(days / 30), 1, 200)",
                language=None,
            )


def render_volatility_intelligence(symbol: str) -> None:
    """Company-context volatility that never fabricates market measurements."""
    st.markdown("## Volatility Intelligence")
    st.caption(
        "See how much a stock has actually fluctuated, when you have daily "
        "price data. Historical volatility is not a prediction."
    )
    with st.container(border=True):
        st.markdown("### Volatility overview")
        a, b = st.columns(2)
        with a:
            st.markdown("**Historical volatility**")
            st.caption("Past price fluctuations · Calculated only from uploaded data")
        with b:
            st.markdown("**Implied volatility**")
            st.caption("Not available · Requires authorized options quotes")
        st.info(
            "Company volatility is **not connected**. The historical price chart above "
            "is a display-only TradingView widget, not an authorized data feed. "
            "No company-specific volatility values will be invented."
        )

        with st.expander("Calculate historical volatility from your own daily prices"):
            st.write(
                "Upload **adjusted daily closing prices** for the selected symbol. "
                "The CSV must contain columns `Date` and `Close`, sorted oldest "
                "to newest, with one row per trading day. Use a source you are "
                "authorized to analyze. Data stays in this session; it is not "
                "written to Neon or sent to any external API by this feature."
            )
            selected = st.checkbox(
                f"I confirm the CSV is for {symbol} and is adjusted for stock splits",
                key="qi_hv_confirm",
            )
            uploaded = st.file_uploader(
                "Daily price CSV (maximum 2 MB)",
                type=["csv"], key="qi_hv_upload",
            )
            if uploaded is not None and selected:
                try:
                    calculated = historical_volatility_from_csv(uploaded.getvalue())
                except ValueError as exc:
                    st.error(str(exc))
                else:
                    hv20 = latest_hv(calculated, 20)
                    hv60 = latest_hv(calculated, 60)
                    a, b = st.columns(2)
                    a.metric("20-day historical volatility", f"{hv20:.1f}%" if hv20 is not None else "—")
                    b.metric("60-day historical volatility", f"{hv60:.1f}%" if hv60 is not None else "Not enough observations")
                    first = calculated["Date"].iloc[0].strftime("%b %d, %Y")
                    last = calculated["Date"].iloc[-1].strftime("%b %d, %Y")
                    st.caption(
                        f"Uploaded data: {first} – {last}, {len(calculated)} trading sessions. "
                        "Annualized standard deviation of daily log returns × √252. "
                        "Results depend on the accuracy and freshness of the uploaded prices."
                    )
                    figure = go.Figure()
                    for key, name, color in (
                        ("HV20", "20-day realized volatility", "#FF78B7"),
                        ("HV60", "60-day realized volatility", "#79B8FF"),
                    ):
                        if calculated[key].notna().any():
                            figure.add_trace(go.Scatter(
                                x=calculated["Date"], y=calculated[key],
                                mode="lines", name=name,
                                line={"color": color, "width": 3},
                                hovertemplate="%{x|%Y-%m-%d}<br>%{y:.1f}%<extra>%{fullData.name}</extra>",
                            ))
                    figure.update_layout(
                        template="plotly_dark", paper_bgcolor="#0B1226",
                        plot_bgcolor="#0B1226", height=340,
                        margin={"l": 35, "r": 15, "t": 20, "b": 35},
                        xaxis_title="Trading date",
                        yaxis_title="Annualized historical volatility (%)",
                        legend={"orientation": "h", "y": 1.12},
                    )
                    st.plotly_chart(figure, width="stretch", key="qi_hv_chart")
                    st.caption(
                        "**Interpretation:** Higher values mean larger past daily price "
                        "changes, not that the share price will go up. This is "
                        "**historical** volatility, not options-implied volatility."
                    )
            elif uploaded is not None:
                st.warning("Confirm the symbol and adjustment before calculating.")

        st.divider()
        st.markdown("**Want to explore how options volatility shapes work?**")
        st.caption(
            "Optional educational demonstration — its numbers are invented "
            "and never represent the selected company's real volatility."
        )
        if st.toggle(
            "Open educational volatility simulation",
            key="qi_vol_lab_enabled",
            value=False,
        ):
            _render_simulation_lab(symbol)
