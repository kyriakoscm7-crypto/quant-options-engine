"""Look-ahead-safe educational backtesting on invented price histories.

This module intentionally accepts generated demo data only in the hosted
research UI. It neither fetches third-party quotes nor makes investment calls.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from dashboard.demo_showcase import DEMO_ASSETS, synthetic_history
from dashboard.workspace_settings import research_notes_enabled


def run_strategy_backtest(
    history: pd.DataFrame,
    fast: int,
    slow: int,
    fee_bps: float = 5.0,
) -> pd.DataFrame:
    """Backtest long-or-cash moving-average crossovers without lookahead.

    A signal based on day t's close can be applied only to day t+1's
    return. Fees are paid on position changes on the same day that the
    adjusted position becomes active. Nothing uses a future price.
    """
    if not 2 <= fast < slow <= 250:
        raise ValueError("Require 2 <= fast < slow <= 250.")
    if not math.isfinite(fee_bps) or not 0 <= fee_bps <= 1000:
        raise ValueError("Fee must be finite and in range 0–1000 bps.")
    if "Close" not in history or len(history) < slow + 30:
        raise ValueError("Insufficient illustrative closing-price history.")

    close = pd.to_numeric(history["Close"], errors="coerce")
    if not (np.isfinite(close).all() and (close > 0).all()):
        raise ValueError("Illustrative prices must be positive and finite.")
    moving_fast = close.rolling(fast, min_periods=fast).mean()
    moving_slow = close.rolling(slow, min_periods=slow).mean()

    # At time t, the earliest tradable signal is calculated using t-1.
    raw_signal = (moving_fast > moving_slow).astype(float)
    position = raw_signal.shift(1).fillna(0.0)
    returns = close.pct_change().fillna(0.0)
    changes = position.diff().abs().fillna(position.abs())
    costs = changes * fee_bps / 10000
    # Subtract trading fees from simple returns; cap for a valid equity curve.
    strategy_return = (position * returns - costs).clip(lower=-0.999)
    # Start performance after the first complete slow moving average.
    start = slow
    out = pd.DataFrame({
        "Synthetic close": close.iloc[start:],
        "Fast average": moving_fast.iloc[start:],
        "Slow average": moving_slow.iloc[start:],
        "Position": position.iloc[start:],
        "Turnover": changes.iloc[start:],
        "Strategy daily return": strategy_return.iloc[start:],
        "Buy-and-hold daily return": returns.iloc[start:],
    })
    out["Strategy value"] = 100 * (1 + out["Strategy daily return"]).cumprod()
    out["Buy-and-hold value"] = 100 * (1 + out["Buy-and-hold daily return"]).cumprod()
    return out


def backtest_stats(result: pd.DataFrame) -> dict[str, float]:
    """Use an identical window for illustrative strategy comparisons."""
    if result.empty:
        raise ValueError("Cannot score an empty backtest")
    strategy = result["Strategy value"]
    benchmark = result["Buy-and-hold value"]
    day_returns = result["Strategy daily return"]
    std = float(day_returns.std(ddof=1))
    sharpe = (
        float(day_returns.mean() / std * math.sqrt(252))
        if std > 0 else 0.0
    )
    return {
        "strategy_return_pct": float((strategy.iloc[-1] / 100 - 1) * 100),
        "benchmark_return_pct": float((benchmark.iloc[-1] / 100 - 1) * 100),
        "max_drawdown_pct": float((strategy / strategy.cummax().clip(lower=100.0) - 1).min() * 100),
        "sharpe": sharpe,
        "entry_events": int(((result["Position"].diff().fillna(result["Position"].iloc[0]) > 0).fillna(False)).sum()),
        "time_in_market_pct": float(result["Position"].mean() * 100),
    }


def render_strategy_research() -> None:
    st.title(":primary[:material/experiment:] Strategy Research")
    st.caption("PRIVATE RESEARCH LAB / reproducible strategies / illustrative backtesting")
    st.info(
        "**Synthetic market experiment.** This lab uses fictional instruments "
        "and generated prices, not actual market observations. Results are "
        "not real investment returns, trading recommendations, or a claim of "
        "predictive performance."
    )
    assets = [s for s in DEMO_ASSETS if s != "ATLAS"]
    left, right = st.columns([1.25, 1])
    with left:
        selected = st.selectbox(
            "Fictional instrument", assets,
            format_func=lambda s: f"{DEMO_ASSETS[s]['name']} ({s})",
            key="qi_strategy_symbol",
        )
    with right:
        fee = st.slider(
            "Transaction fee per position change (basis points)",
            min_value=0.0, max_value=50.0, value=5.0, step=1.0,
            key="qi_strategy_fee",
        )

    a, b = st.columns(2)
    with a:
        fast = st.slider(
            "Fast moving average (sessions)",
            min_value=5, max_value=80, value=20, step=5,
            key="qi_strategy_fast",
        )
    with b:
        slow = st.slider(
            "Slow moving average (sessions)",
            min_value=90, max_value=250, value=100, step=10,
            key="qi_strategy_slow",
        )
    result = run_strategy_backtest(synthetic_history(selected), fast, slow, fee)
    stats = backtest_stats(result)

    cols = st.columns(4)
    cols[0].metric("Simulated strategy return",
                   f"{stats['strategy_return_pct']:+.1f}%")
    cols[1].metric("Synthetic buy & hold",
                   f"{stats['benchmark_return_pct']:+.1f}%")
    cols[2].metric("Strategy max drawdown",
                   f"{stats['max_drawdown_pct']:.1f}%")
    cols[3].metric("Simulated Sharpe", f"{stats['sharpe']:.2f}")

    chart = go.Figure()
    for name, color in [
        ("Strategy value", "#ff78b7"),
        ("Buy-and-hold value", "#abb8d3"),
    ]:
        chart.add_trace(go.Scatter(
            x=list(range(len(result) + 1)), y=[100.0, *result[name]],
            name=name, mode="lines",
            line={"color": color, "width": 2.6},
        ))
    chart.update_layout(
        title="Illustrative portfolio growth / both start at 100",
        template="plotly_dark", height=440,
        paper_bgcolor="#111c2e", plot_bgcolor="#111c2e",
        font={"color": "#f8fafc"},
        xaxis_title="Illustrative session",
        yaxis_title="Synthetic portfolio index",
        hovermode="x unified",
        margin={"l": 25, "r": 20, "t": 65, "b": 30},
    )
    st.plotly_chart(chart, use_container_width=True)

    st.markdown("#### Trade and exposure diagnostics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Entry events", stats["entry_events"])
    c2.metric("Time in synthetic market",
              f"{stats['time_in_market_pct']:.1f}%")
    c3.metric("Simulated position changes",
              int((result["Turnover"] > 0).sum()))

    if research_notes_enabled():
        with st.expander("How this test avoids look-ahead bias", expanded=False):
            st.write(
                "Execution is simplified: prior-close signals apply to the next close-to-close return. Signals use prior completed synthetic closes "
                "and applied to the next session's return. Moving averages "
                "need enough prior data, both strategies use the same test "
                "period, and every entry or exit incurs the selected fee."
            )
            st.write(
                "The example omits taxes, liquidity, market impact, "
                "dividend entitlements, slippage and realistic execution "
                "constraints. Parameter tuning on the same sample may "
                "overstate apparent performance. No out-of-sample "
                "predictive ability is established."
            )
