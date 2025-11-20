import streamlit as st
import plotly.express as px
import pandas as pd
from Home import load_and_process_data
from src.metrics import MetricsEngine

st.set_page_config(page_title="ROI & Strategy", page_icon="💎", layout="wide")

# --- Data Loading ---
try:
    df, _, _ = load_and_process_data()
    if df.empty: st.warning("No data found."); st.stop()
except Exception as e:
    st.error(f"Error: {e}"); st.stop()

st.title("💎 ROI & Business Impact")
st.markdown("Quantifying the value of AI acceleration with adjustable sensitivity.")

# --- Interactive Assumptions ---
with st.expander("🧮 ROI Configuration Model", expanded=True):
    col_assumptions, col_haircut = st.columns([2, 1])
    
    with col_assumptions:
        st.markdown("**1. Base Assumptions (Minutes Saved per Task)**")
        c1, c2, c3, c4 = st.columns(4)
        hourly_rate = c1.number_input("Avg Hourly Cost ($)", value=125, step=25)
        time_chat = c2.number_input("Chat (Simple)", value=5, help="Quick questions, rewrites")
        time_research = c3.number_input("Research (Complex)", value=15, help="BlueFlame / Deep Research")
        time_analysis = c4.number_input("Data Analysis", value=30, help="Coding / Excel / Visualization")

    with col_haircut:
        st.markdown("**2. The 'Reality Check'**")
        discount_rate = st.slider(
            "Discount Factor (%)", 
            min_value=0, 
            max_value=90, 
            value=50,
            step=10,
            help="Reduces total value to account for trial-and-error, hallucinations, and learning curves. 50% means only half of interactions yielded final value."
        )
        st.caption(f"Retaining **{100-discount_rate}%** of calculated value.")
    
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
roi_df = engine.calculate_roi(hourly_rate, assumptions, discount_rate=discount_rate/100)

# --- Top Level Impact ---
total_hours = roi_df['Hours_Saved'].sum()
total_value = roi_df['Dollar_Value'].sum()
equivalent_fte = total_hours / (40 * 52) 

# Visualization of the "Haircut"
st.divider()
m1, m2, m3 = st.columns(3)

m1.metric(
    "📉 Net Hours Reclaimed", 
    f"{total_hours:,.0f}", 
    delta=f"-{discount_rate}% adjustment applied", 
    delta_color="inverse"
)
m2.metric(
    "💰 Net Value Created", 
    f"${total_value:,.0f}",
    help=f"Value after applying {discount_rate}% discount factor"
)
m3.metric(
    "🤖 Digital FTE Capacity", 
    f"{equivalent_fte:.1f} FTEs", 
    help="Equivalent annual work-hours released back to the firm"
)

st.divider()

# --- Charts ---
c1, c2 = st.columns([1, 1])

with c1:
    st.markdown("#### 📊 Value Distribution by Platform")
    val_by_tool = roi_df.groupby("Tool")["Dollar_Value"].sum().reset_index()
    fig_bar = px.bar(
        val_by_tool, 
        x="Tool", 
        y="Dollar_Value", 
        color="Tool", 
        text_auto='.2s',
        color_discrete_map={'ChatGPT': '#10a37f', 'BlueFlame': '#2563EB'}
    )
    fig_bar.update_layout(yaxis_title="Net Dollar Value")
    st.plotly_chart(fig_bar, use_container_width=True)

with c2:
    st.markdown("#### 🏆 Top Departments by Value Creation")
    val_by_dept = roi_df.groupby("Department")["Dollar_Value"].sum().sort_values(ascending=True).tail(10).reset_index()
    fig_hbar = px.bar(
        val_by_dept, 
        y="Department", 
        x="Dollar_Value", 
        orientation='h', 
        text_auto='.2s', 
        color="Dollar_Value",
        color_continuous_scale="Greens"
    )
    fig_hbar.update_layout(xaxis_title="Net Dollar Value", showlegend=False)
    st.plotly_chart(fig_hbar, use_container_width=True)

# --- Capability Matrix ---
st.divider()
st.subheader("🎯 Department Capability Matrix")
st.markdown("Strategic Leaders vs. Emerging Adopters (Bubble Size = Active Headcount)")

quad_data = engine.get_efficiency_quadrant()

fig_quad = px.scatter(
    quad_data,
    x="Total_Volume",
    y="Unique_Features",
    size="Active_Users",
    color="Department",
    hover_name="Department",
    text="Department",
    labels={"Total_Volume": "Usage Intensity (Total Messages)", "Unique_Features": "Feature Sophistication"}
)

med_vol = quad_data['Total_Volume'].median()
med_feat = quad_data['Unique_Features'].median()

fig_quad.add_vline(x=med_vol, line_dash="dash", line_color="grey", opacity=0.5, annotation_text="Avg Vol")
fig_quad.add_hline(y=med_feat, line_dash="dash", line_color="grey", opacity=0.5, annotation_text="Avg Sophistication")
fig_quad.update_traces(textposition='top center')
fig_quad.update_layout(height=600, showlegend=False)

st.plotly_chart(fig_quad, use_container_width=True)
