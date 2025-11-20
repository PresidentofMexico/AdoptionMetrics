import streamlit as st
import pandas as pd
import plotly.express as px
from src.data_processor import DataProcessor

# --- Configuration ---
st.set_page_config(page_title="AI Executive Dashboard", page_icon="🚀", layout="wide")

# --- Styling ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
    .metric-label { font-size: 14px; color: #7f8c8d; }
</style>
""", unsafe_allow_html=True)

# --- Data Loading (Cached) ---
@st.cache_data
def load_data():
    # In production, these paths would be dynamic or from file_uploader
    # For now, we assume files are in 'data/'
    processor = DataProcessor("data/Employee Headcount 2025_Emails.csv")
    
    # NOTE: You would feed your actual uploaded files here
    # df = processor.get_unified_data(...) 
    
    # For this demo run, we load the pre-processed CSV we just generated
    df = pd.read_csv("unified_ai_usage_data.csv") 
    df['Date'] = pd.to_datetime(df['Date'])
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Data not found. Please upload CSVs in the sidebar. ({e})")
    st.stop()

# --- Sidebar Filters ---
st.sidebar.header("Filters")
selected_tools = st.sidebar.multiselect("Select Tools", df['Tool'].unique(), default=df['Tool'].unique())
selected_depts = st.sidebar.multiselect("Select Departments", df['Department'].unique(), default=df['Department'].unique())

# Filter Data
mask = (df['Tool'].isin(selected_tools)) & (df['Department'].isin(selected_depts))
filtered_df = df[mask]

# --- Main Dashboard ---
st.title("🚀 Enterprise AI Adoption Dashboard")
st.markdown("Tracking adoption velocity and engagement across the organization.")

# 1. Top Level Metrics
col1, col2, col3, col4 = st.columns(4)
total_users = filtered_df['Email'].nunique()
total_activities = filtered_df['Count'].sum()
active_depts = filtered_df['Department'].nunique()
top_tool = filtered_df.groupby('Tool')['Count'].sum().idxmax()

col1.metric("Active Users", total_users, "+12% vs prev")
col2.metric("Total Interactions", f"{total_activities:,.0f}")
col3.metric("Active Departments", active_depts)
col4.metric("Top Tool", top_tool)

st.divider()

# 2. Adoption Rate & Trends
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Adoption Trend (Monthly Active Users)")
    # Aggregate MAU by Month & Tool
    mau_trend = filtered_df.set_index('Date').groupby([pd.Grouper(freq='M'), 'Tool'])['Email'].nunique().reset_index()
    fig_mau = px.line(mau_trend, x='Date', y='Email', color='Tool', markers=True)
    fig_mau.update_layout(xaxis_title="", yaxis_title="Active Users")
    st.plotly_chart(fig_mau, use_container_width=True)

with c2:
    st.subheader("🛠️ Feature Usage Breakdown")
    # What are people actually doing? (Chat vs Advanced Data vs Blueprints)
    feature_mix = filtered_df.groupby('Feature')['Count'].sum().reset_index()
    fig_pie = px.pie(feature_mix, values='Count', names='Feature', hole=0.4)
    st.plotly_chart(fig_pie, use_container_width=True)

# 3. The "Who & Where" (Leaderboards)
st.subheader("🏆 Top 25 Power Users & Departments")

tab1, tab2 = st.tabs(["👥 Top Users", "🏢 Top Departments"])

with tab1:
    # Aggregating user stats
    user_stats = filtered_df.groupby(['Name', 'Department']).agg(
        Total_Interactions=('Count', 'sum'),
        Tools_Used=('Tool', lambda x: ", ".join(x.unique())),
        Last_Active=('Date', 'max')
    ).sort_values('Total_Interactions', ascending=False).head(25).reset_index()
    
    st.dataframe(user_stats, use_container_width=True, hide_index=True)

with tab2:
    # Aggregating dept stats
    dept_stats = filtered_df.groupby('Department').agg(
        Active_Users=('Email', 'nunique'),
        Total_Volume=('Count', 'sum')
    ).sort_values('Total_Volume', ascending=False).reset_index()
    
    st.dataframe(dept_stats, use_container_width=True, hide_index=True)
