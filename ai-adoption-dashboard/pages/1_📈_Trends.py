import sys
import os
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# --- PATH FIX: FORCE PYTHON TO SEE ROOT FOLDER ---
# Use '..' to go up one level from 'pages/' to root
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(root_dir)
# -------------------------------------------------

from src.data_processor import load_and_process_data
from src.metrics import MetricsEngine

st.set_page_config(page_title="Trends & Insights", page_icon="📈", layout="wide")

# --- Data Loading ---
try:
    df, _, _ = load_and_process_data()
    if df.empty: st.warning("No data found."); st.stop()
except Exception as e:
    st.error(f"Error: {e}"); st.stop()

st.title("📈 Adoption Trends & Insights")
st.markdown("Visualizing the velocity and trajectory of AI adoption.")

# --- 1. TIME TRAVEL (Animated) ---
st.subheader("⏳ The Evolution of Adoption (Press Play ▶️)")
st.caption("Watch how departments mature over time. Bubble Size = Monthly Volume.")

# Prepare Data for Animation
ani_df = df.groupby([pd.Grouper(key='Date', freq='M'), 'Department']).agg(
    Active_Users=('Email', 'nunique'),
    Monthly_Volume=('Count', 'sum'),
    Unique_Features=('Feature', 'nunique')
).reset_index()

# Format Date for Animation Frame
ani_df['Date_Str'] = ani_df['Date'].dt.strftime('%Y-%m')
ani_df = ani_df.sort_values('Date')

max_users = ani_df['Active_Users'].max() * 1.1 if not ani_df.empty else 10
max_vol = ani_df['Monthly_Volume'].max() * 1.1 if not ani_df.empty else 100

fig_ani = px.scatter(
    ani_df,
    x="Active_Users",
    y="Monthly_Volume",
    animation_frame="Date_Str",
    animation_group="Department",
    size="Monthly_Volume",
    color="Department",
    hover_name="Department",
    range_x=[0, max_users],
    range_y=[0, max_vol],
    title="Monthly Evolution: Headcount vs. Volume",
    labels={"Active_Users": "Active Staff", "Monthly_Volume": "Messages Sent"}
)

fig_ani.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 800
fig_ani.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color='DarkSlateGrey')))
fig_ani.update_layout(height=600, plot_bgcolor="white")
st.plotly_chart(fig_ani, use_container_width=True)

st.divider()

# --- 2. GROWTH TRAJECTORIES ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("🏁 Department Growth Race")
    
    daily_dept = df.groupby([pd.Grouper(key='Date', freq='M'), 'Department'])['Count'].sum().reset_index()
    top_depts = df.groupby('Department')['Count'].sum().nlargest(10).index
    filtered_race = daily_dept[daily_dept['Department'].isin(top_depts)].copy()
    
    filtered_race = filtered_race.sort_values(['Department', 'Date'])
    filtered_race['Cumulative_Volume'] = filtered_race.groupby('Department')['Count'].cumsum()
    
    fig_race = px.line(
        filtered_race, 
        x="Date", 
        y="Cumulative_Volume", 
        color="Department",
        markers=True,
        title="Cumulative Usage Volume"
    )
    fig_race.update_layout(plot_bgcolor="white", height=450)
    st.plotly_chart(fig_race, use_container_width=True)

with c2:
    st.subheader("🔥 Intensity Heatmap")
    
    heatmap_data = daily_dept.pivot(index="Department", columns="Date", values="Count").fillna(0)
    heatmap_data['Total'] = heatmap_data.sum(axis=1)
    heatmap_data = heatmap_data.sort_values('Total', ascending=True).drop(columns='Total').tail(15)
    
    x_labels = [d.strftime('%b %y') for d in heatmap_data.columns]
    
    fig_heat = px.imshow(
        heatmap_data,
        x=x_labels,
        aspect="auto",
        color_continuous_scale="Blues"
    )
    fig_heat.update_layout(height=450)
    st.plotly_chart(fig_heat, use_container_width=True)

# --- 3. RETENTION ANALYSIS ---
st.divider()
st.subheader("🧲 User Retention Analysis")

engine = MetricsEngine(df)
retention_df = engine.get_retention_matrix()

if not retention_df.empty:
    fig_ret = px.line(
        retention_df, 
        x='Month', 
        y='Retention_Rate',
        markers=True,
        title="Global Retention Rate (%)",
        labels={'Retention_Rate': 'Retention %'}
    )
    fig_ret.update_traces(line_color='#EF4444', line_width=3)
    fig_ret.update_layout(yaxis_range=[0, 110], plot_bgcolor="white")
    
    st.plotly_chart(fig_ret, use_container_width=True)
else:
    st.info("Not enough data for retention.")
