import streamlit as st
import pandas as pd
import plotly.express as px
from Home import load_and_process_data

st.set_page_config(page_title="GenAI App Store", page_icon="🤖", layout="wide")

st.title("🤖 GenAI App Store Intelligence")
st.markdown("Discover which internal agents and Custom GPTs are actually delivering value.")

try:
    df, _, _ = load_and_process_data()
    if df.empty: st.stop()
except:
    st.stop()

# Filter to only rows that represent Agentic usage
# BlueFlame is an agent. Custom GPTs are agents.
agent_mask = (
    (df['Tool'] == 'BlueFlame') | 
    (df['Feature'] == 'GPT Messages')  # Use exact match or specific inclusion
)
agent_df = df[agent_mask].copy()

if agent_df.empty:
    st.warning("No Agent or Custom GPT usage found in the data.")
    st.stop()

# --- 1. High Level Stats ---
bf_vol = df[df['Tool'] == 'BlueFlame']['Count'].sum()
gpt_vol = df[df['Feature'].str.contains('GPT', case=False, na=False)]['Count'].sum()

c1, c2, c3 = st.columns(3)
c1.metric("BlueFlame Volume", f"{bf_vol:,.0f}", help="Total messages sent to BlueFlame")
c2.metric("Custom GPT Volume", f"{gpt_vol:,.0f}", help="Total messages sent to Custom GPTs")
c3.metric("Agent Adoption Rate", f"{(bf_vol + gpt_vol) / df['Count'].sum():.1%}", help="% of total AI traffic going to Agents")

st.divider()

# --- 2. Comparison Chart ---
c_chart, c_dept = st.columns([2, 1])

with c_chart:
    st.subheader("Agent Wars: BlueFlame vs. Custom GPTs")
    
    # Group by month and type
   agent_df['Agent_Type'] = agent_df['Tool'].apply(
    lambda x: 'BlueFlame' if x == 'BlueFlame' else 'Custom GPTs'
)
    
    trend = agent_df.groupby([pd.Grouper(key='Date', freq='M'), 'Agent_Type'])['Count'].sum().reset_index()
    
    fig_trend = px.bar(
        trend, 
        x='Date', 
        y='Count', 
        color='Agent_Type', 
        barmode='group',
        color_discrete_map={'BlueFlame': '#2563EB', 'Custom GPTs': '#10a37f'},
        title="Monthly Volume by Agent Type"
    )
    fig_trend.update_layout(plot_bgcolor="white", hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)

with c_dept:
    st.subheader("Top Departments")
    dept_counts = agent_df.groupby('Department')['Count'].sum().nlargest(10).reset_index()
    
    fig_dept = px.pie(
        dept_counts, 
        names='Department', 
        values='Count', 
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig_dept.update_layout(showlegend=False)
    st.plotly_chart(fig_dept, use_container_width=True)

# --- 3. Raw Data View ---
with st.expander("View Agent Usage Details"):
    st.dataframe(agent_df.sort_values('Date', ascending=False))
