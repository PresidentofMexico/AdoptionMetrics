import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import glob
from src.data_processor import DataProcessor

# --- Configuration ---
st.set_page_config(page_title="AI Strategy Dashboard", page_icon="🚀", layout="wide")

# --- Styling ---
st.markdown("""
<style>
    .metric-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid #e0e0e0;
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .big-number { font-size: 36px; font-weight: 800; color: #1E3A8A; }
    .metric-label { font-size: 13px; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# --- Data Loading (Cached) ---
@st.cache_data(show_spinner="Processing Data...")
def load_and_process_data():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    search_paths = [script_dir, repo_root, os.path.join(script_dir, "data"), os.path.join(repo_root, "data")]
    
    emp_path = None
    bf_files = []
    openai_files = []

    for folder in search_paths:
        if not os.path.exists(folder): continue
        if not emp_path:
            found = glob.glob(os.path.join(folder, "Employee Headcount*"))
            if found: emp_path = found[0]
    
        bf_files.extend(glob.glob(os.path.join(folder, "*blueflame*.csv")) + glob.glob(os.path.join(folder, "*BlueFlame*.csv")))
        openai_files.extend(glob.glob(os.path.join(folder, "*Openai*.csv")) + glob.glob(os.path.join(folder, "*ChatGPT*.csv")))
    
    processor = DataProcessor(emp_path)
    df = processor.get_unified_data(bf_paths=list(set(bf_files)), openai_paths=list(set(openai_files)))
    return df, emp_path, processor.debug_log

try:
    df, emp_path, debug_log = load_and_process_data()
    if 'Name' not in df.columns: st.cache_data.clear(); st.rerun()
except Exception as e:
    st.error(f"Processing Error: {e}"); st.stop()

# --- Sidebar & Smart Filters ---
with st.sidebar:
    st.header("🎛️ Strategy Controls")
    
    if st.button("🔥 Nuke Cache & Reload"): st.cache_data.clear(); st.rerun()
    
    # 1. Date Filter
    df['Date'] = pd.to_datetime(df['Date'])
    min_date, max_date = df['Date'].min(), df['Date'].max()
    date_range = st.date_input("Date Range", value=(min_date, max_date))

    # 2. Tool Filter
    st.subheader("🛠️ Platforms")
    tools = st.multiselect("Select Tools", df['Tool'].unique(), default=df['Tool'].unique())

    # 3. Feature Filter (OpenAI Only)
    st.subheader("💬 ChatGPT Message Types")
    st.caption("Filters do not apply to BlueFlame (Total Volume).")
    
    openai_features = sorted(df[df['Tool'] == 'ChatGPT']['Feature'].unique())
    
    # UPDATED DEFAULT: Match the new "ChatGPT Messages" label
    default_features = ['ChatGPT Messages'] if 'ChatGPT Messages' in openai_features else openai_features
    
    selected_features = st.multiselect(
        "Filter Message Categories", 
        openai_features, 
        default=default_features,
        help="Select which ChatGPT interactions to count."
    )

    # 4. Department Filter
    st.subheader("🏢 Departments")
    all_depts = sorted([str(d) for d in df['Department'].unique()])
    depts = st.multiselect("Departments", all_depts, default=all_depts)

# --- Global Filter Application ---
mask = (
    (df['Date'] >= pd.to_datetime(date_range[0])) & 
    (df['Date'] <= pd.to_datetime(date_range[1])) & 
    (df['Tool'].isin(tools)) & 
    (df['Department'].astype(str).isin(depts)) &
    (
        (df['Tool'] == 'BlueFlame') | 
        (df['Feature'].isin(selected_features))
    )
)
filtered_df = df[mask]

if filtered_df.empty:
    st.warning("No data matches your filters.")
    st.stop()

# --- Dashboard Main ---
st.title("🚀 Enterprise AI Strategy Dashboard")
st.markdown("### Executive Overview")

# 1. KPI Cards
col1, col2, col3, col4 = st.columns(4)
active_users = filtered_df['Email'].nunique()
total_vol = filtered_df['Count'].sum()
top_dept = filtered_df.groupby('Department')['Count'].sum().idxmax()
avg_per_user = int(total_vol / active_users) if active_users else 0

def kpi(label, value, col, prefix="", suffix=""):
    col.markdown(f"""<div class="metric-card"><div class="metric-label">{label}</div><div class="big-number">{prefix}{value}{suffix}</div></div>""", unsafe_allow_html=True)

kpi("Active Users", f"{active_users:,}", col1)
kpi("Total Volume", f"{total_vol:,.0f}", col2)
kpi("Top Department", top_dept, col3)
kpi("Avg Msgs / User", f"{avg_per_user}", col4)

st.write("")
st.divider()

# --- TABS FOR ADVANCED VIEWS ---
tab_trends, tab_breakdown, tab_leaderboard = st.tabs(["📈 Trends & Impact", "🧩 Usage Hierarchy", "🏆 Champions"])

with tab_trends:
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.subheader("Adoption Velocity")
        # Group by Date and Tool
        trend_df = filtered_df.groupby([pd.Grouper(key='Date', freq='M'), 'Tool'])['Count'].sum().reset_index()
        fig_area = px.area(trend_df, x='Date', y='Count', color='Tool', 
                           title="Monthly Usage Volume by Platform",
                           labels={'Count': 'Message Volume'},
                           color_discrete_map={'ChatGPT': '#10a37f', 'BlueFlame': '#2563EB'})
        fig_area.update_layout(hovermode="x unified", plot_bgcolor="white")
        st.plotly_chart(fig_area, use_container_width=True)
        
    with c2:
        st.subheader("Engagement Distribution")
        # Scatter plot: Dept vs Volume vs Users
        bubble_df = filtered_df.groupby('Department').agg(
            Volume=('Count', 'sum'),
            Users=('Email', 'nunique')
        ).reset_index()
        
        fig_bubble = px.scatter(bubble_df, x='Users', y='Volume', size='Volume', color='Department',
                                hover_name='Department', title="Department Intensity Matrix",
                                labels={'Users': 'Active Headcount', 'Volume': 'Total Messages'})
        fig_bubble.update_layout(showlegend=False, plot_bgcolor="white")
        st.plotly_chart(fig_bubble, use_container_width=True)

with tab_breakdown:
    st.subheader("Organizational Usage Hierarchy")
    st.caption("Click segments to drill down: Tool → Department → Feature")
    
    fig_sun = px.sunburst(
        filtered_df, 
        path=['Tool', 'Department', 'Feature'], 
        values='Count',
        color='Tool',
        color_discrete_map={'ChatGPT': '#10a37f', 'BlueFlame': '#2563EB', 'Unassigned': '#94a3b8'},
        branchvalues='total'
    )
    fig_sun.update_layout(height=700)
    st.plotly_chart(fig_sun, use_container_width=True)

with tab_leaderboard:
    st.subheader("Identify Your Power Users")
    
    pivot_df = filtered_df.pivot_table(
        index=['Name', 'Department'], 
        columns='Tool', 
        values='Count', 
        aggfunc='sum', 
        fill_value=0
    ).reset_index()
    
    pivot_df['Total_Activity'] = pivot_df.get('ChatGPT', 0) + pivot_df.get('BlueFlame', 0)
    pivot_df = pivot_df.sort_values('Total_Activity', ascending=False).head(50)
    
    st.dataframe(
        pivot_df,
        column_order=("Name", "Department", "Total_Activity", "ChatGPT", "BlueFlame"),
        hide_index=True,
        use_container_width=True,
        column_config={
            "Total_Activity": st.column_config.ProgressColumn("Volume", format="%f", min_value=0, max_value=int(pivot_df['Total_Activity'].max())),
            "ChatGPT": st.column_config.NumberColumn("ChatGPT"),
            "BlueFlame": st.column_config.NumberColumn("BlueFlame"),
        }
    )
