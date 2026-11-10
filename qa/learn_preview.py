"""Self-contained visual browser fixture for Learn 2.0, with production CSS."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from dashboard.learn_page import render_learn_page

st.set_page_config(page_title="Quant Intelligence Learn preview", layout="wide")
st.html("<style>" + Path("dashboard/premium_theme.css").read_text() + "</style>")
render_learn_page()
