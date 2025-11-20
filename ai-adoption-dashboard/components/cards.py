"""
Metric Cards Module

Reusable card components for displaying metrics like ROI, User Count, etc.
"""

import streamlit as st
from typing import Optional


def metric_card(title: str, value: str, delta: Optional[str] = None, 
                delta_color: str = "normal") -> None:
    """
    Display a metric card with title, value, and optional delta.
    
    Args:
        title: Card title
        value: Main metric value to display
        delta: Optional change indicator
        delta_color: Color for delta ("normal", "inverse", "off")
    """
    st.metric(label=title, value=value, delta=delta, delta_color=delta_color)


def roi_card(roi_value: float, currency_saved: float) -> None:
    """
    Display ROI metric card with percentage and currency saved.
    
    Args:
        roi_value: ROI percentage
        currency_saved: Amount saved in currency
    """
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            label="📈 Return on Investment",
            value=f"{roi_value:.1f}%",
            delta="Positive" if roi_value > 0 else "Negative"
        )
    
    with col2:
        st.metric(
            label="💰 Total Savings",
            value=f"${currency_saved:,.2f}"
        )


def user_count_card(total_users: int, active_users: int, 
                   adoption_rate: float) -> None:
    """
    Display user count metrics.
    
    Args:
        total_users: Total number of users
        active_users: Number of active users
        adoption_rate: Adoption rate percentage
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="👥 Total Users",
            value=f"{total_users:,}"
        )
    
    with col2:
        st.metric(
            label="✅ Active Users",
            value=f"{active_users:,}"
        )
    
    with col3:
        st.metric(
            label="📊 Adoption Rate",
            value=f"{adoption_rate:.1f}%"
        )


def department_card(department: str, user_count: int, 
                   adoption_rate: float) -> None:
    """
    Display department-specific metrics.
    
    Args:
        department: Department name
        user_count: Number of users in department
        adoption_rate: Department adoption rate
    """
    st.subheader(department)
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(label="Users", value=f"{user_count:,}")
    
    with col2:
        st.metric(label="Adoption", value=f"{adoption_rate:.1f}%")
