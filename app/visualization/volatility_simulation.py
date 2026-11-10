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
    axis = {
        'gridcolor': '#27334B',
        'gridwidth': 2,
        'linecolor': '#61708E',
        'tickfont': {'color': '#ACBEDA', 'size': 11},
        'zeroline': False,
        'showbackground': False,
        'showspikes': False,
    }
    # Frame the full surface and its axis labels within Plotly's scene. A very
    # close camera makes the front corners and tick labels clip on wide screens.
    if view == '3D surface':
        figure.update_layout(
            scene={
                'domain': {'x': [0.08, 0.92], 'y': [0.09, 0.93]},
                'xaxis': dict(axis, title={'text': 'Strike / price', 'font': {'size': 12}}),
                'yaxis': dict(axis, title={'text': 'Days to expiry', 'font': {'size': 12}}),
                'zaxis': dict(
                    axis, title={'text': 'IV (%)', 'font': {'size': 12}},
                    range=[max(0, float(z.min()) - 4), float(z.max()) + 4],
                ),
                'bgcolor': '#0B1226',
                'aspectmode': 'manual',
                'aspectratio': {'x': 1.38, 'y': 1.12, 'z': 0.58},
                'camera': {
                    'eye': {'x': 1.85, 'y': -2.15, 'z': 1.35},
                    'center': {'x': 0, 'y': 0, 'z': 0},
                    'up': {'x': 0, 'y': 0, 'z': 1},
                    'projection': {'type': 'perspective'},
                },
            },
        )
        figure.update_traces(
            contours={'z': {'show': True, 'usecolormap': True, 'project_z': True,
                            'highlightcolor': '#F4D9EC', 'width': 1}},
            lighting={'ambient': 0.8, 'diffuse': 0.75, 'specular': 0.16,
                      'roughness': 0.65, 'fresnel': 0.08},
            lightposition={'x': -40, 'y': -20, 'z': 100},
        )
    else:
        figure.update_traces(
            colorbar={'title': 'IV (%)', 'thickness': 12, 'len': 0.78,
                      'tickfont': {'color': '#CBD5EB'}},
            showscale=True,
        )
        figure.update_layout(
            xaxis={'title': 'Strike / reference price', 'gridcolor': '#23334F',
                   'tickfont': {'color': '#CBD5EB'}},
            yaxis={'title': 'Days to expiry', 'gridcolor': '#23334F',
                   'tickfont': {'color': '#CBD5EB'}},
        )
    figure.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0B1226',
        plot_bgcolor='#0B1226',
        font={'color': '#DCE3F4', 'family': 'Arial', 'size': 12},
        title=None,
        margin={'l': 4, 'r': 4, 't': 8, 'b': 8},
        height=515 if view == '3D surface' else 425,
        uirevision='volatility-simulation',
    )
    return figure
