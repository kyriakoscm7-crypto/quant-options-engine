"""Simulation accuracy, bounded inputs, labeling and explorer integration."""
from pathlib import Path

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from app.visualization.volatility_simulation import simulate_surface, simulation_figure


def test_anchor_and_deterministic_formula():
    x, days, z = simulate_surface()
    expected = 30 - 12 * np.log(x)[None, :] + 20 * np.log(x)[None, :]**2 + 5 * np.log(days[:, None] / 30)
    np.testing.assert_allclose(z, expected)
    assert z.shape == (40, 49)
    np.testing.assert_allclose(x[24], 1)


@pytest.mark.parametrize('args', [(float('nan'),), (float('inf'),), (4,), (101,), (True,), (30, 31), (30, 0, -1), (30, 0, 0, 16)])
def test_invalid_assumptions_rejected(args):
    with pytest.raises(ValueError):
        simulate_surface(*args)


def test_extreme_inputs_remain_bounded():
    for level in (5, 100):
        for term in (-15, 15):
            z = simulate_surface(level, 30, 60, term)[2]
            assert np.isfinite(z).all()
            assert z.min() >= 1 and z.max() <= 200


@pytest.mark.parametrize('view,kind', [('3D surface', 'surface'), ('2D heatmap', 'heatmap')])
def test_chart_labels_and_shape(view, kind):
    fig = simulation_figure(view=view)
    assert fig.data[0].type == kind
    assert fig.layout.title.text is None
    assert 'SIMULATION' in fig.data[0].hovertemplate
    assert fig.layout.paper_bgcolor == '#0B1226'
    if view == '3D surface':
        assert 1.7 < fig.layout.scene.camera.eye.x < 2.2
        assert fig.layout.scene.domain.x[0] > 0
        assert fig.layout.scene.domain.x[1] < 1
        assert fig.layout.scene.domain.y[0] > 0
        assert fig.layout.scene.aspectratio.x > 1.2
    with pytest.raises(ValueError):
        simulation_figure(view='invalid')


@pytest.mark.parametrize('symbol', ['NASDAQ:AAPL', 'NYSE:UNKNOWN', 'AMEX:SPY'])
def test_ui_controls_for_any_company_without_market_requests(symbol, monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError('Simulation attempted options access')
    import app.market_data.yahoo_client as yahoo
    monkeypatch.setattr(yahoo, 'fetch_option_chain', fail)
    app = AppTest.from_string('from dashboard.volatility_intelligence import render_volatility_intelligence\n'
                              f'render_volatility_intelligence({symbol!r})').run()
    assert not app.exception
    app.slider(key='qi_vol_level').set_value(55).run()
    app.radio(key='qi_vol_view').set_value('2D heatmap').run()
    assert not app.exception
    assert app.slider(key='qi_vol_level').value == 55


def test_exact_explorer_placement():
    source = (Path(__file__).parents[1] / 'dashboard/stock_explorer_widget.py').read_text()
    assert source.index('## Historical price chart') < source.index('render_volatility_intelligence(symbol)') < source.index('## Understanding the numbers')
