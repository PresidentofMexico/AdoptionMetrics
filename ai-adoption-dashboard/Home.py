"""
AI Adoption Dashboard - Main Entry Point

This is the home page of the AI adoption metrics dashboard.
"""

import streamlit as st

st.set_page_config(
    page_title="AI Adoption Dashboard",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI Adoption Dashboard")
st.markdown("Welcome to the AI Adoption Metrics Dashboard")

st.markdown("""
### Overview
This dashboard provides insights into AI adoption metrics across your organization.

Use the sidebar to navigate to different sections:
- 📈 **Trends**: View adoption trends over time
- 👥 **User Deep Dive**: Analyze individual user behavior
""")
