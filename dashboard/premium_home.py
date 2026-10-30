"""Premium Quant Intelligence homepage."""

import re

import streamlit as st

from dashboard.home_analytics import render_options_preview


def render_html(content):
    """Render HTML as one continuous string."""
    flattened = re.sub(r"\s*\n\s*", " ", content).strip()
    st.html(flattened)


def render_premium_home():

    render_html(
        """
<div style="
position:relative;
overflow:hidden;
padding:52px 46px;
border:1px solid #34405E;
border-radius:24px;
background:
radial-gradient(
ellipse at 85% 20%,
rgba(255,120,183,0.16),
transparent 45%
),
linear-gradient(135deg,#152441,#090E1D);
margin-bottom:32px;
">
<div style="
color:#FF78B7;
font-size:12px;
font-weight:750;
letter-spacing:3px;
margin-bottom:20px;
">
QUANTITATIVE RESEARCH PLATFORM
</div>

<div style="
color:#FFFFFF;
font-size:clamp(36px,5vw,64px);
font-weight:850;
letter-spacing:-2.5px;
line-height:1.08;
margin-bottom:22px;
">
Intelligence for<br>
<span style="color:#FF78B7;">
every market move.
</span>
</div>

<div style="
color:#B1BED7;
font-size:17px;
line-height:1.75;
max-width:610px;
">
An advanced quantitative intelligence terminal.
Research markets, model derivatives, analyze
portfolios, and discover financial insights
through powerful analytical tools.
</div>

<div style="
display:flex;
flex-wrap:wrap;
gap:12px;
margin-top:32px;
">
<span style="
border:1px solid #3B4B68;
border-radius:30px;
padding:9px 16px;
color:#E8EDFA;
font-size:12px;
">OPTIONS ANALYTICS</span>

<span style="
border:1px solid #3B4B68;
border-radius:30px;
padding:9px 16px;
color:#E8EDFA;
font-size:12px;
">PORTFOLIO RISK</span>

<span style="
border:1px solid #3B4B68;
border-radius:30px;
padding:9px 16px;
color:#E8EDFA;
font-size:12px;
">QUANT RESEARCH</span>
</div>
</div>
""",

    )

    render_options_preview()

    st.divider()

    st.markdown("### Explore the Platform")
    st.caption(
        "Professional analytics. Powerful research. "
        "One integrated workspace."
    )

    modules = [
        (
            "01",
            "Stock Explorer",
            "Analyze market history, price trends, "
            "and historical performance.",
            "🔎 Stock Explorer",
            "Open Stock Explorer",
        ),
        (
            "02",
            "Options Lab",
            "Explore theoretical option prices "
            "and derivatives analytics.",
            "💰 Options Lab",
            "Open Options Lab",
        ),
        (
            "03",
            "Risk Analytics",
            "Understand Greeks and market "
            "sensitivity across scenarios.",
            "📊 Greeks Analysis",
            "Explore Risk",
        ),
        (
            "04",
            "Market Scanner",
            "Rank stocks using transparent "
            "quantitative research factors.",
            "🔍 Market Scanner",
            "Launch Scanner",
        ),
        (
            "05",
            "Portfolio Intelligence",
            "Explore portfolio performance, "
            "allocation, and historical risk.",
            "💼 Portfolio Manager",
            "Open Portfolio",
        ),
        (
            "06",
            "Forecast Intelligence",
            "Evaluate machine learning forecasts "
            "using historical research.",
            "🧠 Forecast Intelligence",
            "Explore Forecasts",
        ),
    ]

    for row_start in range(0, len(modules), 2):
        columns = st.columns(2, gap="large")

        for column, module in zip(
            columns, modules[row_start:row_start + 2]
        ):
            number, title, description, destination, label = module

            with column:
                render_html(
                    f"""
<div class="dashboard-card"
style="min-height:175px;">
<div style="
color:#FF78B7;
font-size:12px;
font-weight:750;
letter-spacing:2px;
margin-bottom:16px;
">{number} / RESEARCH MODULE</div>

<h3 style="
font-size:21px;
margin-bottom:10px;
">{title}</h3>

<p style="
font-size:14px;
line-height:1.6;
">{description}</p>
</div>
""",

                )

                if st.button(
                    label + " →",
                    key=f"premium_module_{number}",
                    use_container_width=True,
                ):
                    st.session_state[
                        "_navigation_request"
                    ] = destination
                    st.rerun()

    st.divider()

    st.caption(
        "QUANT INTELLIGENCE  /  "
        "RESEARCH & ANALYTICS PLATFORM"
    )
    st.caption(
        "Educational and research use only. "
        "Not personalized financial advice."
    )
