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
    
    # Get only OpenAI features for the list to avoid confusion
    openai_features = sorted(df[df['Tool'] == 'ChatGPT']['Feature'].unique())
    
    # Default to 'Standard Chat' (High Signal)
    default_features = ['Standard Chat'] if 'Standard Chat' in openai_features else openai_features
    
    selected_features = st.multiselect(
        "Filter Message Categories", 
        openai_features, 
        default=default_features,
        help="Select which ChatGPT interactions to count. 'Standard Chat' is the best proxy for true human usage."
    )

    # 4. Department Filter
    st.subheader("🏢 Departments")
    all_depts = sorted([str(d) for d in df['Department'].unique()])
    depts = st.multiselect("Departments", all_depts, default=all_depts)

# --- Global Filter Application ---
# LOGIC: 
# 1. Must match Date, Tool, and Dept.
# 2. THEN: It's kept if it is BlueFlame OR if it matches the selected OpenAI feature.
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
    
    # Sunburst Chart for hierarchical data
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
    
    # Advanced Pivot Table
    pivot_df = filtered_df.pivot_table(
        index=['Name', 'Department'], 
        columns='Tool', 
        values='Count', 
        aggfunc='sum', 
        fill_value=0
    ).reset_index()
    
    # Calculate Total
    pivot_df['Total_Activity'] = pivot_df.get('ChatGPT', 0) + pivot_df.get('BlueFlame', 0)
    pivot_df = pivot_df.sort_values('Total_Activity', ascending=False).head(50)
    
    # Formatting for display
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
    )import streamlit as st
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
    
    # SAFETY CHECK: If Name column is missing, something is wrong with cache or empty data
    if 'Name' not in df.columns:
        st.error("CRITICAL: 'Name' column missing in dataframe. Clearing cache...")
        st.cache_data.clear()
        st.rerun()

except Exception as e:
    st.error(f"Processing Error: {e}")
    st.stop()

# --- Sidebar Debug & Filters ---
with st.sidebar:
    st.header("🎛️ Controls")
    
    if st.button("🔥 Nuke Cache & Reload"):
        st.cache_data.clear()
        st.rerun()

    # DIAGNOSTICS
    with st.expander("🔍 Diagnostics", expanded=True):
        if emp_path:
            st.success(f"✅ Emp: {os.path.basename(emp_path)}")
        else:
            st.error("❌ Emp File Missing")
            
        st.write(f"**BF Files:** {len(bf_files)}")
        st.write(f"**OpenAI Files:** {len(openai_files)}")
        
        st.write("**Logs:**")
        for log in debug_log:
            if "Sample" in log: st.code(log) # Show samples in code block
            elif "❌" in log: st.error(log)
            elif "✅" in log: st.success(log)
            else: st.caption(log)
            
        # Department Check
        if not df.empty:
            unassigned = len(df[df['Department'] == 'Unassigned'])
            total = len(df)
            st.write(f"**Unassigned:** {unassigned}/{total}")

    if df.empty:
        st.warning("No data found.")
        st.stop()
        
    # Filters
    st.divider()
    df['Date'] = pd.to_datetime(df['Date'])
    
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    date_range = st.date_input("Date Range", value=(min_date, max_date))
    
    tools = st.multiselect("Select Tools", df['Tool'].unique(), default=df['Tool'].unique())
    
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
