
"""
Quant Options Engine | Quant Intelligence Dashboard.

Interactive research dashboard providing:
- Platform overview.
- Historical stock research.
- European option pricing.
- Analytical Greeks.
- Hypothetical option price scenarios.

Run from the project root:

    python -m streamlit run dashboard/main.py

Historical market data is for research and education.
It is not a prediction or investment recommendation.
"""
import sys
from pathlib import Path

import streamlit as st

# ============================================================
# PROJECT IMPORT CONFIGURATION
# ============================================================

# Add the repository root before importing project modules.
# This supports both local runs and Streamlit Cloud.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.learn_page import render_learn_page  # noqa: E402
from dashboard.legal_pages import render_legal_pages  # noqa: E402
from dashboard.navigation_ux import render_navigation_ux  # noqa: E402
from dashboard.premium_home import render_premium_home  # noqa: E402
from dashboard.public_safety import public_market_data_route_blocked  # noqa: E402
from dashboard.workspace_settings import (  # noqa: E402
    render_workspace_settings,
    research_notes_enabled,
)

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Quant Intelligence | Quant Options Engine",
    page_icon=str(Path(__file__).parent / "assets" / "qi_favicon.png"),
    layout="wide",
    initial_sidebar_state="auto",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #080d18;
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] {
        background-color: #0d1424;
        border-right: 1px solid #1e293b;
    }

    h1, h2, h3 {
        color: #f8fafc;
    }

    [data-testid="stMetric"] {
        background: #111c2e;
        border: 1px solid #243247;
        border-radius: 12px;
        padding: 18px;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8;
    }

    [data-testid="stMetricValue"] {
        color: #f8fafc;
    }

    div.stButton > button {
        background-color: #FF78B7;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
    }

    div.stButton > button:hover {
        background-color: #FF96C7;
        color: white;
    }

    .section-caption {
        color: #94a3b8;
        font-size: 0.95rem;
    }

    .dashboard-card {
        background: #111c2e;
        border: 1px solid #243247;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 12px;
    }

    .dashboard-card h3 {
        margin-top: 0;
    }

    .dashboard-card p {
        color: #94a3b8;
        margin-bottom: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)



# Load Quant Intelligence premium styling.
premium_css = (
    Path(__file__).parent / "premium_theme.css"
).read_text(encoding="utf-8")

st.markdown(
    f"<style>{premium_css}</style>",
    unsafe_allow_html=True,
)

