import streamlit as st
import pandas as pd
import plotly.express as px
import os
import glob
from src.data_processor import DataProcessor

# --- Configuration ---
st.set_page_config(page_title="AI Executive Dashboard", page_icon="🚀", layout="wide")

# --- Styling ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #e0e0e0;
    }
    .big-number { font-size: 32px; font-weight: 800; color: #1E3A8A; }
    .metric-label { font-size: 14px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
</style>
""", unsafe_allow_html=True)

# --- Data Loading Logic ---
@st.cache_data(show_spinner="Processing Data...")
def load_and_process_data():
    # Determine Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    
    search_paths = [script_dir, repo_root, os.path.join(script_dir, "data"), os.path.join(repo_root, "data")]
    
    emp_path = None
    bf_files = []
    openai_files = []

    # 1. Find Employee File
    for folder in search_paths:
        if not os.path.exists(folder): continue
        found = glob.glob(os.path.join(folder, "Employee Headcount*"))
        if found: 
            emp_path = found[0]
            break
    
    # 2. Find Usage Files
    for folder in search_paths:
        if not os.path.exists(folder): continue
        bf_files.extend(glob.glob(os.path.join(folder, "*blueflame*.csv")) + glob.glob(os.path.join(folder, "*BlueFlame*.csv")))
        openai_files.extend(glob.glob(os.path.join(folder, "*Openai*.csv")) + glob.glob(os.path.join(folder, "*ChatGPT*.csv")))
    
    bf_files = list(set(bf_files))
    openai_files = list(set(openai_files))

    # 3. Run Processor
    processor = DataProcessor(emp_path)
    df = processor.get_unified_data(bf_paths=bf_files, openai_paths=openai_files)
    
    return df, emp_path, bf_files, openai_files, processor.debug_log

# --- App Logic ---
try:
    df, emp_path, bf_files, openai_files, debug_log = load_and_process_data()
except Exception as e:
    st.error(f"Critical Error during processing: {e}")
    st.stop()

# --- Sidebar Debug & Filters ---
with st.sidebar:
    st.header("🎛️ Controls")
    
    # DIAGNOSTICS
    with st.expander("🔍 Diagnostics (Check this!)", expanded=True):
        # 1. File Detection
        if emp_path:
            st.success(f"✅ Employees: {os.path.basename(emp_path)}")
        else:
            st.error("❌ Employee File Missing")
        
        # 2. Processor Logs
        st.write("**Processor Logs:**")
        for log in debug_log:
            if "❌" in log: st.error(log)
            elif "⚠️" in log: st.warning(log)
            else: st.caption(log)
            
        # 3. Match Rate Check
        if not df.empty:
            assigned = len(df[df['Department'] != 'Unassigned'])
            total = len(df)
            st.write(f"**Match Rate:** {assigned}/{total} records")
            if assigned == 0:
                st.error("0% Matching! Check email column names.")

    if df.empty:
        st.warning("No unified data found.")
        st.stop()
        
    # Filters
    st.divider()
    df['Date'] = pd.to_datetime(df['Date'])
    
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    date_range = st.date_input("Date Range", value=(min_date, max_date))
    
    tools = st.multiselect("Select Tools", df['Tool'].unique(), default=df['Tool'].unique())
    
    # Dept Filter
    available_depts = sorted([str(d) for d in df['Department'].unique()])
    depts = st.multiselect("Select Departments", available_depts, default=available_depts)

# Apply Filters
mask = (
    (df['Date'] >= pd.to_datetime(date_range[0])) & 
    (df['Date'] <= pd.to_datetime(date_range[1])) & 
    (df['Tool'].isin(tools)) & 
    (df['Department'].astype(str).isin(depts))
)
filtered_df = df[mask]

# --- Main Dashboard ---
st.title("🚀 Enterprise AI Adoption Dashboard")

# 1. Top Level Metrics
col1, col2, col3, col4 = st.columns(4)
total_users = filtered_df['Email'].nunique()
total_activities = filtered_df['Count'].sum()
active_depts = filtered_df['Department'].nunique()
top_tool = filtered_df.groupby('Tool')['Count'].sum().idxmax() if not filtered_df.empty else "N/A"

def custom_metric(label, value, col):
    col.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="big-number">{value}</div></div>""", unsafe_allow_html=True)

custom_metric("Active Users", f"{total_users:,}", col1)
custom_metric("Total Interactions", f"{total_activities:,.0f}", col2)
custom_metric("Active Departments", active_depts, col3)
custom_metric("Top Platform", top_tool, col4)

st.write("")

# 2. Adoption Rate & Trends
c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("📈 Adoption Trend")
    if not filtered_df.empty:
        mau_trend = filtered_df.set_index('Date').groupby([pd.Grouper(freq='M'), 'Tool'])['Email'].nunique().reset_index()
        fig_mau = px.line(mau_trend, x='Date', y='Email', color='Tool', markers=True, labels={'Email': 'Active Users'})
        st.plotly_chart(fig_mau, use_container_width=True)

with c2:
    st.subheader("🛠️ Usage Breakdown")
    if not filtered_df.empty:
        feature_mix = filtered_df.groupby('Feature')['Count'].sum().reset_index()
        fig_pie = px.pie(feature_mix, values='Count', names='Feature', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)

# 3. Leaderboards
st.divider()
tab1, tab2 = st.tabs(["👥 Top Users", "🏢 Top Departments"])

with tab1:
    if not filtered_df.empty:
        user_stats = filtered_df.groupby(['Name', 'Department']).agg(
            Total_Interactions=('Count', 'sum'),
            Tools_Used=('Tool', lambda x: ", ".join(x.unique())),
            Last_Active=('Date', 'max')
        ).sort_values('Total_Interactions', ascending=False).head(25).reset_index()
        user_stats.index += 1
        st.dataframe(user_stats, use_container_width=True)

with tab2:
    if not filtered_df.empty:
        dept_stats = filtered_df.groupby('Department').agg(
            Active_Users=('Email', 'nunique'),
            Total_Volume=('Count', 'sum')
        ).sort_values('Total_Volume', ascending=False).reset_index()
        dept_stats.index += 1
        st.dataframe(dept_stats, use_container_width=True)
