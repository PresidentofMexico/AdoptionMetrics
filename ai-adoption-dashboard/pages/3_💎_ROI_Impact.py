import streamlit as st
import plotly.express as px
import pandas as pd
from Home import load_and_process_data # Import data loader from main app
from src.metrics import MetricsEngine

st.set_page_config(page_title="ROI & Strategy", page_icon="💎", layout="wide")

# --- Data Loading ---
try:
    df, _, _ = load_and_process_data()
    if df.empty: st.warning("No data found."); st.stop()
except Exception as e:
    st.error(f"Error: {e}"); st.stop()

st.title("💎 ROI & Business Impact")
st.markdown("Quantifying the value of AI acceleration across the enterprise.")

# --- Interactive Assumptions ---
with st.expander("🧮 Adjust ROI Assumptions", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    hourly_rate = c1.number_input("Avg Hourly Cost ($)", value=125, step=25)
    time_chat = c2.number_input("Mins Saved (Chat)", value=5)
    time_research = c3.number_input("Mins Saved (Research)", value=15)
    time_analysis = c4.number_input("Mins Saved (Data)", value=30)
    
    assumptions = {
        'Standard Chat': time_chat,
        'ChatGPT Messages': time_chat,
        'Investment Research': time_research,
        'BlueFlame Messages': time_research,
        'Advanced Data Analysis': time_analysis,
        'Tool Messages': time_analysis
    }

# --- Run Calculations ---
engine = MetricsEngine(df)
roi_df = engine.calculate_roi(hourly_rate, assumptions)

# --- Top Level Impact ---
total_hours = roi_df['Hours_Saved'].sum()
total_value = roi_df['Dollar_Value'].sum()
equivalent_fte = total_hours / (40 * 52) # 40hr weeks * 52 weeks

m1, m2, m3 = st.columns(3)
m1.metric("📉 Hours Reclaimed", f"{total_hours:,.0f} hrs")
m2.metric("💰 Est. Value Created", f"${total_value:,.0f}")
m3.metric("🤖 Digital FTEs Added", f"{equivalent_fte:.1f} FTEs", help="Equivalent Full-Time Employees based on hours saved")

st.divider()

# --- The "Magic Quadrant" Chart ---
st.subheader("🎯 Department Capability Matrix")
st.markdown("Identifies **Strategic Leaders** (High Volume + High Diversity) vs **Specialists**.")

quad_data = engine.get_efficiency_quadrant()

fig_quad = px.scatter(
    quad_data,
    x="Total_Volume",
    y="Unique_Features",
    size="Active_Users",
    color="Department",
    hover_name="Department",
    text="Department",
    title="Volume vs. Sophistication (Bubble Size = Headcount)",
    labels={"Total_Volume": "Usage Intensity", "Unique_Features": "Feature Sophistication"}
)

# Add quadrant lines
med_vol = quad_data['Total_Volume'].median()
med_feat = quad_data['Unique_Features'].median()

fig_quad.add_vline(x=med_vol, line_dash="dash", line_color="grey", opacity=0.5)
fig_quad.add_hline(y=med_feat, line_dash="dash", line_color="grey", opacity=0.5)
fig_quad.update_traces(textposition='top center')
fig_quad.update_layout(height=600, showlegend=False)

st.plotly_chart(fig_quad, use_container_width=True)

# --- Impact Breakdown ---
c1, c2 = st.columns([1, 1])
with c1:
    st.markdown("#### Value by Platform")
    # Aggregate value by tool
    val_by_tool = roi_df.groupby("Tool")["Dollar_Value"].sum().reset_index()
    fig_bar = px.bar(val_by_tool, x="Tool", y="Dollar_Value", color="Tool", text_auto='.2s')
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.markdown("#### Value by Department (Top 10)")
    val_by_dept = roi_df.groupby("Department")["Dollar_Value"].sum().sort_values(ascending=True).tail(10).reset_index()
    fig_hbar = px.bar(val_by_dept, y="Department", x="Dollar_Value", orientation='h', text_auto='.2s', color="Dollar_Value")
    st.plotly_chart(fig_hbar, use_container_width=True)
