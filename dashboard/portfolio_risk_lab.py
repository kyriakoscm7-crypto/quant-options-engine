"""Offline stochastic risk modeling for the fictional Portfolio Manager.

Educational assumptions only: all assets are fictional, historical moments
are estimated solely from synthetic data, no real exchange data is fetched.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def simulate_portfolio_distribution(
    prices: pd.DataFrame,
    quantities: dict[str, int | float],
    *,
    sessions: int = 30,
    paths: int = 1200,
    seed: int = 20261103,
) -> dict:
    """Simulate constant-weight rebalanced wealth using multivariate log returns.

    Annualized moments are intentionally not implied: each simulated time
    step corresponds to one business session of the supplied example data.
    Correlation comes from the covariance of the historical log returns.
    """
    if not 5 <= sessions <= 252:
        raise ValueError("Sessions must be between 5 and 252")
    if not 100 <= paths <= 10000:
        raise ValueError("Paths must be between 100 and 10000")
    if not isinstance(prices, pd.DataFrame) or len(prices) < 35:
        raise ValueError("Need at least 35 synthetic price observations")
    if not quantities or not set(quantities).issubset(prices.columns):
        raise ValueError("Holdings must match supplied synthetic instruments")
    if any(
        not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0
        for v in quantities.values()
    ):
        raise ValueError("Quantities must be finite and nonnegative")

    quantities = {key: value for key, value in quantities.items() if value > 0}
    if not quantities:
        raise ValueError("At least one nonzero position required")
    frame = prices[list(quantities)].astype(float)
    if not np.isfinite(frame.to_numpy()).all() or (frame <= 0).any().any():
        raise ValueError("Prices must be positive and finite")
    latest = frame.iloc[-1].to_numpy()
    counts = np.array(list(quantities.values()), dtype=float)
    contributions = counts * latest
    initial = float(contributions.sum())
    if initial <= 0:
        raise ValueError("At least one nonzero position required")
    weights = contributions / initial

    # Slice after log transform so every covariance value is a daily return.
    log_returns = np.log(frame / frame.shift(1)).dropna()
    mu = log_returns.mean().to_numpy()
    covariance = log_returns.cov().to_numpy()
    # Numerical tolerance for very small sample covariance eigenvalues.
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    covariance = (eigenvectors * np.maximum(eigenvalues, 0)) @ eigenvectors.T

    rng = np.random.default_rng(seed)
    daily_log = rng.multivariate_normal(
        mu, covariance, size=(paths, sessions), method="eigh"
    )
    daily_simple = np.expm1(daily_log)
    # Constant-weight daily rebalancing is an *assumption*, not buy-and-hold.
    portfolio_daily = np.einsum("psa,a->ps", daily_simple, weights)
    wealth = initial * np.cumprod(1 + portfolio_daily, axis=1)
    wealth = np.column_stack([np.full(paths, initial), wealth])
    if not np.isfinite(wealth).all():
        raise ValueError("Simulation generated nonfinite results")

    final_return = wealth[:, -1] / initial - 1
    q05, q50, q95 = np.quantile(final_return, [0.05, 0.5, 0.95])
    lower_tail = final_return[final_return <= q05]
    probability = float(np.mean(final_return < 0))
    denominator = 1 + 1.96**2 / paths
    center = (probability + 1.96**2 / (2 * paths)) / denominator
    half = (
        1.96
        * math.sqrt(probability * (1 - probability) / paths + 1.96**2 / (4 * paths**2))
        / denominator
    )
    return {
        "wealth": wealth,
        "initial": initial,
        "weights": dict(zip(quantities, weights.tolist())),
        "quantile5": float(q05),
        "median": float(q50),
        "quantile95": float(q95),
        "loss_probability": probability,
        "loss_probability_interval95": (
            max(0.0, center - half),
            min(1.0, center + half),
        ),
        "value_at_risk_95": float(max(0.0, -q05 * initial)),
        "expected_shortfall_95": float(max(0.0, -lower_tail.mean() * initial)),
        "mean_pairwise_correlation": mean_correlation(log_returns),
        "loss_probability_se": float(
            np.sqrt(np.mean(final_return < 0) * (1 - np.mean(final_return < 0)) / paths)
        ),
        "tail_samples": len(lower_tail),
    }


def mean_correlation(log_returns: pd.DataFrame) -> float | None:
    """Undefined if any included asset has zero sample variance."""
    if (
        len(log_returns) < 2
        or len(log_returns.columns) < 2
        or (log_returns.std() == 0).any()
    ):
        return None
    values = log_returns.corr().to_numpy()[np.triu_indices(len(log_returns.columns), 1)]
    return float(values.mean()) if np.isfinite(values).all() else None


def render_portfolio_risk_lab(
    prices: pd.DataFrame,
    quantities: dict[str, int | float],
) -> None:
    """Render visually rich reproducible simulations without data-provider calls."""
    st.markdown("### Risk Intelligence / Monte Carlo Lab")
    st.caption(
        "Model 1,200 correlated synthetic price paths using the observed "
        "behaviour of the fictional dataset. Not investment forecasts."
    )
    st.info(
        "Monte Carlo assumes daily constant-weight rebalancing. The historical chart uses static-unit buy-and-hold; these are different strategies. No fees or taxes are modeled."
    )
    seed = st.number_input(
        "Simulation seed · compare seeds for sensitivity",
        0,
        2147483647,
        20261103,
        key="qi_mc_seed",
    )
    left, right = st.columns(2)
    with left:
        horizon = st.slider(
            "Illustrative horizon (trading sessions)",
            5,
            90,
            30,
            5,
            key="qi_portfolio_mc_horizon",
        )
    with right:
        correlation_mode = st.selectbox(
            "Correlation assumption",
            ["Estimated from synthetic histories", "Independently shuffled histories"],
            key="qi_portfolio_mc_correlation",
        )

    # The independent-case toggle changes dependence assumptions while
    # maintaining every marginal asset's log-return volatility and drift.
    if correlation_mode == "Independently shuffled histories":
        # Deterministic orthogonalized illustration: generate an independent
        # sample from each asset's synthetic marginal (no provider data).
        returns = np.log(prices / prices.shift(1)).dropna()
        rng = np.random.default_rng(413)
        independent = pd.DataFrame(
            index=prices.index, columns=prices.columns, dtype=float
        )
        independent.iloc[0] = prices.iloc[0]
        for symbol in prices.columns:
            values = rng.permutation(returns[symbol].to_numpy())
            independent[symbol] = prices[symbol].iloc[0] * np.exp(
                np.r_[0.0, np.cumsum(values)]
            )
        model_prices = independent
    else:
        model_prices = prices

    result = simulate_portfolio_distribution(
        model_prices, quantities, sessions=horizon, seed=int(seed)
    )
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Median illustrative change", f"{result['median'] * 100:+.1f}%")
    k2.metric("5th percentile", f"{result['quantile5'] * 100:+.1f}%")
    k3.metric("Chance of synthetic loss", f"{result['loss_probability'] * 100:.1f}%")
    k4.metric("95% simulated VaR", f"${result['value_at_risk_95']:,.0f}")

    low_probability, high_probability = result["loss_probability_interval95"]
    st.caption(
        f"Sampling uncertainty: 95% Wilson interval for modeled loss probability {low_probability:.1%}–{high_probability:.1%} (Monte Carlo sampling only); {result['tail_samples']} tail outcomes. Compare seeds; parameter/model uncertainty is additional."
    )
    wealth = result["wealth"]
    x = np.arange(wealth.shape[1])
    low, med, high = np.quantile(wealth, [0.05, 0.5, 0.95], axis=0)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=high,
            mode="lines",
            line={"width": 0},
            name="95th percentile",
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=low,
            mode="lines",
            line={"width": 0},
            fill="tonexty",
            fillcolor="rgba(255,120,183,0.19)",
            name="5th–95th percentile range",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=med,
            mode="lines",
            line={"color": "#ff78b7", "width": 3},
            name="Median synthetic path",
        )
    )
    fig.add_hline(
        y=result["initial"],
        line_dash="dot",
        line_color="#91a1c0",
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111c2e",
        plot_bgcolor="#111c2e",
        font={"color": "#f8fafc"},
        title="Fictional portfolio / outcome distribution",
        xaxis_title="Illustrative future session",
        yaxis_title="Synthetic portfolio value ($)",
        height=395,
        margin={"l": 18, "r": 15, "t": 60, "b": 35},
    )
    st.plotly_chart(fig, use_container_width=True)

    details, assumptions = st.tabs(["Risk diagnostics", "Model assumptions"])
    with details:
        st.metric(
            "95% expected shortfall (conditional mean loss)",
            f"${result['expected_shortfall_95']:,.0f}",
        )
        st.caption(
            "VaR is the 5th-percentile modeled loss over this hypothetical "
            "horizon. Expected shortfall averages the worst 5% of modeled "
            "outcomes; neither is a bound on potential real losses."
        )
    with assumptions:
        st.markdown(
            "The simulation estimates per-session mean and covariance "
            "from fictional log returns and draws a multivariate normal "
            "distribution. The portfolio is assumed rebalanced daily "
            "to current example value weights. The independent-shuffle "
            "option independently shuffles each fictional asset's returns. "
            "No taxes, trading costs, liquidity effects, regime changes, "
            "fat tails, or out-of-sample predictive validation are included."
        )
