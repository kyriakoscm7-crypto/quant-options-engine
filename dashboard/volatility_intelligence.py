"""Company-context educational volatility explorer, without market-data access."""
from html import escape

import streamlit as st

from app.visualization.volatility_simulation import simulation_figure


def render_volatility_intelligence(symbol: str) -> None:
    st.markdown('## Volatility Intelligence')
    with st.container(border=True):
        st.markdown(f'''<div style="background:linear-gradient(115deg,#101A32 12%,#2B1C3B 72%,#462540);padding:19px 24px 20px;border-radius:13px;border-top:2px solid #FF78B7;margin-bottom:8px">
<div style="color:#FF9ACA;font-size:11px;font-weight:700;letter-spacing:2px">VOLATILITY LAB <span style="color:#99ABC7">/</span> SIMULATION</div>
<h3 style="margin:7px 0 5px;color:#FFFFFF;font-size:25px;letter-spacing:-.6px">Explore the shape of uncertainty</h3>
<p style="color:#CFD8EB;margin:0;font-size:13px">Research context: {escape(symbol)} · The same illustrative model for every ticker.</p></div>''', unsafe_allow_html=True)
        st.caption('**SIMULATION ONLY** · Hypothetical annualized volatility, not observed options '
                   'data or a company-specific forecast. No options data is fetched.')
        view = st.radio('Choose your view', ['3D surface', '2D heatmap'],
                        horizontal=True, key='qi_vol_view',
                        help='Rotate the 3D surface with your mouse or choose the 2D heatmap for touch devices.')
        with st.expander('Customize the volatility shape', expanded=False):
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
            st.caption('The reference stock price is normalized to 1.00×. '
                       'These controls persist across tickers for comparison.')
        st.markdown('<div style="color:#FF9ACA;font-size:11px;letter-spacing:1.8px;font-weight:700;margin:4px 0 -12px">INTERACTIVE VOLATILITY LANDSCAPE · SIMULATION</div>',
                    unsafe_allow_html=True)
        st.plotly_chart(simulation_figure(level, skew, curvature, term, view),
                        width='stretch', key='qi_vol_chart', config={
                            'displaylogo': False, 'scrollZoom': False,
                            'modeBarButtonsToRemove': ['toImage'], 'responsive': True})
        st.caption('**Explore:** Drag to rotate · Hover for precise modeled IV · Double-click to reset. '
                   'The height indicates volatility, **not** the direction of a future price move.')
        with st.expander('How to read this visualization'):
            a, b, c = st.columns(3)
            with a:
                st.markdown('**Strike ratio**')
                st.write('1.00× is the reference price; 0.90× is 10% below.')
            with b:
                st.markdown('**Time to expiry**')
                st.write('Move from 7 to 365 calendar days.')
            with c:
                st.markdown('**Volatility (%)**')
                st.write('Height and color show annualized hypothetical IV.')
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
