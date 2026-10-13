"""Beginner-friendly forecasting research dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

RESULTS_PATH = (
    Path(__file__).resolve().parent.parent
    / "research_results"
    / "milestone_11_8"
    / "combined_feature_experiments.csv"
)

STOCK_NAMES = {
    "AAPL": "Apple",
    "MSFT": "Microsoft",
    "NVDA": "NVIDIA",
}

HORIZON_NAMES = {
    1: "Tomorrow (1 trading day)",
    5: "Next week (5 trading days)",
    20: "Next month (20 trading days)",
    60: "Next 3 months (60 trading days)",
}


def render_forecast_intelligence():
    """Display understandable conclusions before technical research."""

    st.title("🧠 Forecast Intelligence")

    st.markdown(
        "### Can artificial intelligence predict stock movements?"
    )

    st.info(
        "**Our research hasn't shown reliable predictive ability yet.** "
        "We tested multiple machine-learning approaches using historical "
        "stock prices. So far, simpler historical estimates have generally "
        "performed better."
    )

    st.markdown(
        "This page lets you explore what we discovered. "
        "**It does not predict what a stock will do tomorrow.**"
    )

    if not RESULTS_PATH.exists():
        st.warning(
            "The research results aren't available on this computer yet."
        )
        return

    try:
        results = pd.read_csv(RESULTS_PATH)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        st.error(f"Couldn't load the research results: {exc}")
        return

    required = {
        "Ticker",
        "Configuration",
        "Horizon",
        "N",
        "Brier",
        "Historical Brier",
        "Brier Improvement",
        "ROC AUC",
        "Calibration Error",
        "Features",
        "C",
    }

    if results.empty or not required.issubset(results.columns):
        st.error("The research file is incomplete.")
        return

    st.divider()

    st.subheader("🔎 Explore a Stock")

    col1, col2 = st.columns(2)

    with col1:
        ticker = st.selectbox(
            "Which company?",
            sorted(results["Ticker"].dropna().unique()),
            format_func=lambda value: (
                f"{STOCK_NAMES.get(value, value)} ({value})"
            ),
        )

    with col2:
        horizons = sorted(
            int(value)
            for value in results["Horizon"].dropna().unique()
        )

        horizon = st.selectbox(
            "How far ahead were we testing?",
            horizons,
            format_func=lambda value: HORIZON_NAMES.get(
                value, f"{value} trading days"
            ),
        )

    filtered = results.loc[
        (results["Ticker"] == ticker)
        & (results["Horizon"] == horizon)
    ].copy()

    if filtered.empty:
        st.warning("No research results for this selection.")
        return

    filtered = filtered.sort_values("Brier")

    best = filtered.iloc[0]

    ml_score = float(best["Brier"])
    historical_score = float(best["Historical Brier"])

    company = STOCK_NAMES.get(ticker, ticker)

    st.divider()

    st.subheader(f"📊 What Did We Discover About {company}?")

    if ml_score < historical_score:
        st.success(
            "**The best AI model performed slightly better "
            "than the historical estimate in this experiment.**"
        )
    elif ml_score > historical_score:
        st.warning(
            "**The simpler historical estimate performed better "
            "than our best AI model in this experiment.**"
        )
    else:
        st.info(
            "**The best AI model and historical estimate "
            "performed equally in this experiment.**"
        )

    st.markdown(
        "**What does that mean?**\n\n"
        "We compared how closely different methods predicted "
        "historical up-or-down outcomes. "
        "A more complicated model isn't automatically more accurate."
    )

    st.caption(
        "These comparisons use chronological predictions within "
        "the training period. They are research findings, not "
        "independent proof of future forecasting performance."
    )

    st.markdown("### 🏆 Which Approach Worked Better?")

    if historical_score < ml_score:
        st.success("**Winner: Simple Historical Estimates**")
        st.write(
            "The simpler approach produced more accurate probability "
            "estimates than our best experimental AI model in this "
            "historical comparison."
        )
    elif ml_score < historical_score:
        st.success("**Winner: Experimental AI Model**")
        st.write(
            "Our best experimental AI model produced more accurate "
            "probability estimates than the historical approach "
            "in this particular comparison."
        )
    else:
        st.info("**Result: Both Approaches Performed Equally**")
        st.write(
            "The two approaches produced the same average "
            "probability error in this comparison."
        )

    st.caption(
        "This compares past research results. It does not tell us "
        "which method will perform better in the future."
    )

    st.divider()

    st.subheader("💡 The Bigger Picture")

    st.markdown(
        "Our experiments suggest that **adding machine learning "
        "doesn't automatically improve financial forecasts**. "
        "Before using a forecasting model for investment decisions, "
        "we need convincing evidence that it works on genuinely "
        "unseen data."
    )

    with st.expander("🔬 Advanced Research Details"):
        st.markdown("### Model Comparison")

        chart_data = filtered[
            ["Configuration", "Brier", "Historical Brier"]
        ].melt(
            id_vars="Configuration",
            var_name="Method",
            value_name="Prediction Error",
        )

        figure = px.bar(
            chart_data,
            x="Configuration",
            y="Prediction Error",
            color="Method",
            barmode="group",
            title=f"{company}: {horizon}-Day Research Comparison",
        )

        st.plotly_chart(figure, width="stretch")

        st.markdown("### Model Reliability")

        reliability = px.scatter(
            filtered,
            x="Calibration Error",
            y="ROC AUC",
            size="N",
            color="Configuration",
            hover_data=["Brier", "Brier Improvement"],
            title="Calibration Error vs. ROC AUC",
        )

        st.plotly_chart(reliability, width="stretch")

        st.markdown("### Detailed Results")

        st.dataframe(
            filtered[
                [
                    "Configuration",
                    "Features",
                    "C",
                    "N",
                    "Brier",
                    "Historical Brier",
                    "Brier Improvement",
                    "ROC AUC",
                    "Calibration Error",
                ]
            ].round(4),
            width="stretch",
            hide_index=True,
        )

        st.markdown(
            "**Brier Score:** Measures probability prediction error. "
            "Lower is better.\n\n"
            "**ROC AUC:** Measures how well a model separates rising "
            "and falling outcomes. Around 0.5 suggests little "
            "discrimination.\n\n"
            "**Calibration Error:** Measures how closely predicted "
            "probabilities match observed frequencies. Lower is better."
        )

        st.caption(
            "All displayed results come from training-period "
            "walk-forward experiments, not the reserved test period."
        )

    st.caption(
        "Quant Intelligence is a research and educational platform. "
        "Nothing displayed here is personalized investment advice."
    )
