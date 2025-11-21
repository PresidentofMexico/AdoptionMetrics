import sys
import os
import streamlit as st
import pandas as pd

# --- PATH FIX: FORCE PYTHON TO SEE ROOT FOLDER ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
# -------------------------------------------------

from src.data_processor import load_and_process_data
from components.cards import create_kpi_card

st.set_page_config(
    page_title="Adoption Metrics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI Adoption Executive Summary")
st.markdown("Overview of GenAI usage across the organization.")

# --- LOAD DATA ---
try:
    # This now matches the 3 return values from the processor
    df, total_users, total_vol = load_and_process_data()
except Exception as e:
    st.error(f"Critical Error Loading Data: {e}")
    st.stop()

if df.empty:
    st.warning("No data found in 'data/' folder. Please add CSV files.")
    st.stop()

# --- KPI CARDS ---
c1, c2, c3, c4 = st.columns(4)

with c1:
    create_kpi_card("Active Users", total_users, "Total unique emails")

with c2:
    create_kpi_card("Total Volume", f"{total_vol:,.0f}", "Messages sent")

with c3:
    # Calculate simple MoM growth
    current_month = df['Date'].max()
    prev_month = current_month - pd.DateOffset(months=1)
    
    curr_vol = df[df['Date'].dt.to_period('M') == current_month.to_period('M')]['Count'].sum()
    prev_vol = df[df['Date'].dt.to_period('M') == prev_month.to_period('M')]['Count'].sum()
    
    if prev_vol > 0:
        delta = ((curr_vol - prev_vol) / prev_vol * 100)
        create_kpi_card("Monthly Volume", f"{curr_vol:,.0f}", f"{delta:+.1f}% vs last month")
    else:
        create_kpi_card("Monthly Volume", f"{curr_vol:,.0f}", "No prior month data")

with c4:
    if 'Department' in df.columns:
        top_dept = df.groupby('Department')['Count'].sum().idxmax()
        create_kpi_card("Top Dept", top_dept, "By volume")
    else:
        create_kpi_card("Top Dept", "N/A", "No Data")

st.divider()

# --- RECENT ACTIVITY PREVIEW ---
st.subheader("Recent Activity Preview")

# Select only relevant columns for the preview to keep it clean
cols_to_show = ['Date', 'tool', 'user_email', 'Department']
available_cols = [c for c in cols_to_show if c in df.columns]

st.dataframe(
    df.sort_values('Date', ascending=False)[available_cols].head(10),
    use_container_width=True,
    hide_index=True
)
