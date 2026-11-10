"""Offline browser fixture for the standalone Quant Lab volatility module."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from dashboard.volatility_intelligence import render_volatility_lab

st.set_page_config(layout="wide")
render_volatility_lab()
