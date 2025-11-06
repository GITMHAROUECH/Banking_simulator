"""
Page Liquidité (I7a).
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

st.set_page_config(page_title="Liquidité", page_icon="💧", layout="wide", initial_sidebar_state="expanded")

# Import existing UI function
from app.streamlit_app import show_liquidity_page

# Call the existing function
show_liquidity_page()
