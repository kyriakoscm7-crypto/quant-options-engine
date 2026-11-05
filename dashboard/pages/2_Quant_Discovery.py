"""Compatibility entry for the evidence-based Discover workspace.

Historical database/ranking UI remains in Git history, never in hosted routing.
"""
import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.demo_showcase import render_demo_research_page  # noqa: E402

render_demo_research_page("💎 Quant Discovery")
st.stop()
