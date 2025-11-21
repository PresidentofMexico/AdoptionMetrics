import streamlit as st
import pandas as pd
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
    # Calculate simple MoM growth if possible
    current_month = df['Date'].max()
    prev_month = current_month - pd.DateOffset(months=1)
    
    curr_vol = df[df['Date'].dt.to_period('M') == current_month.to_period('M')]['Count'].sum()
    prev_vol = df[df['Date'].dt.to_period('M') == prev_month.to_period('M')]['Count'].sum()
    
    delta = ((curr_vol - prev_vol) / prev_vol * 100) if prev_vol > 0 else 0
    create_kpi_card("Monthly Volume", f"{curr_vol:,.0f}", f"{delta:+.1f}% vs last month")

with c4:
    top_dept = df.groupby('Department')['Count'].sum().idxmax()
    create_kpi_card("Top Dept", top_dept, "By volume")

st.divider()

# --- RECENT ACTIVITY PREVIEW ---
st.subheader("Recent Activity Preview")
st.dataframe(
    df.sort_values('Date', ascending=False).head(10),
    use_container_width=True,
    hide_index=True
)
