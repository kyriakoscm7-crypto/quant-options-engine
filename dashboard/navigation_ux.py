"""Optional small-screen navigation polish for Quant Intelligence.

Gracefully degrades to Streamlit's native mobile sidebar on older versions.
No external JavaScript, telemetry, user data, or network requests.
"""
from __future__ import annotations

import inspect

import streamlit as st

_NAV_STYLE = """
<style>
@media(max-width:768px){
  [data-testid="stSidebar"]{max-width:min(92vw,350px)!important}
  [data-testid="stMain"] .block-container{padding-left:1rem!important;padding-right:1rem!important;padding-top:1.2rem!important}
  .st-key-qi_learn_page h1{font-size:clamp(2rem,7vw,3rem)!important;line-height:1.12}
  .st-key-qi_learn_page h2{font-size:clamp(1.35rem,5vw,2rem)!important}
}
.st-key-qi_learn_page h1{font-size:clamp(2.25rem,4vw,3.45rem)!important;line-height:1.12;letter-spacing:-.045em}
.st-key-qi_learn_page h2{font-size:clamp(1.45rem,2.7vw,2.2rem)!important;line-height:1.2}
.st-key-qi_learn_page [data-testid="stMarkdownContainer"] p{line-height:1.65}
</style>
"""

_NAV_JS = """
<script>
(() => {
 if(window.__qiNavigationUxV3)return;
 window.__qiNavigationUxV3=true;
 document.addEventListener('click',event=>{
  const el=event.target;
  if(!(el instanceof Element))return;
  const button=el.closest('section[data-testid="stSidebar"] .st-key-qi_navigation button');
  if(!button || button.disabled)return;
  const main=document.querySelector('[data-testid="stMain"]');
  // Only navigation clicks reset the reading position; never slider changes.
  if(main)main.scrollTo({top:0,behavior:'auto'});
  window.scrollTo({top:0,behavior:'auto'});
  if(window.matchMedia('(max-width: 768px)').matches){
   // Native Streamlit collapse control: close after choosing a sidebar route.
   setTimeout(()=>{
    const sidebar=document.querySelector('[data-testid="stSidebar"]');
    if(sidebar?.getAttribute('aria-expanded')!=='true')return;
    const toggle=document.querySelector('[data-testid="stSidebarCollapseButton"] button');
    if(toggle && !toggle.contains(button))toggle.click();
   },15);
  }
 },true);
})();
</script>
"""


def render_navigation_ux() -> None:
    """Render responsive styling and optional mobile menu interaction."""
    st.html(_NAV_STYLE)
    if "unsafe_allow_javascript" in inspect.signature(st.html).parameters:
        st.html(_NAV_JS, unsafe_allow_javascript=True)
