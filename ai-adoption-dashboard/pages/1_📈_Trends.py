import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.data_processor import load_data

st.set_page_config(page_title="Trends & Insights", page_icon="📈", layout="wide")

# --- Data Loading ---
try:
    df, _, _ = load_data()
    if df.empty: st.warning("No data found."); st.stop()
except Exception as e:
    st.error(f"Error: {e}"); st.stop()

st.title("📈 Adoption Trends & Insights")
st.markdown("Visualizing the velocity and trajectory of AI adoption.")

# --- 1. TIME TRAVEL (Animated) ---
st.subheader("⏳ The Evolution of Adoption (Press Play ▶️)")
st.caption("Watch how departments mature over time. Bubble Size = Monthly Volume.")

ani_df = df.groupby([pd.Grouper(key='Date', freq='M'), 'Department']).agg(
    Active_Users=('Email', 'nunique'),
    Monthly_Volume=('Count', 'sum'),
    Unique_Features=('Feature', 'nunique')
).reset_index()

ani_df['Date_Str'] = ani_df['Date'].dt.strftime('%Y-%m')
ani_df = ani_df.sort_values('Date')

max_users = ani_df['Active_Users'].max() * 1.1
max_vol = ani_df['Monthly_Volume'].max() * 1.1

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
fig_ani.update_layout(
    plot_bgcolor="white", 
    height=600,
    xaxis=dict(showgrid=True, gridcolor='#f0f0f0'),
    yaxis=dict(showgrid=True, gridcolor='#f0f0f0')
)

st.plotly_chart(fig_ani, use_container_width=True)

st.divider()

# --- 2. GROWTH TRAJECTORIES ---
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("🏁 Department Growth Race")
    st.caption("Cumulative message volume over time (Top 10 Departments)")
    
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
    fig_race.update_layout(hovermode="x unified", plot_bgcolor="white", height=450)
    st.plotly_chart(fig_race, use_container_width=True)

with c2:
    st.subheader("🔥 Intensity Heatmap")
    st.caption("Volume intensity by Department & Month")
    
    heatmap_data = daily_dept.pivot(index="Department", columns="Date", values="Count").fillna(0)
    heatmap_data['Total'] = heatmap_data.sum(axis=1)
    heatmap_data = heatmap_data.sort_values('Total', ascending=True).drop(columns='Total').tail(15)
    
    x_labels = [d.strftime('%b %y') for d in heatmap_data.columns]
    
    fig_heat = px.imshow(
        heatmap_data,
        labels=dict(x="Month", y="Department", color="Volume"),
        x=x_labels,
        aspect="auto",
        color_continuous_scale="Blues"
    )
    fig_heat.update_layout(height=450)
    st.plotly_chart(fig_heat, use_container_width=True)

# --- 3. PLATFORM SPLIT ---
st.divider()
st.subheader("🛠️ Platform Dominance Trend")

monthly_tool = df.groupby([pd.Grouper(key='Date', freq='M'), 'Tool'])['Count'].sum().reset_index()
pivot_tool = monthly_tool.pivot(index='Date', columns='Tool', values='Count').fillna(0).reset_index()

pivot_tool['Total'] = pivot_tool.get('ChatGPT', 0) + pivot_tool.get('BlueFlame', 0)
pivot_tool['ChatGPT %'] = (pivot_tool.get('ChatGPT', 0) / pivot_tool['Total']) * 100
pivot_tool['BlueFlame %'] = (pivot_tool.get('BlueFlame', 0) / pivot_tool['Total']) * 100

fig_share = go.Figure()
fig_share.add_trace(go.Bar(
    x=pivot_tool['Date'], 
    y=pivot_tool.get('ChatGPT %', [0]*len(pivot_tool)), 
    name='ChatGPT', 
    marker_color='#10a37f'
))
fig_share.add_trace(go.Bar(
    x=pivot_tool['Date'], 
    y=pivot_tool.get('BlueFlame %', [0]*len(pivot_tool)), 
    name='BlueFlame', 
    marker_color='#2563EB'
))

fig_share.update_layout(
    barmode='stack', 
    title="Market Share: ChatGPT vs BlueFlame (Monthly)",
    yaxis_title="Share of Volume (%)",
    hovermode="x unified",
    plot_bgcolor="white"
)
st.plotly_chart(fig_share, use_container_width=True)
