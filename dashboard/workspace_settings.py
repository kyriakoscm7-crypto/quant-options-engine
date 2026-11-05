"""Session-local workspace preferences and compact top-right settings.

Access control is configured in the hosting platform, not in Streamlit
session state. This module does not implement authentication or alter
market-data permission boundaries.
"""

from __future__ import annotations

import streamlit as st

EXTERNAL_PANELS_NOTICE_VERSION = 2


PREFERENCE_KEYS = (
    "qi_external_panels_notice_version",
    "qi_external_charts",
    "qi_show_research_notes",
    "qi_display_density",
    "qi_reduce_motion",
)

DEFAULTS = {
    "qi_external_panels_notice_version": 0,
    "qi_external_charts": False,
    "qi_show_research_notes": True,
    "qi_display_density": "Comfortable",
    "qi_reduce_motion": False,
}


def initialize_workspace_preferences() -> None:
    """Prefer predictable session-only defaults, especially for external charts."""
    import os

    local_preview = (
        os.environ.get("QI_LOCAL_AUTO_TRADINGVIEW") == "1"
    )

    for key, default in DEFAULTS.items():
        if key not in st.session_state:
            if key == "qi_external_charts" and local_preview:
                st.session_state[key] = True
            elif (
                key == "qi_external_panels_notice_version"
                and local_preview
            ):
                st.session_state[key] = EXTERNAL_PANELS_NOTICE_VERSION
            else:
                st.session_state[key] = default

    # A prior chart-only choice must not silently become permission for automatic
    # screeners across additional research pages after a hot reload.
    if (st.session_state["qi_external_charts"]
            and st.session_state["qi_external_panels_notice_version"] != EXTERNAL_PANELS_NOTICE_VERSION):
        st.session_state["qi_external_charts"] = False
        st.session_state["qi_external_panels_notice_version"] = 0


def record_external_panel_choice() -> None:
    st.session_state["qi_external_panels_notice_version"] = (
        EXTERNAL_PANELS_NOTICE_VERSION if st.session_state["qi_external_charts"] else 0
    )


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

            st.markdown(
                '<div class="qi-settings-title">Workspace settings</div>'
                '<div class="qi-settings-subtitle">'
                'Customize your research environment'
                '</div>',
                unsafe_allow_html=True,
            )

            preferences, workspace = st.tabs(
                ["Preferences", "About & legal"]
            )

            with preferences:
                st.markdown("**Appearance**")

                st.selectbox(
                    "Display density",
                    ["Comfortable", "Compact"],
                    key="qi_display_density",
                    help="Adjust workspace spacing.",
                )

                st.toggle(
                    "Show research guidance",
                    key="qi_show_research_notes",
                    help="Show contextual explanations beside research tools.",
                )

                st.toggle(
                    "Reduce animations",
                    key="qi_reduce_motion",
                    help="Minimize decorative motion.",
                )

                st.divider()
                st.markdown("**External market displays**")

                st.toggle(
                    "Automatically load TradingView panels",
                    key="qi_external_charts",
                    on_change=record_external_panel_choice,
                    help="Allow provider-hosted panels during this session.",
                )

                st.caption(
                    "When enabled, TradingView receives connection "
                    "information such as your IP address and selected "
                    "symbol. Turning this off prevents future panel loads "
                    "but cannot undo previous requests."
                )

                st.markdown(
                    "[TradingView privacy policy]"
                    "(https://www.tradingview.com/privacy-policy/)"
                )

                st.divider()

                st.button(
                    "Reset preferences",
                    key="qi_reset_workspace_preferences",
                    use_container_width=True,
                    on_click=reset_workspace_preferences,
                )

                st.caption(
                    "Preferences apply to this session. "
                    "They do not change account access."
                )

            with workspace:
                st.markdown(
                    '<div class="qi-settings-about">'
                    '<div class="qi-settings-about-name">'
                    'Quant Intelligence</div>'
                    '<div class="qi-settings-about-description">'
                    'Research, quantitative analysis and financial education'
                    '</div></div>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    '<div class="qi-settings-info-grid">'
                    '<div class="qi-settings-info-card">'
                    '<span>MARKET DISPLAYS</span>'
                    '<strong>TradingView</strong>'
                    '<small>Provider-hosted information</small>'
                    '</div>'
                    '<div class="qi-settings-info-card">'
                    '<span>QUANTITATIVE MODELS</span>'
                    '<strong>Independent</strong>'
                    '<small>Hypothetical calculations</small>'
                    '</div></div>',
                    unsafe_allow_html=True,
                )

                st.markdown("**Privacy & access**")
                st.caption(
                    "Viewer access is controlled through Streamlit "
                    "Community Cloud sharing settings, not this menu. "
                    "The application is accessible only to the accounts "
                    "permitted by its current hosting configuration."
                )

                if st.button(
                    "Legal, privacy & methodology",
                    key="qi_open_legal_settings",
                    use_container_width=True,
                ):
                    st.session_state["_navigation_request"] = (
                        "📄 Legal & Privacy"
                    )
                    st.rerun()

                with st.expander(
                    "Advanced diagnostics", expanded=False
                ):
                    from dashboard.build_info import build_info

                    info = build_info()
                    st.caption(
                        "Source revision: "
                        + str(info.get("source_sha", "unknown"))[:12]
                    )

                    st.json(info)

                    st.caption(
                        "These details describe the running software. "
                        "They are not independent deployment "
                        "verification or evidence of provider permissions."
                    )


    st.markdown(
        """
        <style>
        .qi-settings-title {
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -0.035em;
            color: #FFFFFF;
            margin: 0 0 4px;
        }
        .qi-settings-subtitle {
            color: #A9B8D2;
            font-size: 0.84rem;
            margin-bottom: 16px;
        }
        .qi-settings-about {
            padding: 19px;
            margin: 8px 0 16px;
            border: 1px solid #344766;
            border-radius: 15px;
            background: linear-gradient(
                125deg, #192741, #11192D
            );
        }
        .qi-settings-about-name {
            color: #FFFFFF;
            font-size: 1.28rem;
            font-weight: 800;
            letter-spacing: -0.035em;
        }
        .qi-settings-about-description {
            color: #BCCAE0;
            font-size: 0.82rem;
            line-height: 1.6;
            margin-top: 5px;
        }
        .qi-settings-info-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        .qi-settings-info-card {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding: 15px;
            border: 1px solid #30405D;
            border-radius: 13px;
            background: #141F35;
            min-width: 0;
        }
        .qi-settings-info-card span {
            color: #FF91C6;
            font-size: 0.62rem;
            font-weight: 750;
            letter-spacing: 0.07em;
        }
        .qi-settings-info-card strong {
            color: #FFFFFF;
            font-size: 1rem;
        }
        .qi-settings-info-card small {
            color: #9FACBF;
            font-size: 0.72rem;
            line-height: 1.45;
        }
        @media (max-width: 500px) {
            .qi-settings-info-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

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
