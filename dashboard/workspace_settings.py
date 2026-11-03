"""Session-local workspace preferences and compact top-right settings.

Access control is configured in the hosting platform, not in Streamlit
session state. This module does not implement authentication or alter
market-data permission boundaries.
"""

from __future__ import annotations

import streamlit as st

PREFERENCE_KEYS = (
    "qi_external_charts",
    "qi_show_research_notes",
    "qi_display_density",
    "qi_reduce_motion",
)

DEFAULTS = {
    "qi_external_charts": False,
    "qi_show_research_notes": True,
    "qi_display_density": "Comfortable",
    "qi_reduce_motion": False,
}


def initialize_workspace_preferences() -> None:
    """Prefer predictable session-only defaults, especially for external charts."""
    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = default


def reset_workspace_preferences() -> None:
    """Reset only application preferences; never pretend to clear host logs."""
    for key, default in DEFAULTS.items():
        st.session_state[key] = default


def render_workspace_settings() -> None:
    """Compact, usable gear in the top-right of the main content area."""
    initialize_workspace_preferences()

    with st.container(key="qi_workspace_bar"):
        header, actions = st.columns([0.92, 0.08], vertical_alignment="center")
        with header:
            st.markdown(
                '<div class="qi-workspace-header">'
                '<span class="qi-workspace-dot" aria-hidden="true"></span>'
                'QUANT INTELLIGENCE <span class="qi-workspace-separator">/</span>'
                ' RESEARCH WORKSPACE'
                '</div>',
                unsafe_allow_html=True,
            )
        with actions, st.container(key="qi_settings_gear"), st.popover(
            "",
            icon=":material/settings:",
            help="Settings",
            use_container_width=False,
        ):
            st.markdown("**Workspace preferences**")
            st.caption(
                "Settings are local to this browser session. Access is "
                "controlled by the Streamlit hosting dashboard, not this menu."
            )
            preferences, workspace = st.tabs(["Preferences", "About & legal"])
            with preferences:
                st.selectbox(
                    "Display density",
                    ["Comfortable", "Compact"],
                    key="qi_display_density",
                    help="Reduce unused space without changing charts or calculations.",
                )
                st.toggle(
                    "Show research guidance",
                    key="qi_show_research_notes",
                    help="Show concise context beside research and simulation tools.",
                )
                st.toggle(
                    "Reduce animations",
                    key="qi_reduce_motion",
                    help="Minimize decorative movement for comfort and accessibility.",
                )
                st.toggle(
                    "Enable external TradingView charts",
                    key="qi_external_charts",
                    help="Off by default. Enabling loads TradingView from your browser.",
                )
                st.caption(
                    "TradingView receives connection metadata including IP "
                    "address, embedding URL and selected symbol when loaded. "
                    "Disabling prevents future chart loads, not past requests."
                )
                st.button(
                    "Reset preferences",
                    key="qi_reset_workspace_preferences",
                    use_container_width=True,
                    on_click=reset_workspace_preferences,
                )
            with workspace:
                st.markdown("**Independent quantitative research**")
                st.caption(
                    "Access is invitation-only if the hosting dashboard "
                    "is configured privately. To add or remove viewers, "
                    "use Streamlit Community Cloud's Sharing settings. "
                    "This menu cannot manage accounts or revoke access."
                )
                st.caption(
                    "Real stocks: provider-hosted TradingView chart only. "
                    "Models and screening: clearly labeled hypothetical "
                    "calculations and synthetic simulations."
                )
                if st.button(
                    "Legal, privacy & methodology",
                    key="qi_open_legal_settings",
                    use_container_width=True,
                ):
                    st.session_state["_navigation_request"] = "📄 Legal & Privacy"
                    st.rerun()
    

    # Applied after preference widgets so a change is visible immediately.
    if st.session_state.get("qi_display_density") == "Compact":
        st.markdown(
            "<style>"
            '[data-testid="stVerticalBlock"] {gap: 0.65rem;}'
            '[data-testid="stMetric"] {padding: 0.2rem 0;}'
            "</style>",
            unsafe_allow_html=True,
        )
    if st.session_state.get("qi_reduce_motion", False):
        st.markdown(
            "<style>"
            "*, *::before, *::after {animation-duration:0.01ms !important;"
            "animation-iteration-count:1 !important;"
            "transition-duration:0.01ms !important;"
            "scroll-behavior:auto !important;}"
            "</style>",
            unsafe_allow_html=True,
        )
    st.markdown(
        "<style>"
        '.st-key-qi_workspace_bar [data-testid="stHorizontalBlock"] {flex-wrap:nowrap !important;}'
        '.st-key-qi_workspace_bar [data-testid="stColumn"] {min-width:0 !important;}'
        '.st-key-qi_workspace_bar [data-testid="stColumn"]:first-child {flex:1 1 0 !important;}'
        '.st-key-qi_workspace_bar [data-testid="stColumn"]:last-child {flex:0 0 44px !important;}'
        '.st-key-qi_settings_gear [data-testid="stPopover"] {display:flex;justify-content:flex-end;}'
        '.st-key-qi_settings_gear button {width:2.5rem;min-width:2.5rem;padding:0.4rem;}'
        ".qi-workspace-header {color:#aebdd4;font-size:0.68rem;"
        "letter-spacing:0.15em;font-weight:650;padding:0.7rem 0;}"
        ".qi-workspace-dot {display:inline-block;width:7px;height:7px;"
        "border-radius:50%;background:#ff78b7;margin-right:10px;}"
        ".qi-workspace-separator {color:#ff78b7;padding:0 0.4rem;}"
        "@media(max-width:640px){.qi-workspace-header{font-size:0.54rem;"
        "letter-spacing:0.07em;}}"
        "</style>",
        unsafe_allow_html=True,
    )


def research_notes_enabled() -> bool:
    """Whether the user wants optional educational context."""
    return st.session_state.get("qi_show_research_notes", True)