# ============================================================
# CACHE MARKET DATA
# ============================================================

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:

    st.html(
        '<div class="qi-brand">'
        '<div class="qi-brand-mark">QI</div>'
        '<div>'
        '<div class="qi-brand-name">QUANT INTELLIGENCE</div>'
        '<div class="qi-brand-subtitle">RESEARCH TERMINAL</div>'
        '<div class="qi-brand-credit">Developed by Kyriakos Margaritis</div>'
        '</div></div>'
    )


    sections = [
        ("Dashboard", "🏠 Overview", []),
        ("Research", "🔎 Stock Explorer", [
            ("Stock Explorer", "🔎 Stock Explorer"),
        ]),
        ("Discover", "💎 Quant Discovery", [
            ("Scan & investigate", "💎 Quant Discovery"),
        ]),
        ("Quant Lab", "💰 Options Lab", [
            ("Options Lab", "💰 Options Lab"),
            ("Greeks Analysis", "📊 Greeks Analysis"),
            ("Scenario Explorer", "📈 Scenario Explorer"),
        ]),
        ("Model testing", "🧠 Strategy Research", [
            ("Strategy Research · hypothetical", "🧠 Strategy Research"),
            ("Simulation Lab", "🧪 Simulation Lab"),
            ("Forecast Lab · synthetic", "🧠 Forecast Intelligence"),
            ("Portfolio Lab · synthetic", "💼 Portfolio Manager"),
        ]),
        ("Learn", "📚 Learn", []),
    ]

    route_groups = {"📄 Legal & Privacy": "Legal"}

    for group, landing, tools in sections:
        route_groups[landing] = group

        for label, route in tools:
            route_groups[route] = group

    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = "🏠 Overview"

    # Handle clickable Intelligence Network links without changing route IDs.
    # The URL key is consumed once, so it cannot override later sidebar clicks.
    _qi_orbit_routes = {
        "discover": "💎 Quant Discovery",
        "research": "🔎 Stock Explorer",
        "learn": "📚 Learn",
        "analyze": "💰 Options Lab",
        "portfolio": "💼 Portfolio Manager",
    }
    _qi_orbit_destination = _qi_orbit_routes.get(st.query_params.get("qi_go", ""))
    if _qi_orbit_destination:
        st.session_state["_navigation_request"] = _qi_orbit_destination
        del st.query_params["qi_go"]

    requested_page = st.session_state.pop(
        "_navigation_request", None
    )

    if requested_page == "🔍 Market Scanner":
        requested_page = "💎 Quant Discovery"
        st.session_state["qi_discovery_stage"] = "Scan"

    if requested_page in route_groups:
        st.session_state["selected_page"] = requested_page

    if st.session_state["selected_page"] == "🔍 Market Scanner":
        st.session_state["selected_page"] = "💎 Quant Discovery"
        st.session_state["qi_discovery_stage"] = "Scan"

    if st.session_state["selected_page"] not in route_groups:
        st.session_state["selected_page"] = "🏠 Overview"

    current_page = st.session_state["selected_page"]
    active_group = route_groups[current_page]

    section_icons = {
        "Dashboard": ":material/dashboard:",
        "Research": ":material/search:",
        "Discover": ":material/radar:",
        "Portfolio": ":material/account_balance_wallet:",
        "Quant Lab": ":material/science:",
        "Model testing": ":material/experiment:",
        "Learn": ":material/school:",
        "Legal": ":material/gavel:",
    }

    with st.container(key="qi_navigation"):
        for index, (group, landing, tools) in enumerate(sections):
            is_active = group == active_group

            if tools:
                arrow = "▾" if is_active else "▸"
                button_label = f"{arrow}  {group}"
            else:
                button_label = group

            if st.button(
                button_label,
                key=f"qi_group_{index}",
                icon=section_icons[group],
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                # QI SIDEBAR RESET V1
                st.session_state["selected_page"] = landing
                st.session_state["qi_learn_pathway"] = None
                st.session_state["qi_learn_lesson"] = None
                st.session_state["_qi_sidebar_reset_count"] = (
                    st.session_state.get("_qi_sidebar_reset_count", 0) + 1
                )
                st.rerun()

            if is_active and tools:
                with st.container(key="qi_subnav"):
                    for tool_index, (label, route) in enumerate(tools):
                        selected = current_page == route
                        marker = "●" if selected else "›"

                        if st.button(
                            f"{marker}  {label}",
                            key=f"qi_subpage_{index}_{tool_index}",
                            type="primary" if selected else "secondary",
                            use_container_width=True,
                        ):
                            st.session_state["selected_page"] = route
                            st.session_state["qi_learn_pathway"] = None
                            st.session_state["qi_learn_lesson"] = None
                            st.session_state["_qi_sidebar_reset_count"] = (
                                st.session_state.get("_qi_sidebar_reset_count", 0) + 1
                            )
                            st.rerun()

    page = st.session_state["selected_page"]
    render_navigation_ux()

    st.divider()
    st.caption("PRIVATE RESEARCH BUILD")
    st.caption(
        "Access managed in Streamlit Sharing · "
        "Independent research and education"
    )


# ============================================================
# TOP-RIGHT WORKSPACE CONTROL
# ============================================================
render_workspace_settings()


# ============================================================
# SHARED OPTION INPUTS
# ============================================================

# Fail closed on public-facing routes that currently use or derive results
# from unlicensed/unverified external market feeds.
if page != "🔎 Stock Explorer":
    st.caption(
        "Research and education only · No individualized investment advice · "
        "Models and data may be incomplete or inaccurate."
    )

if page == "🔎 Stock Explorer":
    from dashboard.stock_explorer_widget import render_stock_explorer

    render_stock_explorer()
    st.stop()

if public_market_data_route_blocked(page):
    # Official browser-only displays and independent models; never
    # unverified server-side historical or live market feeds.
    from dashboard.demo_showcase import render_demo_research_page

    render_demo_research_page(page)
    st.stop()

# ============================================================
# OVERVIEW
# ============================================================


if page == "🏠 Overview":
    if research_notes_enabled():
        st.caption(
            "Real-stock charts in Stock Explorer are provided by TradingView. "
            "Discover screens annual SEC fundamentals inside the app. Simulation Lab uses independent assumptions; portfolio and forecast demos remain fictional."
        )
    render_premium_home()


elif page == "📄 Legal & Privacy":
    render_legal_pages()

elif page == "📚 Learn":
    with st.container(key="qi_learn_page"):
        render_learn_page()

elif page == "💰 Options Lab":
    from dashboard.options_workspace import render_options_workspace

    render_options_workspace()


elif page == "📊 Greeks Analysis":
    from dashboard.greeks_workspace import render_greeks_workspace

    render_greeks_workspace()


elif page == "📈 Scenario Explorer":
    from dashboard.scenario_workspace import render_scenario_workspace
    render_scenario_workspace()


# ============================================================
# FUTURE MODULE PLACEHOLDERS
# ============================================================

elif page == "🔍 Market Scanner":

    st.session_state["_navigation_request"] = "💎 Quant Discovery"
    st.rerun()


elif page == "💎 Quant Discovery":
    import runpy

    discovery_page = (
        Path(__file__).resolve().parent
        / "pages"
        / "2_Quant_Discovery.py"
    )

    runpy.run_path(str(discovery_page), run_name="__main__")

elif page == "💼 Portfolio Manager" or page == "🧠 Forecast Intelligence":

    from dashboard.demo_showcase import render_demo_research_page
    render_demo_research_page(page)


elif page == "🧠 Strategy Research":
    from dashboard.strategy_research import render_strategy_research

    render_strategy_research()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Quant Intelligence | Quant Options Engine "
    "| Research and educational use only."
)
