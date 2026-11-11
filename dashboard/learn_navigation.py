"""First-party scroll restoration for Learn chapter transitions.

No user-supplied JS. The script is emitted only after navigation changes
to avoid resetting scroll while a reader is studying a page.
"""
from __future__ import annotations

import streamlit as st


def request_top() -> None:
    st.session_state["qi_learn_scroll_serial"] = (
        st.session_state.get("qi_learn_scroll_serial", 0) + 1
    )


def scroll_to_top_after_navigation() -> None:
    serial = st.session_state.get("qi_learn_scroll_serial", 0)
    last = st.session_state.get("qi_learn_last_scrolled_serial", 0)
    if not serial or serial == last:
        return
    st.session_state["qi_learn_last_scrolled_serial"] = serial
    # Streamlit 1.66 supports first-party st.html JS. This is a constant,
    # local script: no external imports, user text, eval or navigation URLs.
    st.html(
        f'<div data-qi-learn-scroll="{serial}" aria-hidden="true"></div>'
        '<script>'
        '(function(){'
        'function top(){'
        'window.scrollTo(0,0);'
        'document.documentElement.scrollTop=0;'
        'for(const el of document.querySelectorAll('
        '"[data-testid=stAppViewContainer], [data-testid=stMain], section.main"'
        ')){if(el.scrollTop>0){el.scrollTo(0,0);}}'
        '}'
        'requestAnimationFrame(function(){top();requestAnimationFrame(top);});'
        'setTimeout(top,80);'
        '})();'
        '</script>',
        unsafe_allow_javascript=True,
    )
