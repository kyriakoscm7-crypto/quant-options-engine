"""Manual model assumptions remain connected and valid at low prices."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).parents[1]


def test_options_greeks_roundtrip_and_subdollar_scenario():
    app = AppTest.from_file(str(ROOT / 'dashboard/main.py'))
    app.session_state['selected_page'] = '💰 Options Lab'
    app.run(timeout=45)
    app.number_input(key='qi_workspace_spot').set_value(0.25).run()
    app.number_input(key='qi_workspace_strike').set_value(0.50).run()
    app.radio(key='qi_workspace_kind').set_value('Put').run()
    app.button(key='qi_options_to_greeks').click().run()
    assert not app.exception
    assert app.session_state['selected_page'] == '📊 Greeks Analysis'
    assert app.number_input(key='qi_greeks_spot').value == 0.25
    assert app.radio(key='qi_greeks_kind').value == 'Put'
    app.slider(key='qi_greeks_move').set_value(-0.19).run()
    assert not app.exception
    app.number_input(key='qi_greeks_rate').set_value(6.0).run()
    app.button(key='qi_greeks_to_options').click().run()
    assert not app.exception
    assert app.number_input(key='qi_workspace_spot').value == 0.25
    assert app.number_input(key='qi_workspace_rate').value == 6.0
