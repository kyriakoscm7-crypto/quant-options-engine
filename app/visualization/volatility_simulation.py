"""Clearly labeled educational volatility charts with no market-data access."""
import math

import numpy as np
import plotly.graph_objects as go

from app.visualization.volatility_surface_3d import VOLATILITY_PALETTE as PALETTE

PINK = "#FF78B7"
INK = "#0B1226"
GRID = "#25334B"
TEXT = "#DCE3F4"
EXPIRIES = (7, 30, 90, 180, 365)


def simulate_surface(level=30, skew=12, curvature=20, term=5):
    """Hypothetical annualized IV (%) at strike ratios and expiry days.

    This is a teaching formula, not calibrated to options prices or guaranteed
    arbitrage-free. No underlying-specific input or market feed is involved.
    """
    for value, low, high in (
        (level, 5, 100), (skew, -30, 30),
        (curvature, 0, 60), (term, -15, 15),
    ):
        if isinstance(value, bool) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError("Simulation assumption outside supported range")
    money = np.linspace(0.7, 1.3, 49)
    days = np.linspace(7, 365, 40)
    x, y = np.meshgrid(money, days)
    log_strike = np.log(x)
    z = np.clip(
        level - skew * log_strike + curvature * log_strike**2
        + term * np.log(y / 30), 1, 200,
    )
    return money, days, z


def simulated_slice(level=30, skew=12, curvature=20, term=5, expiry_days=30):
    """Exact curve for one selected expiry, without grid interpolation."""
    money, _, _ = simulate_surface(level, skew, curvature, term)
    if expiry_days not in EXPIRIES:
        raise ValueError("Unsupported expiry")
    log_strike = np.log(money)
    values = np.clip(
        level - skew * log_strike + curvature * log_strike**2
        + term * np.log(expiry_days / 30), 1, 200,
    )
    return money, values


def simulation_figure(
    level=30, skew=12, curvature=20, term=5,
    view="Volatility curve", *, expiry_days=30, camera_revision=0,
):
    """Visualize the same invented model as a readable 2D curve or 3D surface."""
    money, days, z = simulate_surface(level, skew, curvature, term)
    fig = go.Figure()
    hover3d = (
        "<b>SIMULATION — NOT MARKET DATA</b><br>"
        "Strike / reference: %{x:.2f}×<br>"
        "Expiry: %{y:.0f} days<br>"
        "Modeled volatility: %{z:.1f}%<extra></extra>"
    )

    if view == "Volatility curve":
        x, values = simulated_slice(level, skew, curvature, term, expiry_days)
        reference = float(values[len(x) // 2])
        fig.add_trace(go.Scatter(
            x=x, y=values, mode="lines", name=f"{expiry_days}-day simulation",
            line={"color": PINK, "width": 4, "shape": "spline", "smoothing": 0.5},
            fill="tozeroy", fillcolor="rgba(255,120,183,0.07)",
            hovertemplate=(
                "<b>SIMULATION — NOT MARKET DATA</b><br>"
                "Strike ratio: %{x:.2f}×<br>"
                "Modeled IV: %{y:.1f}%<extra></extra>"
            ),
        ))
        fig.add_hline(
            y=reference, line_color="#7197C0", line_dash="dot",
            line_width=1, annotation_text=f"At-the-money {reference:.1f}%",
            annotation_position="bottom right",
        )
        fig.add_vline(x=1, line_color="#A8B7CC", line_dash="dash", line_width=1)
        span = max(2.0, float(np.ptp(values)))
        low = max(0, float(values.min()) - max(2, span * 0.35))
        high = float(values.max()) + max(2, span * 0.35)
        fig.update_layout(
            xaxis={
                "title": "Strike relative to reference price",
                "range": [0.7, 1.3], "tickvals": [0.7, 0.8, 0.9, 1, 1.1, 1.2, 1.3],
                "ticktext": ["70%", "80%", "90%", "100%", "110%", "120%", "130%"],
                "gridcolor": GRID, "zeroline": False, "fixedrange": True,
            },
            yaxis={
                "title": "Modeled annualized volatility (%)",
                "range": [low, high], "gridcolor": GRID,
                "zeroline": False, "fixedrange": True,
            },
            showlegend=False, height=370,
            margin={"l": 58, "r": 28, "t": 25, "b": 65},
        )
    elif view == "3D surface":
        fig.add_trace(go.Surface(
            x=money, y=days, z=z, colorscale=PALETTE, showscale=False,
            hovertemplate=hover3d,
            lighting={"ambient": 0.8, "diffuse": 0.75, "roughness": 0.72,
                      "specular": 0.12},
            contours={"z": {"show": True, "usecolormap": True, "width": 1}},
        ))
        axis = {
            "gridcolor": GRID, "linecolor": "#667A9B",
            "zeroline": False, "showbackground": False,
            "tickfont": {"color": "#B8C5DE", "size": 11},
        }
        fig.update_layout(
            scene={
                "domain": {"x": [0.08, 0.92], "y": [0.07, 0.94]},
                "xaxis": dict(axis, title="Strike ratio", nticks=5),
                "yaxis": dict(axis, title="Days to expiry", nticks=6),
                "zaxis": dict(
                    axis, title="IV (%)",
                    range=[max(0, float(z.min()) - 4), float(z.max()) + 4],
                ),
                "bgcolor": INK, "dragmode": "turntable",
                "aspectmode": "manual",
                "aspectratio": {"x": 1.35, "y": 1.10, "z": 0.64},
                "camera": {
                    "eye": {"x": 1.48, "y": -1.68, "z": 1.08},
                    "up": {"x": 0, "y": 0, "z": 1},
                    "projection": {"type": "orthographic"},
                },
            },
            height=465,
            margin={"l": 0, "r": 0, "t": 0, "b": 0},
        )
    elif view == "2D heatmap":
        # Full model levels rather than deceptive relative color changes.
        fig.add_trace(go.Heatmap(
            x=money, y=days, z=z, colorscale=PALETTE,
            zmin=float(z.min()), zmax=float(z.max()),
            colorbar={
                "title": "IV (%)", "thickness": 12, "len": 0.8,
                "tickfont": {"color": "#C8D5E8"}, "outlinewidth": 0,
            },
            hovertemplate=hover3d,
        ))
        fig.add_hline(
            y=expiry_days, line_color="#F6F8FF", line_dash="dash", line_width=2,
            annotation_text=f"{expiry_days}-day slice",
            annotation_position="top left",
        )
        fig.add_vline(x=1, line_color="#D0E5FF", line_dash="dot", line_width=1)
        fig.update_layout(
            xaxis={
                "title": "Strike / reference price", "gridcolor": GRID,
                "fixedrange": True,
            },
            yaxis={
                "title": "Days to expiry", "gridcolor": GRID,
                "fixedrange": True,
            },
            height=390, margin={"l": 60, "r": 42, "t": 18, "b": 55},
        )
    else:
        raise ValueError("Unsupported view")

    fig.update_layout(
        template="plotly_dark", paper_bgcolor=INK, plot_bgcolor=INK,
        font={"color": TEXT, "family": "Arial", "size": 12},
        uirevision=f"sim-{view}-{camera_revision}",
        hovermode="closest",
    )
    return fig
