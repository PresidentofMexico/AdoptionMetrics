import streamlit as st
import plotly.express as px
import pandas as pd
from Home import load_and_process_data
from src.metrics import MetricsEngine

st.set_page_config(page_title="ROI & Strategy", page_icon="💎", layout="wide")

try:
    df, _, _ = load_and_process_data()
    if df.empty: st.warning("No data found."); st.stop()
except Exception as e:
    st.error(f"Error: {e}"); st.stop()

st.title("💎 ROI & Business Impact")

# --- 1. COST INPUTS ---
with st.sidebar.expander("💸 Contract Pricing", expanded=True):
    st.caption("Enter Annual Contract Values")
    bf_cost_annual = st.number_input("BlueFlame Contract ($)", value=250000, step=10000, help="Based on Nov 2025 Contract Update")
    gpt_cost_annual = st.number_input("ChatGPT Contract ($)", value=120000, step=10000, help="Estimated @ $60/user/mo for 160 users")
    
    # Convert to Monthly for the analysis period
    # (Assuming the dashboard filters usually look at a month)
    bf_cost_mo = bf_cost_annual / 12
    gpt_cost_mo = gpt_cost_annual / 12
    
    tool_costs = {
        'BlueFlame': bf_cost_mo,
        'ChatGPT': gpt_cost_mo
    }
    
    st.divider()
    st.metric("Monthly Cost Basis", f"${(bf_cost_mo + gpt_cost_mo):,.0f}")

# --- 2. ASSUMPTIONS ---
with st.expander("🧮 ROI Configuration", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    hourly_rate = c1.number_input("Avg Hourly Cost ($)", value=125)
    discount_rate = c2.slider("Discount Factor (%)", 0, 90, 50, help="Haircut for trial/error") / 100
    
    assumptions = {
        'Standard Chat': 5, 'ChatGPT Messages': 5,
        'Investment Research': 15, 'BlueFlame Messages': 15,
        'Advanced Data Analysis': 30, 'Tool Messages': 30
    }

# --- 3. CALCULATIONS ---
engine = MetricsEngine(df)
# First calculate Gross Value
roi_df = engine.calculate_roi(hourly_rate, assumptions, discount_rate)
# Then calculate Net Impact (Value - Cost)
net_impact = engine.calculate_net_impact(tool_costs)

# --- 4. KPI DISPLAY ---
total_gross = roi_df['Dollar_Value'].sum()
total_cost = sum(tool_costs.values())
total_net = total_gross - total_cost
overall_roi = (total_net / total_cost) * 100 if total_cost > 0 else 0

st.markdown("### 💰 Net Value (Value Created - Contract Cost)")
k1, k2, k3, k4 = st.columns(4)

k1.metric("Gross Value Created", f"${total_gross:,.0f}", delta="Time Savings")
k2.metric("Contract Cost (Mo)", f"${total_cost:,.0f}", delta="Investment", delta_color="inverse")
k3.metric("Net Profit / (Loss)", f"${total_net:,.0f}", delta=f"{overall_roi:.0f}% ROI")
k4.metric("Break-Even Hours", f"{total_cost / hourly_rate:,.0f} hrs", help="Hours we need to save just to pay the bill")

st.divider()

# --- 5. TOOL P&L ---
c1, c2 = st.columns(2)

with c1:
    st.subheader("📊 Tool Profitability")
    
    # Create P&L Dataframe for Chart
    pnl_data = []
    for tool, metrics in net_impact.items():
        pnl_data.append({'Tool': tool, 'Metric': 'Cost', 'Amount': metrics['Cost']})
        pnl_data.append({'Tool': tool, 'Metric': 'Net Value', 'Amount': metrics['Net_Value']})
    
    pnl_df = pd.DataFrame(pnl_data)
    
    fig_pnl = px.bar(
        pnl_df, 
        x='Tool', 
        y='Amount', 
        color='Metric', 
        barmode='group',
        color_discrete_map={'Cost': '#EF4444', 'Net Value': '#10B981'},
        text_auto='$.2s',
        title="Cost vs. Net Value Created"
    )
    st.plotly_chart(fig_pnl, use_container_width=True)

with c2:
    st.subheader("🏆 Top Departments by Value")
    val_by_dept = roi_df.groupby("Department")["Dollar_Value"].sum().sort_values(ascending=True).tail(10).reset_index()
    fig_hbar = px.bar(
        val_by_dept, 
        y="Department", 
        x="Dollar_Value", 
        orientation='h', 
        text_auto='$.2s', 
        color="Dollar_Value",
        color_continuous_scale="Greens"
    )
    fig_hbar.update_layout(xaxis_title="Gross Dollar Value", showlegend=False)
    st.plotly_chart(fig_hbar, use_container_width=True)
