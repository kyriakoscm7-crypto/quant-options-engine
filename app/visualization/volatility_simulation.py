"""Offline educational surfaces; never calibrated to a security or option quotes."""
import math

import numpy as np
import plotly.graph_objects as go

from app.visualization.volatility_surface_3d import VOLATILITY_PALETTE as PALETTE


def simulate_surface(level=30, skew=12, curvature=20, term=5):
    """Return moneyness, calendar days and annualized hypothetical volatility (%).

    level anchors K/S=1 at 30 days. Log-strike skew and curvature are
    illustrative shape controls, not an arbitrage-free option pricing model.
    """
    for value, low, high in ((level, 5, 100), (skew, -30, 30),
                             (curvature, 0, 60), (term, -15, 15)):
        if isinstance(value, bool) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError('Simulation assumption outside supported range')
    money = np.linspace(0.7, 1.3, 49)
    days = np.linspace(7, 365, 40)
    x, y = np.meshgrid(money, days)
    log_strike = np.log(x)
    z = np.clip(level - skew * log_strike + curvature * log_strike**2
                + term * np.log(y / 30), 1, 200)
    return money, days, z


def simulation_figure(level=30, skew=12, curvature=20, term=5, view='3D surface'):
    """Plotly companion to the existing observed-quote visualization."""
    money, days, z = simulate_surface(level, skew, curvature, term)
    hover = ('SIMULATION<br>Strike / reference: %{x:.2f}×'
             '<br>Expiry: %{y:.0f} calendar days'
             '<br>Modeled volatility: %{z:.1f}%<extra></extra>')
    if view == '3D surface':
        trace = go.Surface(x=money, y=days, z=z, colorscale=PALETTE,
                           hovertemplate=hover, showscale=False,
                           contours={'z': {'show': True, 'usecolormap': True,
                                           'highlightcolor': '#FFFFFF', 'width': 1}},
                           lighting={'ambient': 0.7, 'diffuse': 0.8, 'roughness': 0.5})
    elif view == '2D heatmap':
        trace = go.Heatmap(x=money, y=days, z=z, colorscale=PALETTE,
                           hovertemplate=hover, showscale=False)
    else:
        raise ValueError('Unsupported view')
    figure = go.Figure(trace)
    axis = {'gridcolor': '#26324A', 'zeroline': False, 'showbackground': False}
    figure.update_layout(
        template='plotly_dark', paper_bgcolor='#080D1D', plot_bgcolor='#080D1D',
        font={'color': '#DCE3F4', 'family': 'Arial', 'size': 12},
        title={'text': 'SIMULATION · Hypothetical volatility', 'font': {'size': 16}},
        margin={'l': 30, 'r': 20, 't': 55, 'b': 30}, height=460,
        uirevision='volatility-simulation',
        scene={'xaxis': dict(axis, title='Strike ratio'),
               'yaxis': dict(axis, title='Days'),
               'zaxis': dict(axis, title='Vol (%)', range=[max(0, float(z.min()) - 5), float(z.max()) + 5]),
               'bgcolor': '#080D1D', 'aspectratio': {'x': 1.3, 'y': 1.3, 'z': 0.8},
               'camera': {'eye': {'x': 2.3, 'y': -2.4, 'z': 1.7}}},
        xaxis_title='Strike / reference price', yaxis_title='Calendar days to expiry',
    )
    return figure
