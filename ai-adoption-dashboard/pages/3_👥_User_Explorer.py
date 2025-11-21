import streamlit as st
import pandas as pd
from src.data_processor import load_data
from src.metrics import MetricsEngine

st.set_page_config(page_title="User Explorer", page_icon="👥", layout="wide")

try:
    df, _, _ = load_data()
except:
    st.error("Data load failed."); st.stop()

engine = MetricsEngine(df)
leaderboard = engine.get_user_leaderboard()

st.title("👥 User Explorer & Management")

tab_users, tab_mapper = st.tabs(["🏆 User Leaderboard", "🛠️ Department Fixer"])

with tab_users:
    # Interactive Filters
    c1, c2 = st.columns([3, 1])
    search = c1.text_input("🔍 Search User", placeholder="Type a name...")
    status_filter = c2.multiselect("Tier", options=["🔥 Champion", "⚡ Power User", "🌱 Explorer"])
    
    # Filter Logic
    view_df = leaderboard.copy()
    if search:
        view_df = view_df[view_df['Name'].str.contains(search, case=False, na=False)]
    if status_filter:
        view_df = view_df[view_df['Status'].isin(status_filter)]
        
    st.dataframe(
        view_df,
        column_order=("Status", "Name", "Department", "Total_Interactions", "Tools_Used", "Last_Active"),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Total_Interactions": st.column_config.ProgressColumn("Volume", min_value=0, max_value=int(leaderboard['Total_Interactions'].max())),
            "Tools_Used": st.column_config.ListColumn("Platforms"),
        }
    )

with tab_mapper:
    st.markdown("### 🛠️ Fix 'Unassigned' Departments")
    st.caption("The table below isolates users with missing departments. You can export this list to update your Employee Headcount file.")
    
    # Filter for Unassigned
    unassigned_df = leaderboard[leaderboard['Department'] == 'Unassigned'].copy()
    
    if unassigned_df.empty:
        st.success("✅ No unassigned users found! Your data is clean.")
    else:
        st.warning(f"Found {len(unassigned_df)} users without a department.")
        
        # Editable Dataframe
        edited_df = st.data_editor(
            unassigned_df[['Name', 'Email', 'Department']],
            disabled=["Name", "Email"], # Lock these columns
            num_rows="fixed",
            use_container_width=True
        )
        
        st.download_button(
            "📥 Download for IT",
            data=edited_df.to_csv(index=False),
            file_name="users_needing_departments.csv",
            mime="text/csv",
            help="Download this list, fill in the departments, and add them to your master Employee Headcount file."
        )
