"""
Metric Cards Module

Reusable card components for displaying metrics.
"""

import streamlit as st
from typing import Optional

def styled_metric_card(label: str, value: str, prefix: str = "", suffix: str = ""):
    """
    Renders a custom styled metric card using HTML/CSS.
    Based on the 'executive overview' style.
    """
    st.markdown(f"""
    <div style="
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    ">
        <div style="
            font-size: 13px; 
            color: #64748B; 
            font-weight: 700; 
            text-transform: uppercase; 
            letter-spacing: 1px;
        ">{label}</div>
        <div style="
            font-size: 36px; 
            font-weight: 800; 
            color: #1E3A8A;
        ">{prefix}{value}{suffix}</div>
    </div>
    """, unsafe_allow_html=True)

def metric_card(title: str, value: str, delta: Optional[str] = None, 
                delta_color: str = "normal") -> None:
    """Standard Streamlit metric card"""
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)

def roi_card(roi_value: float, currency_saved: float) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="📈 Return on Investment", value=f"{roi_value:.1f}%", delta="Positive" if roi_value > 0 else "Negative")
    with col2:
        st.metric(label="💰 Total Savings", value=f"${currency_saved:,.2f}")

def user_count_card(total_users: int, active_users: int, adoption_rate: float) -> None:
    col1, col2, col3 = st.columns(3)
    with col1: st.metric(label="👥 Total Users", value=f"{total_users:,}")
    with col2: st.metric(label="✅ Active Users", value=f"{active_users:,}")
    with col3: st.metric(label="📊 Adoption Rate", value=f"{adoption_rate:.1f}%")
