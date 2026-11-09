"""Company-context educational volatility explorer, without market-data access."""
from html import escape

import streamlit as st

from app.visualization.volatility_simulation import simulation_figure


def render_volatility_intelligence(symbol: str) -> None:
    st.markdown('## Volatility Intelligence')
    with st.container(border=True):
        st.markdown(f'''<div style="background:radial-gradient(ellipse at top right,#42233F,#0D1424 70%);padding:24px;border-radius:14px;border-top:2px solid #FF78B7">
<div style="color:#FF78B7;font-size:12px;letter-spacing:2px">SIMULATION · VOLATILITY LAB</div>
<h3 style="margin:10px 0;color:white">Explore the shape of uncertainty</h3>
<p style="color:#DCE3F4;margin:0">Research context: {escape(symbol)} · A hypothetical landscape across strikes and time.</p></div>''', unsafe_allow_html=True)
        st.info('SIMULATION — These are invented educational assumptions, not observed '
                'company-specific implied volatility, live option quotes or a forecast. '
                'Every symbol starts with the same model. No options data is fetched.')
        view = st.radio('Explore the landscape', ['3D surface', '2D heatmap'],
                        horizontal=True, key='qi_vol_view',
                        help='Use the heatmap for easier touch navigation or if 3D is unavailable.')
        with st.expander('Shape your simulation', expanded=False):
            a, b = st.columns(2)
            with a:
                level = st.slider('Baseline volatility (%)', 5, 100, 30, key='qi_vol_level',
                                  help='Annualized modeled volatility at reference strike and 30 days.')
                skew = st.slider('Downside skew', -30, 30, 12, key='qi_vol_skew',
                                 help='Positive values lift modeled volatility at lower strikes; negative reverses it.')
            with b:
                curvature = st.slider('Smile curvature', 0, 60, 20, key='qi_vol_curve',
                                      help='Higher values lift the wings away from the reference strike.')
                term = st.slider('Expiry slope', -15, 15, 5, key='qi_vol_term',
                                 help='Positive values lift longer expiries. Negative values invert the slope.')
            st.caption('Manual assumptions persist across symbols so you can compare shapes. '
                       'Reference price is normalized to 1.00×; no stock price is assumed.')
        st.plotly_chart(simulation_figure(level, skew, curvature, term, view),
                        width='stretch', key='qi_vol_chart', config={
                            'displaylogo': False, 'scrollZoom': False,
                            'modeBarButtonsToRemove': ['toImage'], 'responsive': True})
        st.caption('Drag to rotate · Hover to inspect · Use the chart toolbar to reset the camera. '
                   'On touch screens, try the 2D heatmap. Higher does not mean a stock will rise.')
        a, b, c = st.columns(3)
        with a:
            st.markdown('**01 · Strike**')
            st.write('1.00× is the reference price. 0.90× is a strike 10% below it; 1.10× is 10% above.')
        with b:
            st.markdown('**02 · Time**')
            st.write('Expiry runs from 7 to 365 calendar days. The slope shows how your assumptions vary across time.')
        with c:
            st.markdown('**03 · Volatility**')
            st.write('Height and color show annualized modeled volatility, in percent. This measures uncertainty, not direction.')
        with st.expander('What would real implied volatility tell me?'):
            st.write('Implied volatility is inferred from an observed option price using a pricing model. '
                     'It can differ by strike and expiry. A smile describes higher volatility in the wings; '
                     'skew describes an asymmetric shape. Neither guarantees future returns.')
            st.write('This simulation is a visual teaching model, not a calibrated or arbitrage-free '
                     'options surface. Values are bounded at 1%–200%. No earnings dates, prices, '
                     'company fundamentals or historical volatility enter the model. '
                     'Actual company IV requires appropriately authorized option quotes and quality checks.')
            st.code('vol % = clip(baseline − skew × ln(K/S) + curvature × ln(K/S)²\n'
                    '             + expiry slope × ln(days / 30), 1, 200)', language=None)
