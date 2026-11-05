"""Research math and interactive behavior without a market-data dependency."""

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from app.intelligence.explorer_lab import portfolio_path, research_paths


def test_repeatable_paths_and_portfolio_endpoints():
    paths = research_paths(.08, .25, .6)
    assert paths.equals(research_paths(.08, .25, .6))
    assert (paths.iloc[0] == 100).all()
    assert np.isfinite(paths).all().all()
    assert (paths > 0).all().all()
    np.testing.assert_allclose(portfolio_path(paths, 1), paths['Model A'])
    np.testing.assert_allclose(portfolio_path(paths, 0), paths['Model B'])
    np.testing.assert_allclose(portfolio_path(paths, .5), paths.mean(axis=1))
    assert not paths.equals(research_paths(.08, .4, .6))


@pytest.mark.parametrize('args', [(float('nan'), .2, .6), (.1, 0, .6), (.1, .2, 1.1)])
def test_invalid_assumptions_rejected(args):
    with pytest.raises(ValueError):
        research_paths(*args)


def test_optional_lab_interactions():
    app = AppTest.from_string('from dashboard.stock_research_lab import render_research_lab\nrender_research_lab()').run()
    assert not app.exception
    initial = [metric.value for metric in app.metric]
    app.slider(key='lab_vol').set_value(50).run()
    assert not app.exception
    assert app.metric[1].value != initial[1]
    assert any(b.label == 'Open Options workspace' for b in app.button)
    assert len(app.get('plotly_chart')) == 3
    app.button(key='qi_simulation_options').click().run()
    assert app.session_state['_navigation_request'] == '💰 Options Lab'
