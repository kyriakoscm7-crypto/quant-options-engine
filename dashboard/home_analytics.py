"""Interactive quantitative analytics homepage preview."""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from app.pricing.vectorized_black_scholes import (
    price_options_vectorized,
)


def render_options_preview() -> None:
    """Display a real, interactive BSM pricing visualization."""

    st.markdown("### Quantitative Model Explorer")
    st.caption(
        "Explore how theoretical European option values "
        "respond to changes in stock price and volatility."
    )

    chart_col, control_col = st.columns(
        [1.7, 1], gap="large"
    )

    with control_col:
        st.markdown("#### Model Parameters")

        volatility = st.slider(
            "Annualized volatility (%)",
            min_value=10,
            max_value=80,
            value=25,
            step=5,
            key="home_model_volatility",
        )

        st.caption(
            "Strike: $100 | Expiry: 30 days | "
            "Risk-free rate: 4% | Dividend yield: 0%"
        )

    stock_prices = np.linspace(60.0, 140.0, 161)

    calls, puts = price_options_vectorized(
        S=stock_prices,
        K=100.0,
        T=30.0 / 365.0,
        r=0.04,
        sigma=volatility / 100.0,
        q=0.0,
    )

    with control_col:
        midpoint = 80

        st.metric(
            "Call value at $100",
            f"${calls[midpoint]:.2f}",
        )

        st.metric(
            "Put value at $100",
            f"${puts[midpoint]:.2f}",
        )

        st.caption(
            "Hypothetical Black–Scholes–Merton "
            "valuations, not market quotes or forecasts."
        )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=stock_prices,
            y=calls,
            name="Call Option",
            mode="lines",
            line=dict(color="#FF78B7", width=3),
            hovertemplate=(
                "Stock: $%{x:.2f}<br>"
                "Call: $%{y:.2f}<extra></extra>"
            ),
        )
    )

    figure.add_trace(
        go.Scatter(
            x=stock_prices,
            y=puts,
            name="Put Option",
            mode="lines",
            line=dict(color="#8EA8FF", width=3),
            hovertemplate=(
                "Stock: $%{x:.2f}<br>"
                "Put: $%{y:.2f}<extra></extra>"
            ),
        )
    )

    figure.add_vline(
        x=100,
        line_dash="dot",
        line_color="#63718E",
    )

    figure.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111B30",
        plot_bgcolor="#111B30",
        font=dict(color="#DCE5F6"),
        height=355,
        margin=dict(l=15, r=15, t=25, b=15),
        xaxis_title="Underlying Stock Price ($)",
        yaxis_title="Theoretical Option Value ($)",
        legend=dict(
            orientation="h",
            y=1.16,
            x=0,
        ),
        hovermode="x unified",
    )

    figure.update_xaxes(gridcolor="#26344F")
    figure.update_yaxes(gridcolor="#26344F")

    with chart_col:
        st.plotly_chart(
            figure,
            use_container_width=True,
            key="home_options_preview_chart",
        )
