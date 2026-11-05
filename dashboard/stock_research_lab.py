"""Integrated research UI with deliberately company-independent assumptions."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.intelligence.explorer_lab import portfolio_path, research_paths
from app.intelligence.risk_engine import calculate_risk_metrics


def _chart(frame, title):
    fig = go.Figure()
    for i, name in enumerate(frame.columns):
        fig.add_scatter(x=frame.index, y=frame[name], name=name,
                        line=dict(color=["#FF78B7", "#91B4F4", "#FFFFFF"][i % 3], width=2))
    fig.update_layout(title=title, template="plotly_dark", height=330,
                      paper_bgcolor="#080D1D", plot_bgcolor="#0D1424",
                      margin=dict(l=15, r=15, t=45, b=20),
                      legend=dict(orientation="h", y=1.15), hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)


def render_research_lab():
    st.markdown("## Quantitative workbench")
    st.caption("ASSUMPTION-DRIVEN MODEL · Independent of the reference company. No market data is imported; these results are not company forecasts, quotes or recommendations.")
    with st.expander("Model assumptions · adjust your experiment", expanded=True):
        a, b = st.columns(2)
        drift = a.slider("Model A annual growth assumption (%)", -40, 40, 8, key="lab_drift") / 100
        vol = b.slider("Model A annual volatility (%)", 5, 80, 25, key="lab_vol") / 100
        corr = a.slider("Assumed shock correlation with Model B", -1.0, 1.0, 0.6, 0.05, key="lab_corr")
        seed = b.number_input("Reproducible experiment seed", 0, 10000, 17, key="lab_seed")
        st.caption("253 generated daily observations, index starts at 100. Model B: 6% growth, 16% volatility. Geometric Brownian paths; no company data. Risk-free rate: 0% for path statistics.")
    paths = research_paths(drift, vol, corr, int(seed))
    dates = pd.bdate_range("2000-01-03", periods=len(paths))
    def history(name):
        return pd.DataFrame({"Date": dates, "Close": paths[name].to_numpy()})
    risk = calculate_risk_metrics(history("Model A"), history("Model B"))
    columns = st.columns(4)
    for column, label, value in zip(columns,
            ["Model A realized return", "Model A volatility", "Model A max drawdown", "Model A Sharpe · rf 0%"],
            [f"{(paths.iloc[-1, 0] / 100 - 1):.1%}", f"{risk['annualized_volatility_pct']:.1f}%",
             f"{risk['maximum_drawdown_pct']:.1f}%", f"{risk['sharpe_ratio']:.2f}"]):
        column.metric(label, value)
    performance, exposure, options, research = st.tabs(["Performance & comparison", "Risk & portfolio", "Options & Greeks", "Research desk"])
    with performance:
        _chart(paths, "Generated scenarios · indexed growth / observation number")
        st.caption("One generated realization, not an expected outcome. Changing the selected company never changes these paths.")
        st.dataframe(paths.describe().T[["min", "max", "mean"]].rename(columns={"mean": "Average index"}), use_container_width=True)
        st.download_button("Download generated model paths · CSV", paths.to_csv(index_label="Observation"), "fictional-model-paths.csv", "text/csv")
    with exposure:
        weight = st.slider("Buy-and-hold allocation to Model A (%)", 0, 100, 60) / 100
        blend = portfolio_path(paths, weight)
        drawdowns = paths.div(paths.cummax()).sub(1).mul(100)
        _chart(drawdowns, "Model drawdowns (%) / observation number")
        _chart(pd.DataFrame({"Model A": paths.iloc[:, 0], "Model B": paths.iloc[:, 1], "Blend": blend}), "Buy-and-hold comparison · index")
        st.write(f"Realized model beta vs Model B: **{risk['beta_vs_spy']:.2f}** · correlation: **{risk['correlation_vs_spy']:.2f}**")
        shock = st.slider("Manual instantaneous shock to Model A (%)", -60, 60, -20) / 100
        shock_b = st.slider("Manual instantaneous shock to Model B (%)", -60, 60, -10) / 100
        st.metric("Hypothetical allocation shock", f"{weight * shock + (1-weight) * shock_b:.1%}")
        st.caption("Blend assumes initial weights and no rebalancing, fees or dividends. Shock uses initial weights; beta and correlation describe this generated sample only.")
    with options:
        st.write("Continue in the shared Options workspace to price options and investigate Greeks with the same saved assumptions.")
        if st.button("Open Options workspace", key="qi_simulation_options"):
            st.session_state["_navigation_request"] = "💰 Options Lab"
            st.rerun()
    with research:
        st.markdown("### From observation to experiment")
        st.write("Use the market chart to explore a question, then test assumptions here. Lower volatility, vary correlation or change allocation and compare outcomes. No synthetic score is assigned to the selected company.")
        st.link_button("Company filings · SEC EDGAR ↗", "https://www.sec.gov/edgar/search/")
        st.link_button("Company coverage on TradingView ↗", "https://www.tradingview.com/symbols/")
        st.caption("External research destinations, not an ingested news feed. Verify issuer identity, dates and sources at the destination.")
        st.markdown("**Available now:** provider-hosted market chart, generated risk/comparison analysis, manual portfolio shocks and European option pricing. **Requires separate data rights:** automatic stock KPIs, company scoring, price-derived forecasts, historical downloads and republished news.")
